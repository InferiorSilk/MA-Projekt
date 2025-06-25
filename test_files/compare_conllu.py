#!/usr/bin/env python3
"""
Compare two *normalised* CoNLL-U files and report differences.

Usage:
   python compare_conllu.py left.conllu right.conllu
"""
import sys, argparse
from conllu import parse

def load(path):
    with open(path, encoding="utf-8") as f:
        return parse(f.read())

def align(left, right):
    """
    Yield tuples: (left_sentence, right_sentence, key)
    key = sent_id if available else running index.
    """
    lmap = {s.metadata.get("sent_id", str(i)): s for i, s in enumerate(left)}
    rmap = {s.metadata.get("sent_id", str(i)): s for i, s in enumerate(right)}
    keys = sorted(set(lmap) | set(rmap), key=lambda k: int(re.sub(r'\D','',k) or 0))
    for k in keys:
        yield lmap.get(k), rmap.get(k), k

def diff_tokens(lsent, rsent):
    """Return lists of (i, ltok, rtok) where at least one field differs."""
    diffs = []
    if not lsent or not rsent:
        return diffs
    ldict = {t["id"]: t for t in lsent if isinstance(t["id"], int)}
    rdict = {t["id"]: t for t in rsent if isinstance(t["id"], int)}
    ids = sorted(set(ldict) | set(rdict))
    for i in ids:
        lt, rt = ldict.get(i), rdict.get(i)
        if lt != rt:
            diffs.append((i, lt, rt))
    return diffs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("left"), ap.add_argument("right")
    args = ap.parse_args()
    left, right = load(args.left), load(args.right)

    sent_total, sent_added, sent_removed, tok_diff = 0, 0, 0, 0
    for lsent, rsent, key in align(left, right):
        sent_total += 1
        if lsent is None:
            print(f"+ Sentence {key} only in RIGHT")
            sent_added += 1
            continue
        if rsent is None:
            print(f"- Sentence {key} only in LEFT")
            sent_removed += 1
            continue

        diffs = diff_tokens(lsent, rsent)
        if diffs:
            print(f"~ Sentence {key}: {len(diffs)} differing token(s)")
            for idx, lt, rt in diffs:
                print(f"  token {idx}:")
                print(f"    L {lt['form'] if lt else '-':<15} {lt}")
                print(f"    R {rt['form'] if rt else '-':<15} {rt}")
            tok_diff += len(diffs)

    print("\n--- summary ---")
    print(f"sentences compared : {sent_total}")
    print(f"  added in right   : {sent_added}")
    print(f"  removed in left  : {sent_removed}")
    print(f"token differences  : {tok_diff}")

if __name__ == "__main__":
    main()
