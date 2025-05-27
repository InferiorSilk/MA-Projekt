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

start_prob = {
    "ADJ": 0,
    "ADP": 0,
    "ADV": 0,
    "AUX": 0,
    "CCONJ": 0,
    "DET": 0,
    "INTJ": 0,
    "NOUN": 0,
    "NUM": 0,
    "PART": 0,
    "PRON": 0,
    "PROPN": 0,
    "PUNCT": 0,
    "SCONJ": 0,
    "SYM": 0,
    "VERB": 0,
    "X": 0
}

trans_prob = {
    "ADJ": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "ADP": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "ADV": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "AUX": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "CCONJ": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "DET": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "INTJ": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "NOUN": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "NUM": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "PART": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "PRON": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "PROPN": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "PUNCT": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "SCONJ": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "SYM": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "VERB": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0},
    "X": {"ADJ": 0, "ADP": 0, "ADV": 0, "AUX": 0, "CCONJ": 0, "DET": 0, "INTJ": 0, "NOUN": 0, "NUM": 0, "PART": 0, "PRON": 0, "PROPN": 0, "PUNCT": 0, "SCONJ": 0, "SYM": 0, "VERB": 0, "X": 0}
}

emit_prob = {}

total_words = 0
total_first_words = 0

global hmm_params
hmm_params = {
    'states': states,
    'observations': observations,
    'start_prob': start_prob,
    'trans_prob': trans_prob,
    'emit_prob': emit_prob,
    'total_words': total_words,
    'total_first_words': total_first_words
}

def train(sent):
    pass

def write(params):
    with open("hmm_params.json", "w", encoding="utf-8") as f:
        json.dump(hmm_params, f, indent=2)

with open("UD_English-GUM/en_gum-ud-train.conllu", "r", encoding="utf-8") as f:
    for tokenlist in parse_incr(f):
        sentence = [(token["form"], token["upostag"]) for token in tokenlist if isinstance(token["id"], int)]
        train(sentence)

def open():
    with open('hmm_params.json', 'r', encoding='utf-8') as f:
        hmm_params = json.load(f)

def read_observations():
    with open("UD_English-GUM/en_gum-ud-train.conllu", "r", encoding="utf-8") as f:
        for tokenlist in parse_incr(f):
            words = [token["form"] for token in tokenlist if isinstance(token["id"], int)]
            observations.update(words)

        train_emit(words)

def train(sentence):
    train_first(sentence)
    train_trans(sentence)

def train_emit(words):
    for word in words:
        if word in emit_prob:
            emit_prob[word] += 1
        else:
            emit_prob[word] = 0
        
def train_first(sentence):
    first_tag = sentence[0][1]
    hmm_params["start_prob"][first_tag] += 1
    hmm_params["total_words"] += 1

def train_trans(sentence):
    for i in range(len(sentence) - 1):
        current_tag = sentence[i][1]
        next_tag = sentence[i+1][1]
        hmm_params['trans_prob'][current_tag][next_tag] += 1

def calculate_prob():
    trans_prob_temp = trans_prob
    start_prob_temp = start_prob
    emit_prob_temp = emit_prob
    for i in trans_prob_temp:
        for ii in i:
            trans_prob[ii] = trans_prob_temp[ii] / total_words
    
    for i in start_prob_temp:
        start_prob[i] = start_prob_temp[i] / total_first_words

    for i in emit_prob_temp:
        emit_prob[i] = emit_prob_temp[i] / total_words