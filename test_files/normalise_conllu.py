#!/usr/bin/env python3
"""
normalise_conllu.py  –  make any *.conllu variant strict 10-column CoNLL-U.

Changes compared with the previous version:
  * multi-line '# Sentence:' blocks collapsed into '# text = …'
  * sentence boundaries for that variant found via '# Sentence:' not blank lines
  * robust against space-separated token rows

Fully made by AI
"""
import argparse, pathlib, re, sys
from typing import List, Iterable

def pad(cols: List[str], length: int = 10) -> List[str]:
    "Pad / truncate to `length` elements with '_'"
    return (cols + ["_"] * length)[:length]

def iter_sentences(path: pathlib.Path) -> Iterable[List[str]]:
    """
    Yield lists of raw lines representing one sentence.

    • If the file contains '# Sentence:' we use that tag as explicit
      delimiter (blank lines inside the block are kept).
    • Otherwise we fall back to the normal blank-line rule.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=False)

    if any(l.startswith("# Sentence:") for l in lines):
        current: List[str] = []
        for ln in lines:
            if ln.startswith("# Sentence:"):
                if current:
                    yield current
                    current = []
            current.append(ln)
        if current:
            yield current
    else:                                                # canonical CoNLL-U
        current: List[str] = []
        for ln in lines + [""]:                          # sentinel blank
            if ln.strip():
                current.append(ln)
            else:
                if current:
                    yield current
                    current = []

def fix_sentence(lines: List[str]) -> List[str]:
    """
    Return ONE sentence as canonical 10-column CoNLL-U.
    Removes spaCy ‘SPACE/_’ pseudo-tokens and other non-numeric IDs.
    """
    meta, tokens = [], []
    header_map = {}
    next_auto_id = 1                   # when header-table rows have no ID

    # --- variant 1: already CoNLL-U (spaCy, Stanza, etc.) ------------------
    already_ok = any(l.startswith("#") for l in lines if l.strip()) \
                 and not any(l.upper().startswith("ID") for l in lines)

    if already_ok:
        for l in lines:
            if not l.strip():
                continue
            if l.startswith("#"):
                meta.append(l.rstrip("\n"))
                continue

            # choose delimiter dynamically
            line = l.rstrip("\n")
            parts = line.split("\t") if "\t" in line else line.split()

            # skip phantom/padding tokens (ID non-numeric or FORM == "_")
            try:
                int(parts[0])
            except (ValueError, IndexError):
                continue
            if len(parts) > 1 and parts[1] == "_":
                continue

            tokens.append("\t".join(pad(parts)))
        return meta + tokens

    # ---------- variant 2: header row + table -----------------------------
    def safe(parts: List[str], col_name: str, fallback: str = "_") -> str:
        idx = header_map.get(col_name)
        return parts[idx] if (idx is not None and idx < len(parts)) else fallback

    def looks_like_id(value: str) -> bool:
        """Return True for 1, 14, 3-4, 5.1 ... but False for 'SPACE' etc."""
        return bool(re.match(r"^\d+(?:-\d+|\.\d+)?$", value))

    for l in lines:
        if l.lower().startswith("# sentence"):
            text = re.sub(r"^# Sentence:\s*", "", l, flags=re.I).strip()
            meta.append(f"# text = {text}")
        elif l.startswith("#"):
            meta.append(l.rstrip("\n"))
        elif not l.strip():
            continue
        elif l.upper().startswith("ID"):
            # build once:  {'ID':0,'FORM':1,'LEMMA':2 ...}
            header_map = {h.upper(): i for i, h in enumerate(l.split())}
        else:
            parts = l.split()
            # skip rows that do not really carry an ID value
            id_val = safe(parts, "ID", "")
            if not looks_like_id(id_val):
                continue                       # ← toss “SPACE _SP …” rows

            cols = ["_"] * 10
            cols[0] = id_val
            cols[1] = safe(parts, "FORM")
            cols[2] = safe(parts, "LEMMA")
            cols[3] = safe(parts, "UPOS")
            cols[4] = safe(parts, "XPOS")
            cols[6] = safe(parts, "HEAD", "0")
            cols[7] = safe(parts, "DEPREL")
            tokens.append("\t".join(cols))

    # make sure there is some kind of sent_id
    if not any(m.startswith("# sent_id") for m in meta):
        fix_sentence.sid += 1
        meta.insert(0, f"# sent_id = {fix_sentence.sid}")

    return meta + tokens

fix_sentence.sid = 0

def normalise_file(fp: pathlib.Path) -> List[str]:
    out: List[str] = []
    for sent in iter_sentences(fp):
        out.extend(fix_sentence(sent))
        out.append("")                                    # blank sep
    return out

def main() -> None:
    ap = argparse.ArgumentParser(description="Normalise weird CoNLL-U variants.")
    ap.add_argument("files", nargs="*", help="*.conllu files to process")
    ap.add_argument("--auto", metavar="DIR",
                    help="recursively process every *.conllu beneath DIR")
    ap.add_argument("-o", "--outdir",
                    help="write results here instead of <name>.normalized.conllu")
    args = ap.parse_args()

    inputs = [pathlib.Path(f) for f in args.files]

    if args.auto:
        inputs.extend(pathlib.Path(args.auto).rglob("*.conllu"))

    if not inputs:
        ap.error("No input files and no --auto given")

    for fp in inputs:
        out_lines = normalise_file(fp)

        if args.outdir:
            outdir = pathlib.Path(args.outdir)
            outdir.mkdir(parents=True, exist_ok=True)
            out_path = outdir / fp.name
        else:
            out_path = fp.with_suffix(".normalized.conllu")

        out_path.write_text("\n".join(out_lines), encoding="utf-8")
        print(f"✓ normalised → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
