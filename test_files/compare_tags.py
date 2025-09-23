"""
Token-stream comparison of POS tags in CoNLL-U files.

Alignment heuristic:
    Two tokens are considered the “same” word if:
      - For punctuation: exact match after Unicode normalization
      - For words: first N characters (default 5) of the normalized, lowercased FORM
    If the token is shorter than N characters, the entire string is used.

After alignment only the chosen tag column (UPOS or XPOS) is evaluated.

Differences caused by extra or missing punctuation, stemming, or slightly
different sentence boundaries therefore affect the score much less than in a
strict index-by-index comparison.

USAGE
-----
    python compare_tags_stream.py gold.conllu system1.conllu system2.conllu ...
OPTIONS
-------
    -t, --tag-field {upos,xpos}   column to evaluate (default: upos)
    -v, --verbose                 list every mismatch
Fully implemented by AI
"""

import argparse
import glob
import sys
import unicodedata
import re
from pathlib import Path
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from collections import defaultdict, Counter

FIELDS = (
    "ID", "FORM", "LEMMA", "UPOS", "XPOS",
    "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"
)

PUNCT_RE = re.compile(r"^\W+$", flags=re.UNICODE)

def normalize_form(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    trans = {
        "“": '"', "”": '"', "„": '"', "’": "'", "‘": "'",
        "–": "-", "—": "-", "…": "...",
    }
    return "".join(trans.get(ch, ch) for ch in s)

def key_for_alignment(form: str, n: int = 5) -> str:
    f = normalize_form(form)
    if PUNCT_RE.match(f):
        return f
    return f.lower() if len(f) < n else f.lower()[:n]

def parse_conllu(path: Path) -> List[Dict[str, str]]:
    tokens: List[Dict[str, str]] = []
    with path.open(encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) != 10:
                raise ValueError(f"{path}:{ln}: expected 10 columns, got {len(cols)}")
            tok_id = cols[0]
            if "-" in tok_id or "." in tok_id:
                continue
            cols[1] = normalize_form(cols[1])
            token = {field: value for field, value in zip(FIELDS, cols)}
            tokens.append(token)
    return tokens

def compare_streams(
    gold: List[Dict[str, str]],
    sys: List[Dict[str, str]],
    tag_field: str,
    verbose: bool = False,
) -> Tuple[int, int, List[str], Dict[str, Counter]]:
    g_keys = [key_for_alignment(t["FORM"]) for t in gold]
    s_keys = [key_for_alignment(t["FORM"]) for t in sys]

    print(f"DEBUG: First 10 gold keys: {g_keys[:10]}")
    print(f"DEBUG: First 10 sys keys : {s_keys[:10]}")

    sm = SequenceMatcher(a=g_keys, b=s_keys)  # autojunk=True

    total_gold = 0
    correct = 0
    diff_lines: List[str] = []
    confusion: Dict[str, Counter] = defaultdict(Counter)

    for tag, g0, g1, s0, s1 in sm.get_opcodes():
        if tag == "equal":
            for gi, si in zip(range(g0, g1), range(s0, s1)):
                total_gold += 1
                g_tag = gold[gi][tag_field]
                s_tag = sys[si][tag_field]
                confusion[g_tag][s_tag] += 1
                if g_tag == s_tag:
                    correct += 1
                elif verbose:
                    diff_lines.append(
                        f"{gold[gi]['FORM']}  {tag_field}: gold='{g_tag}' | sys='{s_tag}'"
                    )
        elif tag == "replace":
            g_sub = gold[g0:g1]
            s_sub = sys[s0:s1]
            gk = [key_for_alignment(t["FORM"]) for t in g_sub]
            sk = [key_for_alignment(t["FORM"]) for t in s_sub]
            sub_sm = SequenceMatcher(a=gk, b=sk)
            for sub_tag, gg0, gg1, ss0, ss1 in sub_sm.get_opcodes():
                if sub_tag == "equal":
                    for gi, si in zip(range(gg0, gg1), range(ss0, ss1)):
                        total_gold += 1
                        g_tag = g_sub[gi][tag_field]
                        s_tag = s_sub[si][tag_field]
                        confusion[g_tag][s_tag] += 1
                        if g_tag == s_tag:
                            correct += 1
                        elif verbose:
                            diff_lines.append(
                                f"{g_sub[gi]['FORM']}  {tag_field}: gold='{g_tag}' | sys='{s_tag}'"
                            )
                else:
                    for gi in range(gg0, gg1):
                        total_gold += 1
                        g_tag = g_sub[gi][tag_field]
                        confusion[g_tag]["∅"] += 1
                        if verbose:
                            diff_lines.append(
                                f"{g_sub[gi]['FORM']}  {tag_field}: gold='{g_tag}' | sys=∅"
                            )
        elif tag == "delete":
            for gi in range(g0, g1):
                total_gold += 1
                g_tag = gold[gi][tag_field]
                confusion[g_tag]["∅"] += 1
                if verbose:
                    diff_lines.append(
                        f"{gold[gi]['FORM']}  {tag_field}: gold='{g_tag}' | sys=∅"
                    )
        elif tag == "insert":
            continue

    return total_gold, correct, diff_lines, confusion

def print_confusion(confusion: Dict[str, Counter]):
    if not confusion:
        print("No tokens compared — confusion matrix is empty.")
        return
    tags = sorted(confusion.keys())
    sys_tags = sorted({t for c in confusion.values() for t in c})
    header = ["GOLD\\SYS"] + sys_tags
    col_widths = [max(len(h), 5) for h in header]
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*header))
    for g_tag in tags:
        row = [g_tag] + [str(confusion[g_tag].get(s_tag, 0)) for s_tag in sys_tags]
        print(fmt.format(*row))

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("gold", type=Path)
    ap.add_argument("systems", nargs="+")
    ap.add_argument("-t", "--tag-field", choices=("upos", "xpos"),
                    default="upos")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    tag_field = args.tag_field.upper()

    if not args.gold.exists():
        sys.exit(f"Gold file '{args.gold}' not found")

    gold_stream = parse_conllu(args.gold)
    print(f"DEBUG: Parsed {len(gold_stream)} tokens from gold file.")

    sys_paths: List[Path] = []
    for pattern in args.systems:
        matches = [Path(p) for p in glob.glob(pattern)]
        if not matches:
            print(f"Warning: pattern '{pattern}' matched no files", file=sys.stderr)
        sys_paths.extend(matches)

    if not sys_paths:
        sys.exit("No system files to compare.")

    for sys_path in sys_paths:
        if not sys_path.exists():
            print(f"Skipping missing file '{sys_path}'", file=sys.stderr)
            continue

        sys_stream = parse_conllu(sys_path)
        sys_count = len(sys_stream)
        print(f"DEBUG: Parsed {sys_count} tokens from system file '{sys_path}'.")

        total_gold, correct, diffs, confusion = compare_streams(
            gold_stream, sys_stream, tag_field, verbose=args.verbose
        )

        # Use the smaller of the two token counts for percentage calculation
        denom = min(len(gold_stream), sys_count)

        print(f"=== {sys_path} ===")
        if denom > 0:
            print(f"Tokens correct : {correct}/{denom} ({correct/denom:.2%})\n")
        else:
            print("No overlapping tokens — cannot compute accuracy.\n")

        print("Per-tag confusion matrix:")
        print_confusion(confusion)
        print()

        if args.verbose:
            print("Detailed differences")
            print("--------------------")
            if diffs:
                for line in diffs:
                    print(line)
            else:
                print("(No mismatches recorded)")
            print()

if __name__ == "__main__":
    main()