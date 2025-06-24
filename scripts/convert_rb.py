#!/usr/bin/env python3
"""
Convert rule-based tagger JSON -> CoNLL-U.
Handles both
  { 'this': {...}, 'is': {...}, ... }               # single sentence
and
  [ { 'this': {...}, 'is': {...}, ... },            # list of sentences
    { ... }, ... ]
"""

import sys, json, collections

# ----------------- mapping -----------------
RB2UD = {
    "noun":        "NOUN",
    "verb":        "VERB",
    "adjective":   "ADJ",
    "adverb":      "ADV",
    "pronoun":     "PRON",
    "determiner":  "DET",
    "preposition": "ADP",
    "conjunction": "CCONJ",
    "interjection":"INTJ",
    "number":      "NUM",
    "punctuation": "PUNCT",
    "uncertain":   "X"
}

def rb2ud(tag):
    return RB2UD.get(tag, "X")

# ------------- CoNLL-U builder -------------
def sentence_dict_to_conllu(sent_dict, sent_id):
    """
    sent_dict : {'word1': {...}, 'word2': {...}, ...}
    returns   : list[str]  (one CoNLL-U sentence incl. blank line)
    """
    # insertion order of dicts is preserved in Py 3.7+, so this keeps token order
    words = list(sent_dict.keys())
    lines = [f"# sent_id = {sent_id}",
             f"# text = {' '.join(words)}"]

    for i, w in enumerate(words, 1):
        ud = rb2ud(sent_dict[w].get("tag", "uncertain"))
        lines.append(f"{i}\t{w}\t_\t{ud}\t_\t_\t_\t_\t_\t_")

    lines.append("")            # blank line after each sentence
    return lines

def convert(obj):
    """
    obj is either a dict (one sentence) or list[dict] (many sentences)
    returns full CoNLL-U string
    """
    if isinstance(obj, collections.abc.Mapping):
        obj = [obj]             # wrap single sentence as list

    lines = ["# newdoc id = converted_rule_based", "# newpar"]
    for sid, sent in enumerate(obj, 1):
        lines.extend(sentence_dict_to_conllu(sent, sid))
    return "\n".join(lines)

# ----------------- CLI -----------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(f"Usage: {sys.argv[0]} input.json output.conllu")

    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    conllu = convert(data)

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(conllu)

    print("✓ Conversion finished:", sys.argv[2])
