import dictionaries
from enum import Enum
import logging
from main import NLP

class Tag(Enum):
    NOUN = 'noun'
    VERB = 'verb'
    ADJECTIVE = 'adjective'
    ADVERB = 'adverb'
    PRONOUN = 'pronoun'
    DETERMINER = 'determiner'
    PREPOSITION = 'preposition'
    CONJUNCTION = 'conjunction'
    INTERJECTION = 'interjection'
    NUMBER = 'number'
    PUNCTUATION = 'punctuation'
    UNCERTAIN = 'uncertain'

class Tagging:
    """Tagging class for tagging words in context.

    Attributes:
        patterns (dict): Dictionary containing patterns for tagging words
        sentence_connectors (frozenset): Frozen set containing sentence connectors
        sentence_amount (int): Number of sentences in the list of sentences
        list_of_sentences (list): List of sentences to process

    Pattern matching (_is_is_pattern()), _get_pattern_tag()), comments and formating done by AI
    """
    def __init__(self, patterns):
        self.patterns = patterns
        self.sentence_connectors = frozenset(['and', 'but', 'or', 'nor', 'for', 'yet', 'so'])  # Add sentence connectors
        self.sentence_amount = 0
        self.list_of_sentences = []   

    def _tag_word_in_context(self, word, prev_word, next_word, prev_prev_word, next_next_word, tagged_words):
        """Tag the word in context.
        
        Args:
            word: String containing the word to tag
            prev_word: String containing the previous word
            next_word: String containing the next word
            prev_prev_word: String containing the previous previous word
            next_next_word: String containing the next next word
            tagged_words: Dictionary containing tagged words
            
        Returns:
            Tag of the word
        """
        # First check for auxiliary verbs and common verb forms
        try:
            logging.info(tagged_words)
            if self._is_number(word):
                return Tag.NUMBER.value
            logging.debug("Checking for determiner")
            if self._is_determiner(word):
                return Tag.DETERMINER.value
            logging.debug("Checked for determiner")
            if self._is_preposition(word):
                return Tag.PREPOSITION.value
            logging.debug("Checked for preposition")
            if self._is_conjunction(word):
                return Tag.CONJUNCTION.value
            logging.debug("Checked for conjunction")
            if self._is_pronoun(word):
                return Tag.PRONOUN.value
            logging.debug("Checked for pronoun")
            if word in ['.', ',', '?', '!', ':', ';', '-']:
                return Tag.PUNCTUATION.value
            logging.debug("Punctuation checked")
            if self._is_adjective(word, prev_word, tagged_words):
                return Tag.ADJECTIVE.value
            logging.debug("Adjective checked")
            if prev_word is not None and self._is_verb(word, prev_word, tagged_words):
                return Tag.VERB.value
            logging.debug(f"Checked for verb for word '{word}'")
            if self._is_adjective_after_adverb(word, prev_word, tagged_words):
                return Tag.ADJECTIVE.value
            if self._is_noun_after_preposition(next_word, next_next_word):
                return Tag.NOUN.value
            if self._is_sentence_connection(tagged_words, word, prev_word, prev_prev_word) and 'tag' in tagged_words[prev_prev_word]:
                return tagged_words[prev_prev_word]['tag']
            if self._is_verb_after_verb(tagged_words, prev_word, prev_prev_word):
                return Tag.VERB.value
            if self._is_adverb_after_verb(word, prev_word, tagged_words, prev_prev_word):
                return Tag.ADVERB.value
            if self._is_interjection(word):
                return Tag.INTERJECTION.value
            if self._get_tag_by_ending(word, prev_word, tagged_words) != False:
                logging.info(self._get_tag_by_ending(word, prev_word, tagged_words))
                logging.info(tagged_words)
                return self._get_tag_by_ending(word, prev_word, tagged_words)
            logging.debug("Tagging by ending checked")

            return self._fallback_tagging(word, prev_word, next_word)
        except Exception as e:
            logging.warning(f"Error tagging '{word}: {str(e)}")

    def _is_adjective(self, word, prev_word, tagged_words):
        return prev_word in set(["is", "am", "be"]) and tagged_words[word]['ending'] != 'ing'

    def _is_verb(self, word, prev_word, tagged_words):
        logging.debug("Checking for verb")
        return tagged_words[prev_word]['tag'] == Tag.PRONOUN.value

    def _get_tag_by_ending(self, word, prev_word, tagged_words):
        """Helper method to get the tag based on the word ending.
        
        Args:
            word: String containing the word to tag
            prev_word: String containing the previous word
            tagged_words: Dictionary containing tagged words
            
        Returns:
            Tag of the word
        """ 
        try:
            logging.debug("Trying to tag by ending")
            if tagged_words[word]['ending'] == 'ly':
                return Tag.ADVERB.value
            elif tagged_words[word]['ending'] == 'tion':
                return Tag.NOUN.value
            elif tagged_words[word]['ending'] == 'able' or tagged_words[word]['ending'] == 'ible'or tagged_words[word]['ending'] == 'ic' or tagged_words[word]['ending'] == 'al':
                return Tag.ADJECTIVE.value
            elif tagged_words[word]['ending'] == 'es':
                return Tag.VERB.value
            elif tagged_words[word]['ending'] == 'ing' or tagged_words[word]['ending'] == 'ed':
                if tagged_words[prev_word]['tag'] != 'determiner':
                    return Tag.VERB.value
                return Tag.ADJECTIVE.value                
            else:
                return False
        except Exception as e:
            logging.warning(f"Failed to tag by ending: {str(e)}")

    def _is_number(self, word):
        return word.isdigit()

    def _is_determiner(self, word):
        return word in self.patterns['determiners']

    def _is_preposition(self, word):
        return word in self.patterns['prepositions']

    def _is_conjunction(self, word):
        return word in self.patterns['conjunctions']

    def _is_pronoun(self, word):
        return word in self.patterns['pronouns']

    def _is_auxiliary_after(self, word):
        return word in set({'to', 'will', 'can', 'must', 'should', 'would', 'could', 'may', 'might'})

    def _is_adjective_after_adverb(self, word, prev_word, tagged_words):
        return prev_word in set({'veri', 'quite', 'rather', 'extremely'}) and tagged_words[word]['ending'] != 'ly'

    def _is_noun_after_preposition(self, next_word, next_next_word):
        return next_word in dictionaries.patterns['prepositions'] and next_next_word in dictionaries.patterns['determiners']

    def _is_sentence_connection(self, tagged_words, word, prev_word, prev_prev_word):
        if (prev_word is not None and prev_prev_word is not None and 
            prev_word in self.sentence_connectors and 
            prev_prev_word in tagged_words and
            'tag' in tagged_words[prev_prev_word]):
            return True
        return False

    def _is_verb_after_verb(self, tagged_words, prev_word, prev_prev_word):
        if (prev_word is not None and prev_prev_word is not None and 
            prev_word in tagged_words and prev_prev_word in tagged_words and
            'ending' in tagged_words[prev_word] and 'tag' in tagged_words[prev_prev_word] and
            tagged_words[prev_word]['ending'] == 'ing' and tagged_words[prev_prev_word]['tag'] == Tag.VERB.value):
            return True
        return False

    def _is_adverb_after_verb(self, word, prev_word, tagged_words, prev_prev_word):
        """Check if word is an adverb that comes after a verb
        
        Args:
            word: String containing the word to tag
            prev_word: String containing the previous word
            tagged_words: Dictionary containing tagged words
            prev_prev_word: String containing the previous previous word
            
        Returns:
            True if the word is an adverb that comes after a verb, False otherwise
        """
        # First check if we have valid previous word data
        if not prev_word or prev_word not in tagged_words:
            return False
            
        # Check if current word is in adverbs dictionary
        if word not in dictionaries.adverbs:
            return False
            
        # Simple case: word is after a verb
        if ('tag' in tagged_words[prev_word] and 
            tagged_words[prev_word]['tag'] == Tag.VERB.value):
            return True
            
        # Complex case: check prev_prev_word pattern
        if (prev_prev_word and 
            prev_prev_word in tagged_words and 
            'ending' in tagged_words[prev_prev_word] and
            'tag' in tagged_words[prev_word] and 
            'ending' in tagged_words[prev_word] and
            tagged_words[prev_prev_word]['ending'] == 'ing' and 
            tagged_words[prev_word]['tag'] == Tag.VERB.value and 
            tagged_words[prev_word]['ending'] != 'ing'):
            return True
            
        return False

    def _is_interjection(self, word):
        return word in set({'oh', 'wow', 'hey', 'uh', 'um'})

    def _fallback_tagging(self, word, prev_word, next_word):
        """Fallback tagging logic with additional context awareness.
        
        Args:
            word: String containing the word to tag
            prev_word: String containing the previous word
            next_word: String containing the next word
            
        Returns:
            Tag of the word
        """
        if word in dictionaries.verbs or word in dictionaries.irregular_verbs or word in dictionaries.irregular_verbs_list:
            return Tag.VERB.value
        elif word in dictionaries.nouns:
            return Tag.NOUN.value
        elif word in dictionaries.adjectives:
            return Tag.ADJECTIVE.value
        elif word in dictionaries.adverbs:
            return Tag.ADVERB.value
        elif word in dictionaries.adjectives and prev_word in {'very', 'quite', 'rather'}:
            return Tag.ADJECTIVE.value
        elif word in dictionaries.irregular_verbs:
            return Tag.VERB.value
        for irregular_verb in dictionaries.irregular_verbs:
            for time_form in dictionaries.irregular_verbs[irregular_verb]:
                if word in dictionaries.irregular_verbs[irregular_verb][time_form]:
                    return Tag.VERB.value
        return self._additional_contextual_patterns(prev_word, next_word)

    def _additional_contextual_patterns(self, prev_word, next_word):
        if prev_word is not None and prev_word in {'is', 'are', 'was', 'were'} and next_word is not None and next_word in {'by', 'with'}:
            return Tag.VERB.value
        logging.info("The tag was given by exclusion")
        return Tag.UNCERTAIN.value  # Default to uncertain if no pattern matches

