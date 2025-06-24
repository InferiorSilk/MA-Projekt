import json
import math
import re
import logging

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
        # Default values. Empty.
        self.observations = set()
        self.start_prob = {}
        self.trans_prob = {}
        self.emit_prob = {}
        self.total_words = 0
        self.total_first_words = 0
        self.total_transitions = 0
        self.tag_counts = {}
        # Pretrained params fromm HMM.py
        self.read_params()

    def read_params(self, filepath="hmm_probabilities.json"):
        logging.debug("reading params...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_params = json.load(f)
                
                self.observations = set(loaded_params.get('observations', []))
                self.start_prob = loaded_params.get('start_prob', {})
                self.trans_prob = loaded_params.get('trans_prob', {})
                self.emit_prob = loaded_params.get('emit_prob', {})
                logging.info(f"HMM parameters loaded from {filepath}")

        except FileNotFoundError:
            logging.warning(f"Warning: {filepath} not found. Initializing with empty parameters.")
        except json.JSONDecodeError:
            logging.warning(f"Error: Could not decode {filepath}. File might be corrupted. Initializing with empty parameters.")
    
    def process(self, text):
        """
        Self made; Example for isinstance-check and comments by AI.
        Ripped from main.py
        """
        logging.debug("params read")
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        if len(text) == 0:
            raise ValueError("Input must not be empty")
        
        # This will split on '.', '!', and '?' while preserving the punctuation. Empty strings will be ignored.
        sentences = re.split('([.!?])', text)
        tagged_text = []
        # Sentences is a list of substrings, one for every sentence in the input.
        for sentence_part in sentences:
            words = re.findall(r"\b[\w']+\b|[.,?!]", sentence_part.lower())
            # Handling of processed sentences by AI.
            if words:
                tags = self.tag(words)
                tagged_text.append(list(zip(words, tags)))
        return tagged_text

    def tag(self, words):
        trellis = [{}] # Viterbi data structure. No idea why its called that.
        backpointers = [{}] # List of dictionaries for backtracking the best tags

        first_word = words[0]
        for tag in self.UPOS_TAGS:
            start_prob = self.start_prob.get(tag, 1e-6) # Get start probability, if not available set to a low smoothing number.
            emit_prob = self.emit_prob.get(tag, {}).get(first_word, 1e-6) # Get emission probability, if not available set to a low smoothing number.

            # Calculate the likelihood of the first word in logarithms
            trellis[0][tag] = math.log(start_prob) + math.log(emit_prob)
            # Set the backpointer to None -> No previous tag since its the first word
            backpointers[0][tag] = None

        # Recursion
        for t in range(1, len(words)):
            # For every word in the sentence, create a new dictionary to store its values in
            trellis.append({})
            backpointers.append({})
            current_word = words[t]

            for current_tag in self.UPOS_TAGS:
                # Logs work in negative values, the lowest negative value is -inf
                # Maximum probability of a path
                max_prob = -math.inf
                # There hasn't been a previous tag yet -> No best previous tag
                best_prev_tag = None

                # Iterate over all possible previous tags (only the previous word's tag)
                for prev_tag in self.UPOS_TAGS:
                    # Get the transition probability from the previous tag to the current tag (for every possible previous tag)
                    trans_prob = self.trans_prob.get(prev_tag, {}).get(current_tag, 1e-6)

                    # Calculate the path probability by adding the previous tag's probability and the transition (log-) probability
                    path_prob = trellis[t-1][prev_tag] + math.log(trans_prob)
                    # If the path probability is higher than the current max, update the max and best previous tag
                    if path_prob > max_prob:
                        max_prob = path_prob
                        best_prev_tag = prev_tag

                # Get the emission probability of the current word
                emission_prob = self.emit_prob.get(current_tag, {}).get(current_word, 1e-6)
                # Calculate the path probability by adding the current tag's probability and the emission (log-) probability
                trellis[t][current_tag] = max_prob + math.log(emission_prob)
                # Set the backpointer to the best previous tag
                backpointers[t][current_tag] = best_prev_tag

        # Find the best last tag (the tag with the highest probability to be the last tag)
        best_last_tag = max(trellis[-1], key=trellis[-1].get)

        # Create a list of the best path
        best_path = [best_last_tag]

        # Iterate over the words in reverse order (Viterbi stores the path "the wrong way around")
        for t in range(len(words) - 1, 0, -1):
            best_last_tag = backpointers[t][best_last_tag]
            best_path.insert(0, best_last_tag)

        return best_path