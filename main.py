import re
import tagging 
import logging
import stemmer
import dictionaries

class NLP:
    def __init__(self):
        """Self made; Regular expressions and comments done by AI"""
        self.stemmer = stemmer.Stemmer()
        self.contractions = {
            "n't": " not",
            "won't": " will not",
            "can't": " can not",
            "en't": "not",
            "'s": " is",
            "'re": " are",
            "'ve": " have",
            "'m": " am",
            "'ll": " will",
            "'d": " would",
        }
        self.contraction_pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in self.contractions.keys()) + r')\b')
        self.tagging = tagging.Tagging(dictionaries.patterns)  # Initialize Tagging with patterns and empty word_endings
        self.tense = tagging.Tense()  # Initialize the Tense analyzer
        self.semantic_role_labelling = tagging.Semantic_Role_Labelling() # Initialize srl

    def _stem(self, word):
        stemmed, ending = self.stemmer.stem(word)
        return stemmed, ending

    def process(self, text):
        """Self made; Example for isinstance-check and comments by AI"""
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        if len(text) == 0:
            raise ValueError("Input must not be empty")
        
        # Split text into sentences using regex
        # This will split on '.', '!', and '?' while preserving the punctuation
        sentences = re.split('([.!?])', text)
        
        # Pair up sentences with their punctuation
        processed_sentences = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i+1] in '.!?':
                full_sentence = sentences[i] + sentences[i+1]
                i += 2
            else:
                full_sentence = sentences[i]
                i += 1
            
            # Skip empty sentences
            if full_sentence.strip():
                processed_sentence = self.preprocess_sentence(full_sentence)
                # Add tense analysis to the processed sentence
                logging.debug(f"Processing sentence: {processed_sentence}")
                tense = self.tense._get_tense(processed_sentence)
                processed_sentence['sentence_tense'] = tense
                processed_sentences.append(processed_sentence)
                return processed_sentences

    def preprocess_sentence(self, sentence):
        """Preprocess a sentence by handling contractions, stemming words, and determining word endings.
        
        Args:
            sentence: String containing the sentence to process
            
        Returns:
            Dictionary containing processed words with their tags and properties
            
        Raises:
            ValueError: If there's an error processing the sentence
            TypeError: If input is not a string

        Self made; Docstrings, contraction handling, regular expressions, punctuation handling, formating and comments by AI
        """
        if not isinstance(sentence, str):
            raise TypeError("Input sentence must be a string")
        if not sentence.strip():
            raise ValueError("Input sentence cannot be empty")
            
        try:
            # Handle contractions
            sentence = self.contraction_pattern.sub(lambda x: self.contractions[x.group()], sentence)
            
            # Split into words
            words = re.findall(r"\b[\w']+\b|[.,?!]", sentence.lower())
            if not words:
                raise ValueError("No valid words found in sentence")
                
            self.word_endings = {}
            stemmed_words = []
            
            # Process each word
            for word in words:
                if not word:
                    continue
                    
                if any(c in word for c in '.,?!'):
                    self.word_endings[word] = ''
                    stemmed_words.append(word)
                else:
                    # Stem all words except special categories
                    if word not in dictionaries.patterns['determiners'] and \
                    word not in dictionaries.patterns['prepositions'] and \
                    word not in dictionaries.patterns['conjunctions'] and \
                    word not in dictionaries.patterns['pronouns'] and \
                    word not in dictionaries.patterns['modals']:
                        stemmed, ending = self._stem(word)
                        logging.debug(f"Stemmed word is '{stemmed}', ending is '{ending}'")
                        if stemmed:
                            self.word_endings[stemmed] = ending  # Store ending for original word
                            stemmed_words.append(stemmed)
                    else:
                        self.word_endings[word] = ''
                        stemmed_words.append(word)
            
            
            if not stemmed_words:
                raise ValueError("No valid words remained after preprocessing")
                
            # Process words in context
            processed_words = self._context(stemmed_words)
            logging.debug(f"Processed words: {processed_words}")

            # New dictionary to store cleaned pairs in
            cleaned_pairs = {}
            for word in list(processed_words.keys()):  # Create a list of keys to iterate over
                self._clean_sentence(word, processed_words)
            for word in processed_words:
                cleaned_pairs[word] = processed_words.get(word, None)
            return processed_words
            
        except Exception as e:
            raise ValueError(f"Error processing text: {str(e)}")

    def _context(self, sentence_list):
        """Process and tag words in context of the sentence.
        
        Args:
            sentence_list: List of stemmed words to process
            
        Returns:
            Dictionary of tagged words with their properties
            
        Raises:
            ValueError: If there's an error processing the words
            TypeError: If input is not a list

        Self made; Docstrings and formating by AI
        """
        if not isinstance(sentence_list, list):
            raise TypeError("Input must be a list of words")
        if not sentence_list:
            raise ValueError("Input list cannot be empty")
            
        try:
            global tagged_words
            tagged_words = {}
            for i, word in enumerate(sentence_list):
                if word is None or not isinstance(word, str):
                    continue
                    
                # Get surrounding words with proper null checks
                global prev_word, next_word, prev_prev_word, next_next_word

                prev_word = sentence_list[i - 1] if i > 0 else None
                next_word = sentence_list[i + 1] if i + 1 < len(sentence_list) else None
                prev_prev_word = sentence_list[i - 2] if i > 1 else None
                next_next_word = sentence_list[i + 2] if i + 2 < len(sentence_list) else None
                
                # Get tag for the word
                tagged_words[word] = {
                    'word': word,
                    'ending': self.word_endings.get(word, ''),
                    'tag': None,
                    'type': None
                }
                try:
                    tag = self.tagging._tag_word_in_context(
                        word, 
                        prev_word, 
                        next_word, 
                        prev_prev_word, 
                        next_next_word, 
                        tagged_words
                    )
                    logging.debug(f"The tag of the word '{word}' is '{tag}'.")
                except Exception as e:
                    logging.warning(f"Error tagging word '{word}': {str(e)}")
                    continue
                
                # Store word information
                logging.debug(f"word_endings are: {self.word_endings}")
                tagged_words[word] = {
                    'word': word,
                    'ending': self.word_endings.get(word, ''),
                    'tag': tag,
                }
            
                
            if not tagged_words:
                raise ValueError("No words were successfully tagged")
                
            return tagged_words
            
        except Exception as e:
            raise ValueError(f"Error processing words in context: {str(e)}")
        
    def _clean_sentence(self, word, tagged_words):
        """Self made"""
        # Remove unnecessary words / stopwords
        if tagged_words[word]['tag'] == tagging.Tag.CONJUNCTION.value or \
            tagged_words[word]['tag'] == tagging.Tag.PREPOSITION.value:
            tagged_words.pop(word)

