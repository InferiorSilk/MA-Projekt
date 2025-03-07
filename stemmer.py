import logging
class Stemmer:
    """Porter stemmer algorithm: Shown by AI, partially executed by me"""
    def __init__(self):
        self.vowels = "aeiou"
        self.consonants = "bcdfghjklmnpqrstvwxyz"

    def is_vowel(self, letter, prev_letter=None, next_letter=None):
        vowels = set('aeiou')
        if letter in vowels:
            return True

        # Handle 'y' as a vowel in certain contexts
        if letter == 'y':
            if prev_letter and prev_letter not in vowels:
                return True
            if next_letter and next_letter in vowels:
                return True

        # Handle diphthongs
        if prev_letter and next_letter:
            if (prev_letter + letter) in ['oi', 'ou', 'oy']:
                return True
            if (letter + next_letter) in ['ai', 'au', 'ay', 'ei', 'eu', 'ey', 'ie', 'oi', 'ou', 'oy']:
                return True

        return False

    def measure(self, word):
        """Calculate the number of syllables in a word."""
        m = 0
        state = 0  # 0 = expecting vowel, 1 = expecting consonant
        
        for i in range(len(word)):
            is_v = self.is_vowel(word[i], 
                               word[i-1] if i > 0 else None,
                               word[i+1] if i < len(word)-1 else None)
            
            if state == 0 and is_v:  # Found vowel when expecting one
                state = 1
            elif state == 1 and not is_v:  # Found consonant when expecting one
                state = 0
                m += 1
                
        return m

    def stem(self, word):
        """Apply the Porter Stemming algorithm and track removed endings."""
        if len(word) <= 3:  # Don't stem very short words
            return word, ""
            
        # Don't stem if the word contains numbers
        if any(c.isdigit() for c in word):
            return word, ""

        original = word
        ending = ""

        # Step 1a - Handle plurals and verb forms ending in -s/-es
        if word.endswith("sses"):  # e.g., "passes" -> "pass"
            ending = "sses"
            word = word[:-2]
        elif word.endswith("ies"):  # e.g., "flies" -> "fly"
            if len(word) > 4:
                ending = "ies"
                word = word[:-3] + "y"
            else:  # Keep short words unchanged
                ending = ""
        elif word.endswith("ss"):  # e.g., "pass" -> "pass"
            ending = ""  # Don't remove ending for double s
        elif word.endswith("es"):  # e.g., "watches" -> "watch"
            if len(word) > 4:
                ending = "es"
                word = word[:-2]
        elif word.endswith("s"):  # e.g., "works", "makes" -> "work", "make"
            # Don't stem certain words ending in 's'
            if word in {'this', 'has', 'his', 'is', 'was', 'us', 'thus', 'gas', 'lens'}:
                ending = ""
            elif len(word) > 3:  # Only stem if word is long enough
                # Check if it's a verb form or regular plural
                prev_char = word[-2]
                if prev_char in self.vowels or prev_char in 'rkldtmnpv':  # Common verb/noun endings
                    # Don't stem if removing 's' would create a too-short word
                    if len(word[:-1]) > 2:
                        ending = "s"
                        word = word[:-1]

        # Step 1b - More conservative approach
        if word.endswith("eed"):
            if self.measure(word[:-3]) > 0 and len(word) > 4:
                ending = "eed"
                word = word[:-1]
        elif word.endswith("ed"):
            if any(self.is_vowel(char, None, None) for char in word[:-2]):
                temp = word[:-2]
                if len(temp) > 2:  # Ensure we don't create too short words
                    ending = "ed"
                    word = temp
                    word = self._step1b_helper(word)
        elif word.endswith("ing"):
            if any(self.is_vowel(char, word[i-1] if i > 0 else None, word[i+1] if i < len(word)-1 else None) for i, char in enumerate(word[:-3])):
                temp = word[:-3]
                if len(temp) > 2:  # Ensure we don't create too short words
                    ending = "ing"
                    word = temp
                    word = self._step1b_helper(word)

        # Step 2 - More conservative y handling
        if word.endswith("y"):
            if len(word) > 2 and word[-2] not in self.vowels:
                ending = "y"
                word = word[:-1] + "i"

        # Handle double consonants more carefully
        if len(word) > 3 and word[-1] == word[-2] and word[-1] in self.consonants:
            if word[-1] not in 'lsz':  # Keep double l, s, z
                word = word[:-1]

        # Step 3 - Only apply if word is long enough
        if len(word) > 5:
            if word.endswith("ational"):
                if self.measure(word[:-7]) > 0:
                    ending = "ational"
                    word = word[:-7] + "ate"
            elif word.endswith("tional"):
                if self.measure(word[:-6]) > 0:
                    ending = "tional"
                    word = word[:-6] + "ate"
            elif word.endswith("alize"):
                if self.measure(word[:-5]) > 0:
                    ending = "alize"
                    word = word[:-5] + "al"
            elif word.endswith("icate"):
                if self.measure(word[:-5]) > 0:
                    ending = "icate"
                    word = word[:-5] + "ic"
            elif word.endswith("ative"):
                if self.measure(word[:-5]) > 1:
                    ending = "ative"
                    word = word[:-5]

        # Step 4 - More conservative suffix removal
        if len(word) > 4:
            if word.endswith("ful"):
                if self.measure(word[:-3]) > 1:
                    ending = "ful"
                    word = word[:-3]
            elif word.endswith("ness"):
                if self.measure(word[:-4]) > 1:
                    ending = "ness"
                    word = word[:-4]

        return word, ending

    def _step1b_helper(self, word):
        """Helper function for step 1b with more conservative rules."""
        if len(word) < 3:  # Don't modify very short words
            return word

        # Add 'e' in specific cases
        if word.endswith("at") or word.endswith("bl") or word.endswith("iz"):
            return word + "e"

        # Handle double consonants more carefully
        if len(word) > 2 and word[-1] == word[-2] and word[-1] in self.consonants:
            if word[-1] not in 'lsz':  # Keep double l, s, z
                return word[:-1]

        # Add 'e' for short words with specific pattern
        if self.measure(word) == 1 and self._cvc(word):
            return word + "e"

        # Handle 'ing' ending
        if word.endswith("ing"):
            if any(self.is_vowel(char, word[i-1] if i > 0 else None, word[i+1] if i < len(word)-1 else None) for i, char in enumerate(word[:-3])):
                temp = word[:-3]
                if len(temp) > 2:
                    if temp.endswith("e") and self.measure(temp) > 0:
                        temp = temp[:-1]
                    elif self.measure(temp) > 0 and self._cvc(temp):
                        temp += "e"
                return temp
        elif word.endswith("y") and len(word) > 2 and word[-2] not in self.vowels:
            return word[:-1] + "i"
        
        return word


    def _cvc(self, word):
        """Check if the word is a consonant-vowel-consonant (CVC) pattern."""
        if len(word) < 3:
            return False
        if (self.is_vowel(word[-1]) and not self.is_vowel(word[-2]) and
                not self.is_vowel(word[-3])):
            return True
        return False
