"""
  Zeman, Daniel; et al., 2024, 
  Universal Dependencies 2.15, LINDAT/CLARIAH-CZ digital library at the Institute of Formal and Applied Linguistics (ÚFAL), Faculty of Mathematics and Physics, Charles University, 
  http://hdl.handle.net/11234/1-5787.
"""
from conllu import parse_incr
import json
import copy
import os

class HMM:
    UPOS_TAGS = [ # Universal Part of Speech Tags
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

    def __init__(self):
        self.states = self.UPOS_TAGS
        self.observations = set()
        
        self.start_counts = {state: 0 for state in self.states}
        self.transition_counts = {state: {state_to: 0 for state_to in self.states} for state in self.states}
        self.emission_counts = {state: {} for state in self.states}
        
        self.total_words = 0
        self.total_first_words = 0
        self.total_transitions = 0
        self.tag_counts = {state: 0 for state in self.states}

    def write_params(self, filepath="hmm_params.json"):
        params = {
            'states': self.states,
            'observations': list(self.observations), # Convert set to list for JSON (set can't be used with dump)
            'start_prob': self.start_counts,          # Using 'start_prob' key as in original JSON
            'trans_prob': self.transition_counts,     # Using 'trans_prob' key
            'emit_prob': self.emission_counts,        # Using 'emit_prob' key
            'total_words': self.total_words,
            'total_first_words': self.total_first_words,
            'total_transitions': self.total_transitions,
            'total_tag_count': self.tag_counts
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)
        print(f"HMM parameters saved to {filepath}")

    def read_params(self, filepath="hmm_params.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_params = json.load(f)
                
                self.observations = set(loaded_params.get('observations', []))
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

    def _train_first(self, sentence_tags):
        if not sentence_tags:
            return
        first_tag = sentence_tags[0]
        self.start_counts[first_tag] += 1
        self.total_first_words += 1

    def _train_trans(self, sentence_tags):
        if len(sentence_tags) < 2:
            return
        for i in range(len(sentence_tags) - 1):
            current_tag = sentence_tags[i]
            next_tag = sentence_tags[i+1]
            self.transition_counts[current_tag][next_tag] += 1
            self.total_transitions += 1 # Increment for each valid transition pair

    def train(self, sentence_word_tag_pairs):
        if not sentence_word_tag_pairs:
            return

        sentence_tags = [tag for word, tag in sentence_word_tag_pairs]

        # Train first words based on tags
        self._train_first(sentence_tags)
        # Train transitions based on tags
        self._train_trans(sentence_tags)

        for word, tag in sentence_word_tag_pairs:
            # Add word to observations
            self.observations.add(word)
    
            # Emission counts
            if word not in self.emission_counts[tag]:
                self.emission_counts[tag][word] = 0
            self.emission_counts[tag][word] += 1
            
            # Tag counts
            self.tag_counts[tag] += 1
            # Total words
            self.total_words += 1
        
    def get_probabilities(self):
        # Create a structure for probabilities, copying counts and other relevant info
        prob_params = {
            'states': list(self.states), # Copy of states
            'observations': set(self.observations), # Copy of observations
            # Deepcopies recommended by AI
            'start_prob': copy.deepcopy(self.start_counts),
            'trans_prob': copy.deepcopy(self.transition_counts),
            'emit_prob': copy.deepcopy(self.emission_counts),
            'total_words': self.total_words,
            'total_first_words': self.total_first_words,
            'total_transitions': self.total_transitions,
            'total_tag_count': copy.deepcopy(self.tag_counts)
        }

        # Calculate Transition Probabilities
        for current_tag in prob_params['trans_prob']:
            total_transitions_from_current = sum(prob_params['trans_prob'][current_tag].values())
            if total_transitions_from_current > 0:
                for next_tag in prob_params['trans_prob'][current_tag]:
                    prob_params['trans_prob'][current_tag][next_tag] /= total_transitions_from_current
            else: # TODO: Laplace smoothing
                for next_tag in prob_params['trans_prob'][current_tag]:
                    prob_params['trans_prob'][current_tag][next_tag] = 0.0


        # Calculate Start Probabilities
        if prob_params["total_first_words"] > 0:
            for tag in prob_params["start_prob"]:
                prob_params["start_prob"][tag] /= prob_params["total_first_words"]
        else:
             for tag in prob_params["start_prob"]:
                prob_params["start_prob"][tag] = 0.0


        # Calculate Emission Probabilities
        for tag in prob_params['emit_prob']:
            total_occurrences_of_tag = prob_params['total_tag_count'].get(tag, 0)
            if total_occurrences_of_tag > 0:
                for word in prob_params['emit_prob'][tag]:
                    prob_params['emit_prob'][tag][word] /= total_occurrences_of_tag
            else: # First time of the tag
                for word in prob_params['emit_prob'][tag]: # Hopefully
                    prob_params['emit_prob'][tag][word] = 0.0
            
        return prob_params

if __name__ == "__main__":
    model = HMM()
    
    # Try to load params
    model.read_params("hmm_params.json") 

    # Define the training data file path
    training_file = "UD_English-GUM/en_gum-ud-train.conllu"

    if not os.path.exists(training_file):
        print(f"Error: Training file not found at {training_file}")
        print("Please ensure the CoNLL-U file is in the correct location.")
    else:
        print(f"Starting training with data from {training_file}...")
        sentence_count = 0
        with open(training_file, "r", encoding="utf-8") as f:
            for tokenlist in parse_incr(f):
                sentence = []
                for token in tokenlist:
                    if isinstance(token["id"], int) and token["form"] is not None and token["upostag"] is not None:
                        sentence.append((token["form"].lower(), token["upostag"])) # Normalize words to lowercase
                
                if sentence: # Make sure theres something
                    model.train(sentence)
                    sentence_count += 1
        
        print(f"Training completed. Processed {sentence_count} sentences.")
        # Save params
        model.write_params("hmm_params.json")