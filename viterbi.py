import json
import math
import re

class Viterbi():
    def __init__(self):
        self.UPOS_TAGS = [ # Universal Part of Speech Tags
            "ADJ",   # Adjective
            "ADP",   # Adposition
            "ADV",   # Adverb
            "AUX",   # Auxiliary
            "CCONJ", # Coordinating conjunction
            "DET",   # Determiner
            "INTJ",  # Interjection
            "NOUN",  # Noun
            "NUM",   # Numeral
            "PART",  # Particle
            "PRON",  # Pronoun
            "PROPN", # Proper noun
            "PUNCT", # Punctuation
            "SCONJ", # Subordinating conjunction
            "SYM",   # Symbol
            "VERB",  # Verb
            "X"      # Other
        ]

    def read_params(self, filepath="hmm_params.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_params = json.load(f)
                
                self.observations = set(loaded_params.get('observations', []))
                self.start_prob = loaded_params.get('start_prob')
                self.trans_prob = loaded_params.get('trans_prob')
                self.emit_prob = loaded_params.get('emit_prob')
                self.total_words = loaded_params.get('total_words', 0)
                self.total_first_words = loaded_params.get('total_first_words', 0)
                self.total_transitions = loaded_params.get('total_transitions', 0)
                self.tag_counts = loaded_params.get('total_tag_count')
                print(f"HMM parameters loaded from {filepath}")

        except FileNotFoundError:
            print(f"Warning: {filepath} not found. Initializing with empty parameters.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode {filepath}. File might be corrupted. Initializing with empty parameters.")
            self.__init__() # Reset to default (for safety)
    
    def process(self, text):
        """
        Self made; Example for isinstance-check and comments by AI.
        Ripped from main.py
        """
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        if len(text) == 0:
            raise ValueError("Input must not be empty")
        
        # This will split on '.', '!', and '?' while preserving the punctuation
        sentences = re.split('([.!?])', text)
        # Sentences is a list of lists, one list for every sentence in the input.
        for sentence in sentences:
            words = re.findall(r"\b[\w']+\b|[.,?!]", sentence.lower())
            self.tag(words)

    def tag(self, words):
        trellis = [{}] # Viterbi data structure. No idea why its called that.
        backpointers = [{}]

        first_word = words[0]
        for tag in self.UPOS_TAGS:
            start_prob = self.start_prob.get(tag)
            emit_prob = self.emit_prob.get(tag, {}).get(first_word, 1e-6) # Get emission probability, if not available set to a low smoothing number.

            trellis[0][tag] = math.log(start_prob) + math.log(emit_prob)
            backpointers[0][tag] = None

        # Recursion
        for t in range(1, len(words)):
            trellis.append({})
            backpointers.append({})
            current_word = words[t]

            for current_tag in self.UPOS_TAGS:
                max_prob = -math.inf
                best_prev_tag = None

                for prev_tag in self.UPOS_TAGS:
                    trans_prob = self.trans_prob.get(prev_tag, {}).get(current_tag, 1e-6)

                    path_prob = trellis[t-1][prev_tag] + math.log(trans_prob)
                    if path_prob > max_prob:
                        max_prob = path_prob
                        best_prev_tag = prev_tag

                emission_prob = self.emit_prob.get(current_tag, {}).get(current_word, 1e-6)
                trellis[t][current_tag] = max_prob + math.log(emission_prob)
                backpointers[t][current_tag] = best_prev_tag

        best_last_tag = max(trellis[-1], key=trellis[-1].get)

        best_path = [best_last_tag]

        for t in range(len(words) - 1, 0, -1):
            best_last_tag = backpointers[t][best_last_tag]
            best_path.insert(0, best_last_tag)

        return best_path