class Tense:
    """THE USE OF THIS CLASS IS DEPRECATED, I LEFT IT HERE FOR COMPLETENESS"""
    def __init__(self):        
        # Modal verbs that indicate specific tenses
        self.modal_verbs_tense = {
            'will': 'future',
            'shall': 'future',
            'would': 'conditional',
            'should': 'conditional',
            'may': 'present',
            'might': 'present',
            'can': 'present',
            'could': 'past',
            'must': 'present'
        }
        
        # Auxiliary patterns for compound tenses
        self.auxiliary_patterns = [
            # Present continuous
            {
                'auxiliaries': ['am', 'is', 'are'],
                'verb_suffix': 'ing',
                'tense': 'present_continuous'
            },
            # Past continuous
            {
                'auxiliaries': ['was', 'were'],
                'verb_suffix': 'ing',
                'tense': 'past_continuous'
            },
            # Present perfect
            {
                'auxiliaries': ['have', 'has'],
                'verb_suffix': 'ed',
                'tense': 'present_perfect'
            },
            # Past perfect
            {
                'auxiliaries': ['had'],
                'verb_suffix': 'ed',
                'tense': 'past_perfect'
            },
            # Future perfect
            {
                'auxiliaries': ['will have', 'shall have'],
                'verb_suffix': 'ed',
                'tense': 'future_perfect'
            },
            # Future continuous
            {
                'auxiliaries': ['will be', 'shall be'],
                'verb_suffix': 'ing',
                'tense': 'future_continuous'
            }
        ]

    def _get_tense(self, sentence):
        """
        Determine the tense of a sentence through comprehensive analysis.
        
        Args:
            sentence: Dictionary containing words with their tags and endings
            
        Returns:
            str: The identified tense

        Self made; The complex looking append statement and formating done by AI, just like the check for irregular verbs and small statements like the one to handle multi word auxiliaries and the blueprint for checking the tense.
        """
        words = []
        verb_forms = []
        
        # Extract words and identify verb forms
        for word_info in sentence.values():
            word = word_info.get('word', '') # .lower()
            tag = word_info.get('tag', '')
            ending = word_info.get('ending', '')
            
            words.append(word)
            if tag == Tag.VERB.value or word in sum([forms['present'] + forms['past'] + forms['past_participle'] 
                                                    for forms in dictionaries.irregular_verbs.values()], []):
                verb_forms.append((word, ending))

        # Join words to handle multi-word auxiliaries
        text = ' '.join(words)
        
        # Check for future
        if any(aux in text for aux in ['will', 'shall', 'going to']):
            return 'future'
            
        # Check for present/past perfect continuous
        if 'have been' in text and any(v[1] == 'ing' for v in verb_forms) or 'had been' in text and any(v[1] == 'ing' for v in verb_forms):
            return 'present'
            
        # Check compound tenses
        for pattern in self.auxiliary_patterns:
            if any(aux in text for aux in pattern['auxiliaries']):
                for verb, ending in verb_forms:
                    # Check if verb matches pattern
                    if ending == pattern['verb_suffix'] or any(verb in forms['past_participle'] 
                                                             for forms in dictionaries.irregular_verbs.values()):
                        return pattern['tense']
        
        # Check modal verbs
        for modal, tense in self.modal_verbs_tense.items():
            if modal in words:
                return tense
                
        # Check irregular verbs
        for verb_info in dictionaries.irregular_verbs.values():
            for word, _ in verb_forms:
                if word in verb_info['past']:
                    return 'past'
                if word in verb_info['present']:
                    return 'present'
                if word in verb_info['past_participle']:
                    # Look for auxiliary to determine perfect tense
                    if any(aux in words for aux in ['have', 'has']):
                        return 'present'
                    if 'had' in words:
                        return 'past'
        
        # Check regular verb patterns
        for word, ending in verb_forms:
            if ending == 'ed':
                return 'past'
            elif ending == 'ing':
                # Check for auxiliary to determine continuous tense
                if any(aux in words for aux in ['am', 'is', 'are']):
                    return 'present'
                if any(aux in words for aux in ['was', 'were']):
                    return 'past'
            elif ending == 's':
                return 'present'  # Third person singular present
            
        # Look for base form verbs
        if any(word in dictionaries.verbs for word, _ in verb_forms):
            return 'present'
            
        return 'present'  # Default case
    
