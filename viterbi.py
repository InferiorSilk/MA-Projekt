import json
import math

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
        probabilities = {}
        for tag in self.UPOS_TAGS:
            probability = math.log(self.emission_counts[tag][first_word]) + math.log(self.start_counts[tag])
            probabilities[tag] = probability
        self.highest_prob = max(probabilities, key=probabilities.get)