#!/usr/bin/env python3
"""
Convert the output from the HMM-based tagger (viterbi.py) to a format
comparable with the UD_English-GUM format for evaluation.
"""

import sys
import json

def convert_tag_to_ud(tag):
    """
    Convert HMM tagger's tag format to Universal Dependencies format.
    Since the HMM tagger already uses UD tags, this is mostly a pass-through.
    """
    valid_ud_tags = {
        "ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ",
        "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT",
        "SCONJ", "SYM", "VERB", "X"
    }
    
    return tag if tag in valid_ud_tags else "X"

def convert_to_conllu_format(tagged_data):
    """
    Convert the HMM tagger data to CoNLL-U format.
    
    Input format:
    [[["this", "PRON"], ["is", "AUX"], ["a", "DET"], ["test", "NOUN"]]]
    
    Output is CoNLL-U formatted text.
    """
    output_lines = []
    
    # Start with document header
    output_lines.append("# newdoc id = converted_hmm_tagger")
    output_lines.append("# newpar")
    
    current_sent_id = 1
    
    # Process each sentence
    for sentence in tagged_data:
        # Add sentence header
        output_lines.append(f"# sent_id = {current_sent_id}")
        current_sent_id += 1
        
        # Reconstruct the original text
        words = [word_tag[0] for word_tag in sentence]
        text = ' '.join(words)
        output_lines.append(f"# text = {text}")
        
        # Add each token
        for token_id, (word, tag) in enumerate(sentence, 1):
            # Convert to UD tag if needed (already should be UD format)
            ud_tag = convert_tag_to_ud(tag)
            
            # Format: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
            token_line = f"{token_id}\t{word}\t_\t{ud_tag}\t_\t_\t_\t_\t_\t_"
            output_lines.append(token_line)
        
        # Add sentence separator
        output_lines.append("")
    
    return "\n".join(output_lines)

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            tagged_data = json.load(f)
        
        conllu_output = convert_to_conllu_format(tagged_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(conllu_output)
        
        print(f"Conversion complete. Output written to {output_file}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
