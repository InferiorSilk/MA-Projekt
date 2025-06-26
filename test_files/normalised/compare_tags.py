
"""
Token-stream comparison of POS tags in CoNLL-U files.

Alignment heuristic:
    Two tokens are considered the “same” word if the first 3 characters of
    their FORM column (lower-cased) are identical.  If either token is shorter
    than three characters, its entire string must match. This is the case because 
    the stemmer (stemmer.py) does not stem words shorter than three characters.
    Adding more characters to check might increase the chance of false positives.

After the alignment only the chosen tag column (UPOS or XPOS) is evaluated.

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

Quite obviously fully made by AI. I added some clarification into the comments 
and docstrings where needed
"""

import argparse
import glob
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

FIELDS = (
    "ID", "FORM", "LEMMA", "UPOS", "XPOS",
    "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"
)

def short_key(form: str, n: int = 3) -> str:
    """
    Return the first `n` characters of `form` (lower-cased) unless `form`
    is shorter than `n`, in which case return the full string.
    """
    return form.lower()[:n] if len(form) >= n else form.lower()

def parse_conllu(path: Path) -> List[Dict[str, str]]:
    """
    Parse a CoNLL-U file into a flat list of token dicts.
    Comment lines and multi-word tokens (IDs containing '-' or '.') are skipped.
    """
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
            if "-" in tok_id or "." in tok_id:          # skip MWTs & empty nodes
                continue

            token = {field: value for field, value in zip(FIELDS, cols)}
            tokens.append(token)

    return tokens

def compare_streams(
    gold: List[Dict[str, str]],
    sys: List[Dict[str, str]],
    tag_field: str,
    verbose: bool = False,
) -> Tuple[int, int, List[str]]:
    """
    Align `gold` and `sys` token lists via SequenceMatcher on the 3-char key,
    then compute tag accuracy.

    Returns
    -------
    total_gold : int    number of gold tokens evaluated
    correct    : int    how many of them have the same tag in the system
    diffs      : List[str]  textual description of mismatches (for verbose mode)
    """
    g_keys = [short_key(t["FORM"]) for t in gold]
    s_keys = [short_key(t["FORM"]) for t in sys]

    sm = SequenceMatcher(a=g_keys, b=s_keys, autojunk=False)

    total_gold = 0
    correct = 0
    diff_lines: List[str] = []

    for tag, g0, g1, s0, s1 in sm.get_opcodes():
        if tag == "equal":
            # tokens aligned one-to-one
            for gi, si in zip(range(g0, g1), range(s0, s1)):
                total_gold += 1
                g_tag = gold[gi][tag_field]
                s_tag = sys[si][tag_field]
                if g_tag == s_tag:
                    correct += 1
                elif verbose:
                    diff_lines.append(
                        f"{gold[gi]['FORM']}  {tag_field}: gold='{g_tag}' | sys='{s_tag}'"
                    )
        elif tag in {"replace", "delete"}:
            # tokens that exist in gold but not (properly) in system → all wrong
            for gi in range(g0, g1):
                total_gold += 1
                if verbose:
                    diff_lines.append(
                        f"{gold[gi]['FORM']}  {tag_field}: gold='{gold[gi][tag_field]}' | sys=∅"
                    )
        elif tag == "insert":
            # extra tokens only in system → ignored (no gold counterpart)
            continue

    return total_gold, correct, diff_lines

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Compare POS tags in CoNLL-U files with a 3-char token alignment"
    )
    ap.add_argument("gold", type=Path, help="Gold/standard .conllu file")
    ap.add_argument("systems", nargs="+",
                    help="One or more system .conllu files (wildcards OK)")
    ap.add_argument("-t", "--tag-field", choices=("upos", "xpos"),
                    default="upos", help="Column to evaluate (default: upos)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="Show every mismatching token")
    args = ap.parse_args(argv)

    tag_field = args.tag_field.upper()   # work with upper-case key names

    if not args.gold.exists():
        sys.exit(f"Gold file '{args.gold}' not found")

    gold_stream = parse_conllu(args.gold)

    # Expand wild-cards for system files
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
        total, correct, diffs = compare_streams(
            gold_stream, sys_stream, tag_field, verbose=args.verbose
        )

        print(f"=== {sys_path} ===")
        print(f"Tokens correct : {correct}/{total} ({correct/total:.2%})\n")

        if args.verbose and diffs:
            print("Detailed differences")
            print("--------------------")
            for line in diffs:
                print(line)
            print()

if __name__ == "__main__":
    main()