class Type(Enum):
    SUBJECT = 'subject'
    ACTION = 'action'
    OBJECT = 'object'
    LOCATION = 'location'
    TIME = 'time'
    MANNER = 'manner'

class Semantic_Role_Labelling():
    """Self made. Some comments by AI"""

    def __init__(self):
        pass

    def label_roles(self, word, prev_word, tagged_words, next_word):
        """Label the semantic roles of each word in the sentence.

        Args:
            word: String containing the word to tag
            prev_word: String containing the previous word
            tagged_words: Dictionary containing tagged words
            next_word: String containing the next word

        Returns:
            Dictionary containing tagged words with their semantic roles
        """
        for word in tagged_words:
            if self._is_subject(word, prev_word, tagged_words, next_word):
                tagged_words[word]['type'] = Type.SUBJECT.value
            elif self._is_action(word, tagged_words):
                tagged_words[word]['type'] = Type.ACTION.value
            elif self._is_object(word, prev_word, tagged_words):
                tagged_words[word]['type'] = Type.OBJECT.value
            elif self._is_location(word):
                tagged_words[word]['type'] = Type.LOCATION.value
            elif self._is_time(word):
                tagged_words[word]['type'] = Type.TIME.value
            elif self._is_manner(word, tagged_words):
                tagged_words[word]['type'] = Type.MANNER.value
        return tagged_words
    
    def _is_subject(self, word, prev_word, tagged_words, next_word):
        # A pronoun is either a subject or an object, i assume it to be an subject
        if tagged_words[word]['tag'] == Tag.PRONOUN.value and word not in dictionaries.patterns['reflexives']:
            if prev_word and tagged_words[prev_word]['type'] == Type.ACTION.value:
                return False
            return True
        return False
    
    def _is_action(self, word, tagged_words):
        # If the word is a verb (either regular or irregular), it's an action
        if tagged_words[word]['tag'] == Tag.VERB.value:
            if word in dictionaries.irregular_verbs or word in dictionaries.irregular_verbs_list:
                return True
            elif word in dictionaries.verbs:
                return True
        return False
    
    def _is_object(self, word, prev_word, tagged_words):
        # If the word is a noun and the previous word is an action, it's an object
        if tagged_words[word]['tag'] == Tag.NOUN.value or tagged_words[word]['tag'] == Tag.PRONOUN.value:
            if tagged_words[prev_word]['tag'] == Type.ACTION.value:
                return True
            elif any(tagged_words[word]['type'] == Type.SUBJECT.value for word in tagged_words.keys()):
                return True
        return False

    def _is_location(self, prev_word):
        # If the previous word is a preposition indicating location, return True
        if prev_word in set(["in", "on", "near", "under", "above", "behind", "beside", "between", "among", "around", "over", "through", "across", "into", "onto", "toward"]):
            return True
        return False
    
    def _is_time(self, prev_word):
        # If the previous word is a preposition indicating time, return True
        if prev_word in set(["before", "after", "during", "since", "until", "at", "by"]):
            return True
        return False

    def _is_manner(self, word, tagged_words):
        # If the word is an adjective or adverb, it's a manner
        if tagged_words[word]['tag'] == Tag.ADJECTIVE.value or tagged_words[word]['tag'] == Tag.ADVERB.value:
            return True
        return False
    
    def _has_multiple_actions(self, tagged_words):
        verb_count = sum(1 for word in tagged_words if tagged_words[word]['type'] == Type.ACTION.value)
        return verb_count > 1