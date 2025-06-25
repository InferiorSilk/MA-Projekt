"""
compare_with_spacy.py

Read raw text files (e.g. en_gum-ud-test.txt) and run spaCy's transformer
pipeline on them.  Outputs tokens, lemmas, POS tags, dependency relations
and named entities in CoNLL-like format, written to comparison.conllu
"""
import sys
import os
import glob
import spacy

def process_file(nlp, path: str) -> str:
    """Return a single file's annotation in CoNLL-U-like format."""
    lines: list[str] = []

    text = open(path, encoding="utf8").read()
    doc = nlp(text)

    lines.append(f"# File: {path}\n")
    for sent in doc.sents:
        lines.append(f"# Sentence: {sent.text.strip()}")
        lines.append("ID\tFORM\tLEMMA\tUPOS\tXPOS\tHEAD\tDEPREL")
        for token in sent:
            lines.append(
                f"{token.i + 1}\t"
                f"{token.text}\t"
                f"{token.lemma_}\t"
                f"{token.pos_}\t"
                f"{token.tag_}\t"
                f"{token.head.i + 1}\t"
                f"{token.dep_}"
            )
        lines.append("")  # blank line between sentences

    # Named-entity section (optional)
    if doc.ents:
        lines.append("# Named Entities:")
        for ent in doc.ents:
            lines.append(f"{ent.text}\t{ent.label_}\t({ent.start_char},{ent.end_char})")

    # Separator between files
    lines.append("\n" + "=" * 80 + "\n")
    return "\n".join(lines)

def main(folder: str) -> None:
    nlp = spacy.load("en_core_web_trf")
    nlp.add_pipe("sentencizer", first=True)

    conllu_chunks: list[str] = []
    for path in glob.glob(os.path.join(folder, "*.txt")):
        conllu_chunks.append(process_file(nlp, path))

    # Dump everything once
    with open("comparison.conllu", "w", encoding="utf8") as f:
        f.write("\n".join(conllu_chunks))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python comparison_spaCy.py <path_to_txt_folder>")
        sys.exit(1)
    main(sys.argv[1])