if __name__ == "__main__":
    """Logging by AI"""
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    nlp = NLP()
    print("Enter text to process:")
    user_input = input()
    results = nlp.process(user_input)
    print("\nProcessed sentences:")
    for i, sentence_dict in enumerate(results, 1):
        print(f"\nSentence {i}:")
        print(f"Tense: {sentence_dict['sentence_tense']}")
        print("Words:", {word: info for word, info in sentence_dict.items() if word != 'sentence_tense'})

import re
import tagging 
import logging
import stemmer
import dictionaries

class NLP:
    def __init__(self):
        """Self made; Regular expressions and comments done by AI"""
        self.stemmer = stemmer.Stemmer()
        self.contractions = {
            "n't": " not",
            "won't": " will not",
            "can't": " can not",
            "en't": "not",
            "'s": " is",
            "'re": " are",
            "'ve": " have",
            "'m": " am",
            "'ll": " will",
            "'d": " would",
        }
        self.contraction_pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in self.contractions.keys()) + r')\b')
        self.tagging = tagging.Tagging(dictionaries.patterns)  # Initialize Tagging with patterns and empty word_endings
        self.tense = tagging.Tense()  # Initialize the Tense analyzer
        self.semantic_role_labelling = tagging.Semantic_Role_Labelling() # Initialize srl

    def _stem(self, word):
        stemmed, ending = self.stemmer.stem(word)
        return stemmed, ending

    def process(self, text):
        """Self made; Example for isinstance-check and comments by AI"""
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        if len(text) == 0:
            raise ValueError("Input must not be empty")
        
        # Split text into sentences using regex
        # This will split on '.', '!', and '?' while preserving the punctuation
        sentences = re.split('([.!?])', text)
        
        # Pair up sentences with their punctuation
        processed_sentences = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i+1] in '.!?':
                full_sentence = sentences[i] + sentences[i+1]
                i += 2
            else:
                full_sentence = sentences[i]
                i += 1
            
            # Skip empty sentences
            if full_sentence.strip():
                processed_sentence = self.preprocess_sentence(full_sentence)
                # Add tense analysis to the processed sentence
                logging.debug(f"Processing sentence: {processed_sentence}")
                tense = self.tense._get_tense(processed_sentence)
                processed_sentence['sentence_tense'] = tense
                processed_sentences.append(processed_sentence)
                return processed_sentences

    def preprocess_sentence(self, sentence):
        """Preprocess a sentence by handling contractions, stemming words, and determining word endings.
        
        Args:
            sentence: String containing the sentence to process
            
        Returns:
            Dictionary containing processed words with their tags and properties
            
        Raises:
            ValueError: If there's an error processing the sentence
            TypeError: If input is not a string

        Self made; Docstrings, contraction handling, regular expressions, punctuation handling, formating and comments by AI
        """
        if not isinstance(sentence, str):
            raise TypeError("Input sentence must be a string")
        if not sentence.strip():
            raise ValueError("Input sentence cannot be empty")
            
        try:
            # Handle contractions
            sentence = self.contraction_pattern.sub(lambda x: self.contractions[x.group()], sentence)
            
            # Split into words
            words = re.findall(r"\b[\w']+\b|[.,?!]", sentence.lower())
            if not words:
                raise ValueError("No valid words found in sentence")
                
            self.word_endings = {}
            stemmed_words = []
            
            # Process each word
            for word in words:
                if not word:
                    continue
                    
                if any(c in word for c in '.,?!'):
                    self.word_endings[word] = ''
                    stemmed_words.append(word)
                else:
                    # Stem all words except special categories
                    if word not in dictionaries.patterns['determiners'] and \
                    word not in dictionaries.patterns['prepositions'] and \
                    word not in dictionaries.patterns['conjunctions'] and \
                    word not in dictionaries.patterns['pronouns'] and \
                    word not in dictionaries.patterns['modals']:
                        stemmed, ending = self._stem(word)
                        logging.debug(f"Stemmed word is '{stemmed}', ending is '{ending}'")
                        if stemmed:
                            self.word_endings[stemmed] = ending  # Store ending for original word
                            stemmed_words.append(stemmed)
                    else:
                        self.word_endings[word] = ''
                        stemmed_words.append(word)
            
            
            if not stemmed_words:
                raise ValueError("No valid words remained after preprocessing")
                
            # Process words in context
            processed_words = self._context(stemmed_words)
            logging.debug(f"Processed words: {processed_words}")

            # New dictionary to store cleaned pairs in
            cleaned_pairs = {}
            for word in list(processed_words.keys()):  # Create a list of keys to iterate over
                self._clean_sentence(word, processed_words)
            for word in processed_words:
                cleaned_pairs[word] = processed_words.get(word, None)
            return processed_words
            
        except Exception as e:
            raise ValueError(f"Error processing text: {str(e)}")

    def _context(self, sentence_list):
        """Process and tag words in context of the sentence.
        
        Args:
            sentence_list: List of stemmed words to process
            
        Returns:
            Dictionary of tagged words with their properties
            
        Raises:
            ValueError: If there's an error processing the words
            TypeError: If input is not a list

        Self made; Docstrings and formating by AI
        """
        if not isinstance(sentence_list, list):
            raise TypeError("Input must be a list of words")
        if not sentence_list:
            raise ValueError("Input list cannot be empty")
            
        try:
            global tagged_words
            tagged_words = {}
            for i, word in enumerate(sentence_list):
                if word is None or not isinstance(word, str):
                    continue
                    
                # Get surrounding words with proper null checks
                global prev_word, next_word, prev_prev_word, next_next_word

                prev_word = sentence_list[i - 1] if i > 0 else None
                next_word = sentence_list[i + 1] if i + 1 < len(sentence_list) else None
                prev_prev_word = sentence_list[i - 2] if i > 1 else None
                next_next_word = sentence_list[i + 2] if i + 2 < len(sentence_list) else None
                
                # Get tag for the word
                tagged_words[word] = {
                    'word': word,
                    'ending': self.word_endings.get(word, ''),
                    'tag': None,
                    'type': None
                }
                try:
                    tag = self.tagging._tag_word_in_context(
                        word, 
                        prev_word, 
                        next_word, 
                        prev_prev_word, 
                        next_next_word, 
                        tagged_words
                    )
                    logging.debug(f"The tag of the word '{word}' is '{tag}'.")
                except Exception as e:
                    logging.warning(f"Error tagging word '{word}': {str(e)}")
                    continue
                
                # Store word information
                logging.debug(f"word_endings are: {self.word_endings}")
                tagged_words[word] = {
                    'word': word,
                    'ending': self.word_endings.get(word, ''),
                    'tag': tag,
                }
            
                
            if not tagged_words:
                raise ValueError("No words were successfully tagged")
                
            return tagged_words
            
        except Exception as e:
            raise ValueError(f"Error processing words in context: {str(e)}")
        
    def _clean_sentence(self, word, tagged_words):
        """Self made"""
        # Remove unnecessary words / stopwords
        if tagged_words[word]['tag'] == tagging.Tag.CONJUNCTION.value or \
            tagged_words[word]['tag'] == tagging.Tag.PREPOSITION.value:
            tagged_words.pop(word)

if __name__ == "__main__":
    """Logging by AI"""
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    nlp = NLP()
    print("Enter text to process:")
    user_input = input()
    results = nlp.process(user_input)
    print("\nProcessed sentences:")
    for i, sentence_dict in enumerate(results, 1):
        print(f"\nSentence {i}:")
        print(f"Tense: {sentence_dict['sentence_tense']}")
        print("Words:", {word: info for word, info in sentence_dict.items() if word != 'sentence_tense'})
