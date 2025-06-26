import re
import json
import tagging 
import logging
import stemmer
import dictionaries
import viterbi

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
        # self.tense = tagging.Tense()  # Initialize the Tense analyzer. NOT USED ANYMORE
        self.semantic_role_labelling = tagging.Semantic_Role_Labelling() # Initialize srl

    def _stem(self, word):
        stemmed, ending = self.stemmer.stem(word)
        return stemmed, ending

    def process(self, text):
        """Main processing function to handle text input, split it into sentences, and preprocess each sentence.
        Args:
            text: String containing the text to process
        
        Returns:
            processed_sentences: List of dictionaries containing processed sentences with their words, tags, and properties

        Raises:
            ValueError: If the input is empty
            TypeError: If input is not a string or is empty

        Self made; Example for isinstance-check and comments by AI
        """
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        if len(text) == 0:
            raise ValueError("Input must not be empty")
        
        text = text.replace('\n', ' ')
        
        # This will split on delimiters while preserving them
        sentences = re.split('([.!?:;-])', text)
        
        processed_sentences = []
        
        # The re.split with a capturing group creates a list of [text, delim, text, delim, ...].
        # This loop correctly pairs the text parts with their delimiters.
        sentence_parts = sentences[::2]
        delimiters = sentences[1::2]

        for i, part in enumerate(sentence_parts):
            delimiter = delimiters[i] if i < len(delimiters) else ""
            full_sentence = (part + delimiter).strip()

            # Skip empty sentences that might result from multiple delimiters
            if full_sentence:
                processed_sentence = self.preprocess_sentence(full_sentence)
                processed_sentences.append(processed_sentence)
                
        return processed_sentences



    def preprocess_sentence(self, sentence):
        """Preprocess a sentence by handling contractions, stemming words, and determining word endings.
        
        Args:
            sentence: String containing the sentence to process
            
        Returns:
            Dictionary containing processed words with their tags and properties
            
        Raises:
            ValueError: If there was an error processing the sentence
            TypeError: If input is not a string

        Self made; Docstrings, contraction handling, regular expressions, punctuation handling, formating and splitting sentences by AI
        """
        if not isinstance(sentence, str):
            raise TypeError("Input sentence must be a string")
        if not sentence.strip():
            raise ValueError("Input sentence cannot be empty")
            
        try:
            # Handle contractions
            sentence = self.contraction_pattern.sub(lambda x: self.contractions[x.group()], sentence)
            
            # Split into words
            words = re.findall(r"\b[\w']+\b|[.,?!:;-]", sentence.lower())
            if not words:
                raise ValueError("No valid words found in sentence")
                
            self.word_endings = {}
            stemmed_words = []
            
            # Process each word
            for word in words:
                # Check for
                if not word:
                    continue
                    
                if any(c in word for c in '.,?!:;-'):
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
                            self.word_endings[stemmed] = ending  # Store ending for original word to use in tagging
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
                    
                # Get surrounding words with null checks
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
                    # Get tag for the word
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
    logging.basicConfig(level=logging.CRITICAL, filename="log.txt", filemode="w", format='%(asctime)s - %(levelname)s - %(message)s')
    model_input = input("Which version?\nRule-based (rb)\nHidden Markov Model (hmm)\n")
    if model_input.lower() == "rb":
        nlp = NLP()
        print("Enter text to process(press \end to finish):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break

            if line.strip().lower() == "\\end":
                break

            lines.append(line) 
        user_input = "\n".join(lines)
        logging.critical("Started analysing - Rule-based\nInput:\n" + user_input)
        results = nlp.process(user_input)
        logging.critical("Finished analysing - Rule-based")
        with open("rb_raw.txt", "w") as f:
            json.dump(results, f)
        print("\nProcessed sentences:")
        for i, sentence_dict in enumerate(results, 1):
            print(f"\nSentence {i}:")
            print("Words:", {word: info for word, info in sentence_dict.items()})
    elif model_input.lower() == "hmm":
        viterbi = viterbi.Viterbi()
        print("Enter text to process (press \\end to finish):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break

            if line.strip().lower() == "\\end":
                break

            lines.append(line) 
        user_input = "\n".join(lines)
        logging.critical("Started analysing - Viterbi\nInput:\n" + user_input)
        results = viterbi.process(user_input)
        logging.critical("Finished analysing")
        with open("viterbi_raw.txt", "w") as f:
            json.dump(results, f)
        print(results)
    else:
        print("Invalid input")