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

    def write_params(self, params, filepath="hmm_probabilities.json"):
        """
        Writes a given dictionary of parameters to a JSON file.
        It now accepts a 'params' dictionary as its primary data source.
        """
        # Use a passed-through dictionary instead of building one. Fix to accompany the refactor of __main__
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)
        print(f"HMM parameters saved to {filepath}")

    # For Viterbi, read written params
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
        """
        Calculates the start, transition, and emission probabilities from the raw counts. Laplace smoothing implemented.
        """
        num_states = len(self.states)
        num_observations = len(self.observations)

        # Calculate Start Probabilities
        start_prob = {}
        # + num_states for smoothing
        denominator = self.total_first_words + num_states
        for tag in self.states:
            # Add 1 to avoid counts of 0
            start_prob[tag] = (self.start_counts.get(tag, 0) + 1) / denominator

        # Calculate Transition Probabilities
        trans_prob = {state: {} for state in self.states}
        for from_state, transitions in self.transition_counts.items():
            total_transitions_from_state = sum(transitions.values())
            denominator = total_transitions_from_state + num_states
            for to_state in self.states:
                count = transitions.get(to_state, 0)
                trans_prob[from_state][to_state] = (count + 1) / denominator

        # Calculate Emission Probabilities
        emit_prob = {state: {} for state in self.states}
        for state, emissions in self.emission_counts.items():
            total_emissions_from_state = self.tag_counts.get(state, 0)
            # + num_states for smoothing
            denominator = total_emissions_from_state + num_observations
            for word, count in emissions.items():
                emit_prob[state][word] = (count + 1) / denominator
            # Token for unknown words. Recommended by AI.
            emit_prob[state]['<UNK>'] = 1 / denominator

        # Return a new dictionary containing the probabilities
        prob_params = {
            'states': self.states,
            'observations': list(self.observations),
            'start_prob': start_prob,
            'trans_prob': trans_prob,
            'emit_prob': emit_prob,
        }
        return prob_params

if __name__ == "__main__":
    # Initialize a new model every time the script runs.
    model = HMM()

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
                    if isinstance(token["id"], int) and token["form"] and token["upostag"]:
                        sentence.append((token["form"].lower(), token["upostag"]))
                
                if sentence:
                    model.train(sentence)
                    sentence_count += 1
        
        print(f"Training completed. Processed {sentence_count} sentences.")
        
        # Calculate probabilities after training is complete.
        print("Calculating probabilities...")
        final_params = model.get_probabilities()
        
        # Save the final calculated probabilities, not the raw counts.
        model.write_params(final_params, "hmm_probabilities.json")