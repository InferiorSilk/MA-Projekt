"""
compare_with_spacy.py

Read raw text files (e.g. [en_gum-ud-test.txt](file:///C:/Users/wulfa/Documents/Docs/Programming/Python/Chat/NLPV2/MA-Projekt/UD_English-GUM/en_gum-ud-test.txt))
and run spaCy's transformer pipeline on them. Outputs tokens, lemmas, POS tags, dependency relations and named entities in CoNLL-like format.
Fully made by AI
"""

import sys
import os
import glob
import spacy

def process_file(nlp, path):
    text = open(path, encoding='utf8').read()
    doc = nlp(text)
    print(f"# File: {path}\n")
    for sent in doc.sents:
        print(f"# Sentence: {sent.text.strip()}")
        print("ID\tFORM\tLEMMA\tUPOS\tXPOS\tHEAD\tDEPREL")
        for token in sent:
            print(
                f"{token.i+1}\t"
                f"{token.text}\t"
                f"{token.lemma_}\t"
                f"{token.pos_}\t"
                f"{token.tag_}\t"
                f"{token.head.i+1}\t"
                f"{token.dep_}"
            )
        print()
    # Named Entities
    if doc.ents:
        print("# Named Entities:")
        for ent in doc.ents:
            print(f"{ent.text}\t{ent.label_}\t({ent.start_char},{ent.end_char})")
    print("\n" + "="*80 + "\n")

def main(folder):
    # Load spaCy transformer model
    nlp = spacy.load("en_core_web_trf")
    nlp.add_pipe("sentencizer")  # ensure sentence boundaries
    
    # Iterate over all .txt files in folder
    for path in glob.glob(os.path.join(folder, "*.txt")):
        process_file(nlp, path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python comparison_spaCy.py <path_to_txt_folder>")
        sys.exit(1)
    main(sys.argv[1])
