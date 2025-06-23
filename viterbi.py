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
        self.results = []
    def read_params(self, filepath="hmm_params.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_params = json.load(f)
                
                self.observations = set(loaded_params.get('observations', [])) # Provide fallback if the key doesnt exist (would be very weird)
                self.start_counts = loaded_params.get('start_prob', self.start_counts)
                self.transition_counts = loaded_params.get('trans_prob', self.transition_counts)
                self.emission_counts = loaded_params.get('emit_prob', self.emission_counts)
                self.total_words = loaded_params.get('total_words', 0)
                self.total_first_words = loaded_params.get('total_first_words', 0)
                self.total_transitions = loaded_params.get('total_transitions', 0)
                self.tag_counts = loaded_params.get('total_tag_count', self.tag_counts)
                print(f"HMM parameters loaded from {filepath}")

        except FileNotFoundError:
            print(f"Warning: {filepath} not found. Initializing with empty parameters.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode {filepath}. File might be corrupted. Initializing with empty parameters.")
            self.__init__() # Reset to default (for safety)

    def first_word(self, first_word):
        start_probabilities = {}
        for tag in self.UPOS_TAGS:
            # Log for very small numbers that float couldnt display
            start_probabilities[tag] = math.log(self.emission_counts[tag][first_word]) + math.log(self.start_counts[tag])
        self.highest_start_prob = max(start_probabilities, key=start_probabilities.get)
        return {first_word: self.highest_start_prob}
    
    def not_first_word(self, word, previous_tag):
        probabilities = {}
        for tag in self.UPOS_TAGS:
            probabilities[tag] = math.log(self.emission_counts[tag][word]) + math.log(self.transition_counts[previous_tag][tag])
        return max(probabilities, key=probabilities.get)
    
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
            self.determine(words)

    def determine(self, words):
        for i in len(words):
            if words[i-1] is None:
                self.results.append(self.first_word(words[i]))
            else:
                self.results.append(self.not_first_word(words[i], self.results[i-1][words[i-1]]))