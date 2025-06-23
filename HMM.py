"""
  Zeman, Daniel; et al., 2024, 
  Universal Dependencies 2.15, LINDAT/CLARIAH-CZ digital library at the Institute of Formal and Applied Linguistics (ÚFAL), Faculty of Mathematics and Physics, Charles University, 
  http://hdl.handle.net/11234/1-5787.
"""
from conllu import parse_incr
import json
import os
from collections import Counter # For counting vocabulary. Suggested by AI.

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

    def __init__(self, vocabulary):
        self.states = self.UPOS_TAGS
        self.observations = vocabulary
        
        self.start_counts = {state: 0 for state in self.states}
        self.transition_counts = {state: {state_to: 0 for state_to in self.states} for state in self.states}
        self.emission_counts = {state: {} for state in self.states}
        
        self.total_first_words = 0
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

    def train(self, sentence_word_tag_pairs):
        if not sentence_word_tag_pairs:
            return

        sentence_tags = [tag for word, tag in sentence_word_tag_pairs]

        self._train_first(sentence_tags)
        self._train_trans(sentence_tags)

        for word, tag in sentence_word_tag_pairs:
    
            # Calculate emission counts
            self.emission_counts[tag].setdefault(word, 0)
            self.emission_counts[tag][word] += 1
            
            # Calculate tag counts
            self.tag_counts[tag] += 1
        
    def get_probabilities(self):
        """
        Calculates the start, transition, and emission probabilities from the raw counts. 
        Laplace smoothing is implemented.
        """
        num_states = len(self.states)
        vocabulary_size = len(self.observations)

        # Calculate Start Probabilities
        start_prob = {}
        for tag in self.states:
            start_prob[tag] = (self.start_counts.get(tag, 0) + 1) / (self.total_first_words + num_states)

        # Calculate Transition Probabilities
        trans_prob = {state: {} for state in self.states}
        for from_state in self.states:
            total_transitions_from_state = sum(self.transition_counts.get(from_state, {}).values())

            for to_state in self.states:
                count = self.transition_counts.get(from_state, {}).get(to_state, 0)
                trans_prob[from_state][to_state] = (count + 1) / (total_transitions_from_state + num_states)

        # Calculate Emission Probabilities
        emit_prob = {state: {} for state in self.states}
        for state in self.states:
            total_emissions_from_state = self.tag_counts.get(state, 0)
            denominator = total_emissions_from_state + vocabulary_size
            
            for word in self.observations:
                count = self.emission_counts.get(state, {}).get(word, 0)
                emit_prob[state][word] = (count + 1) / denominator

        # Return a new dictionary containing the probabilities
        prob_params = {
            'states': self.states,
            'observations': list(self.observations), # List for json.dump()
            'start_prob': start_prob,
            'trans_prob': trans_prob,
            'emit_prob': emit_prob,
        }
        return prob_params

if __name__ == "__main__":
    # The program flow was shown by AI. Specific variables and actions (e.g. <UNK> and the frequency threshold) shown by AI.
    training_file = "UD_English-GUM/en_gum-ud-train.conllu"
    # Define a frequency threshold for a word to be considered "known"
    # Words appearing less than or equal to this many times will get the tag "<UNK>"
    FREQUENCY_THRESHOLD = 1 
    UNK_TOKEN = "<UNK>"

    if not os.path.exists(training_file):
        print(f"Error: Training file not found at {training_file}")
        print("Please ensure the CoNLL-U file is in the correct location.")
        exit()

    # Build the vocabulary (for smoothing)
    print("Building vocabulary...")
    word_frequencies = Counter()
    all_sentences = [] # Store sentences to avoid reading file twice. Suggested by AI
    # Read the training file
    with open(training_file, "r", encoding="utf-8") as f:
        for tokenlist in parse_incr(f):
            sentence = []
            for token in tokenlist:
                if isinstance(token["id"], int) and token["form"] and token["upostag"]:
                    word = token["form"].lower()
                    sentence.append((word, token["upostag"]))
                    word_frequencies[word] += 1
            if sentence:
                all_sentences.append(sentence)

    # Create the final vocabulary
    final_vocabulary = {word for word, freq in word_frequencies.items() if freq > FREQUENCY_THRESHOLD}
    final_vocabulary.add(UNK_TOKEN)
    
    print(f"Building vocabulary complete. Original words: {len(word_frequencies)}. Final vocabulary size: {len(final_vocabulary)}.")

    # Initialize the Model with the final vocabulary
    model = HMM(vocabulary=final_vocabulary)

    # Train the Model
    print("Training the HMM...")
    for sentence in all_sentences:
        processed_sentence = []
        for word, tag in sentence:
            # Replace rare words with the UNK_TOKEN
            if word not in final_vocabulary:
                processed_sentence.append((UNK_TOKEN, tag))
            else:
                processed_sentence.append((word, tag))
        
        if processed_sentence:
            model.train(processed_sentence)
    
    print(f"Training completed. Processed {len(all_sentences)} sentences.")
    
    # Calculate and Save Probabilities
    print("Calculating probabilities...")
    final_params = model.get_probabilities()
    model.write_params(final_params, "hmm_probabilities.json")