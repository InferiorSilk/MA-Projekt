#!/usr/bin/env python3
"""
normalise_conllu_v2.py
----------------------
Turn any of our three input variants into strict 10-column CoNLL-U.

Changes vs. the earlier version
-------------------------------
*  Sentences are split on '# Sentence:' (table variant) **or** blank line
   (already-good variant) – so internal blank lines no longer break the table.
*  Token lines are recognised only when they contain at least one TAB
   (plain-text lines are ignored).
*  Lines that contain only an ID (e.g. '12') are silently skipped.
*  Dynamic delimiter detection for already-good CoNLL-U (tab **or** spaces).
"""
import argparse, pathlib, re, sys
from typing import List, Dict

# --------------------------------------------------------------------------- helpers
def pad(cols: List[str], length: int = 10) -> List[str]:
    return (cols + ["_"] * length)[:length]

def safe(parts: List[str], idx: int | None, fallback: str = "_") -> str:
    return parts[idx] if idx is not None and idx < len(parts) and parts[idx] else fallback

# --------------------------------------------------------------------------- sentence normaliser
def sentences_from(path: pathlib.Path):
    """
    Yield raw sentence blocks (list[str]) from file.  A blank line only ends
    a sentence if the following *non-empty* line starts with a comment (‘#’).
    This keeps “accidental” blank lines inside the same sentence.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=False)
    lines.append("")                      # sentinel

    cur = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip():                  # real content
            cur.append(line)
        else:                             # blank line → look ahead
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1                    # skip multiple blanks
            if j == len(lines) or lines[j].startswith("#"):
                # real sentence boundary
                if cur:
                    yield cur
                    cur = []
            else:
                # keep single blank inside same sentence (ignore)
                pass
            i = j - 1                     # because loop will ++
        i += 1
    if cur:
        yield cur
# ---------------------------------------------------------------------------
def fix_sentence(lines: List[str]) -> List[str]:
    """
    Return ONE sentence in canonical CoNLL-U (10 tab-separated columns).
    Two variants are handled:
      1. already-good CoNLL-U (tab or space separated);
      2. the “ID FORM …” header dump (header may appear only once).
    """
    meta, tokens = [], []
    header_map = {}
    next_auto_id = 1

    # ––– variant 1: looks like proper CoNLL-U (has comments, no ‘ID …’ row)
    already = any(l.startswith("#") for l in lines if l.strip()) \
              and not any(l.upper().startswith("ID") for l in lines)

    if already:
        for l in lines:
            if l.startswith("#"):
                meta.append(l.rstrip("\n"))
            elif l.strip():               # token line
                parts = (l.rstrip("\n").split("\t")
                         if "\t" in l else l.split())
                tokens.append("\t".join(pad(parts)))
        return meta + tokens

    # ––– variant 2: header row + possibly later plain-token lines –––––––––
    def safe(parts: List[str], col_name: str, fallback: str = "_") -> str:
        idx = header_map.get(col_name)
        return parts[idx] if (idx is not None and idx < len(parts)) else fallback

    for l in lines:
        # ----- metadata ---------------------------------------------------
        if l.lower().startswith("# sentence"):
            text = re.sub(r"^# Sentence:\s*", "", l, flags=re.I).strip()
            meta.append(f"# text = {text}")
            continue
        if l.startswith("#"):
            meta.append(l.rstrip("\n")); continue
        if not l.strip():
            continue                      # (internal blanks have been kept)

        # ----- header row --------------------------------------------------
        if l.upper().startswith("ID"):
            header_map = {h.upper(): i for i, h in enumerate(l.split())}
            continue

        # ----- token line --------------------------------------------------
        parts = l.split()                 # works for both space & tab
        cols = ["_"] * 10

        if header_map:                    # we *have* a header row
            explicit_id = safe(parts, "ID", "")
            if explicit_id == "":
                explicit_id = str(next_auto_id)
            cols[0] = explicit_id
            cols[1] = safe(parts, "FORM")
            cols[2] = safe(parts, "LEMMA")
            cols[3] = safe(parts, "UPOS")
            cols[4] = safe(parts, "XPOS")
            cols[6] = safe(parts, "HEAD", "0")
            cols[7] = safe(parts, "DEPREL")
        else:                             # no header → assume plain CoNLL-U
            # ID FORM LEMMA UPOS XPOS HEAD DEPREL  (ca. 7 cols) + optional
            for i, p in enumerate(parts[:10]):
                cols[i] = p
            # guarantee numeric ID
            if not cols[0].isdigit():
                cols[0] = str(next_auto_id)
            if cols[6] == "_":            # HEAD missing
                cols[6] = "0"

        next_auto_id += 1
        tokens.append("\t".join(cols))

    if not any(m.startswith("# sent_id") for m in meta):
        fix_sentence.sid += 1
        meta.insert(0, f"# sent_id = {fix_sentence.sid}")

    return meta + tokens

fix_sentence.sid = 0

# --------------------------------------------------------------------------- full file normaliser
def normalise_file(fp: pathlib.Path) -> List[str]:
    out: List[str] = []
    for sent in sentences_from(fp):
        out.extend(fix_sentence(sent))
        out.append("")          # blank separator
    return out

# --------------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help=".conllu files to process")
    ap.add_argument("--auto", metavar="DIR", help="recursively normalise every *.conllu under DIR")
    ap.add_argument("-o", "--outdir", help="where to write the output files")
    args = ap.parse_args()

    todo = [pathlib.Path(f) for f in args.files]
    if args.auto:
        todo.extend(pathlib.Path(args.auto).rglob("*.conllu"))
    if not todo:
        ap.error("No input .conllu files and --auto not supplied")

    for fp in todo:
        out_lines = normalise_file(fp)
        if args.outdir:
            outdir = pathlib.Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
            outpath = outdir / fp.name
        else:
            outpath = fp.with_suffix(".normalized.conllu")

        outpath.write_text("\n".join(out_lines), encoding="utf-8")
        print(f"✓ {fp.name}  →  {outpath}", file=sys.stderr)

if __name__ == "__main__":
    main()
