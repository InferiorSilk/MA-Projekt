import dictionaries
from enum import Enum
import logging

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