"""
  Zeman, Daniel; et al., 2024, 
  Universal Dependencies 2.15, LINDAT/CLARIAH-CZ digital library at the Institute of Formal and Applied Linguistics (ÚFAL), Faculty of Mathematics and Physics, Charles University, 
  http://hdl.handle.net/11234/1-5787.
"""
from conllu import parse_incr
import json

states = upos_tags = [
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

observations = set()

start_prob = {state: 0 for state in states}

trans_prob = {state: {state_to: 0 for state_to in states} for state in states}

emit_prob = {state: {} for state in states}

total_words = 0
total_first_words = 0
total_transitions = 0
total_tag_count = {state: 0 for state in states}

global hmm_params
hmm_params = {
    'states': states,
    'observations': observations,
    'start_prob': start_prob,
    'trans_prob': trans_prob,
    'emit_prob': emit_prob,
    'total_words': total_words,
    'total_first_words': total_first_words,
    'total_transitions': total_transitions,
    'total_tag_count': total_tag_count
}

def write_params():
    with open("hmm_params.json", "w", encoding="utf-8") as f:
        json.dump(hmm_params, f, indent=2)

def read_params():
    with open('hmm_params.json', 'r', encoding='utf-8') as f:
        hmm_params = json.load(f)
        return hmm_params

def read_observations():
    with open("UD_English-GUM/en_gum-ud-train.conllu", "r", encoding="utf-8") as f:
        for tokenlist in parse_incr(f):
            words = [token["form"] for token in tokenlist if isinstance(token["id"], int)]
            observations.update(words)
            train_emit(words)

def train(sentence):
    if not sentence:
        return
    # Train first words
    train_first(sentence)
    # Train transitions
    train_trans(sentence)

    for word, tag in sentence:
        # Add word to observations
        if word not in hmm_params["observations"]:
            hmm_params["observations"].add(word)
    
        # Emitions and stuff
        if word not in hmm_params['emit_prob'][tag]:
            hmm_params['emit_prob'][tag][word] = 0
        hmm_params['emit_prob'][tag][word] += 1
        # Tag counts
        hmm_params['total_tag_count'][tag] += 1
        # Total words
        hmm_params["total_words"] += 1

def train_emit(words):
    for word in words:
        if word in emit_prob:
            emit_prob[word]["tag"] += 1
        else:
            emit_prob[word] = 1
        
def train_first(sentence):
    first_tag = sentence[0][1]
    hmm_params["start_prob"][first_tag] += 1
    hmm_params["total_first_words"] += 1

def train_trans(sentence):
    for i in range(len(sentence) - 1):
        hmm_params["total_transitions"] += 1
        current_tag = sentence[i][1]
        next_tag = sentence[i+1][1]
        hmm_params["trans_prob"][current_tag][next_tag] += 1

def calculate_prob():
    # Calculate Transition Probabilities 
    for current_tag in hmm_params['trans_prob']:
        total_transitions_from_current = sum(hmm_params['trans_prob'][current_tag].values())
        if total_transitions_from_current > 0:
            for next_tag in hmm_params['trans_prob'][current_tag]:
                hmm_params['trans_prob'][current_tag][next_tag] /= total_transitions_from_current
    
    # Calculate Start Probabilities 
    if hmm_params["total_first_words"] > 0:
        for tag in hmm_params["start_prob"]:
            hmm_params["start_prob"][tag] /= hmm_params["total_first_words"]

    # Calculate Emission Probabilities 
    for tag in hmm_params['emit_prob']:
        total_occurrences_of_tag = hmm_params['total_tag_count'].get(tag, 0)
        if total_occurrences_of_tag > 0:
            for word in hmm_params['emit_prob'][tag]:
                hmm_params['emit_prob'][tag][word] /= total_occurrences_of_tag

with open("UD_English-GUM/en_gum-ud-train.conllu", "r", encoding="utf-8") as f:
    for tokenlist in parse_incr(f):
        sentence = [(token["form"], token["upostag"]) for token in tokenlist if isinstance(token["id"], int)]
        train(sentence)