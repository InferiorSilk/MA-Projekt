class Stemmer(object):
    """Stemmer class for stemming words.

    Attributes:
        b (list): List of characters in the word
        k (int): Index of the current character in the word
        k0 (int): Index of the first character in the word
        j (int): Index of the last character in the word
        _dirty_ending_tracker (str): String containing the stemmed word and the removed suffix
    
    Some of the explanation of the Porter stemmer and terms and keywords by AI, implementation by me. Docstrings by AI.
    """
    def __init__(self):
        self.b = [] 
        self.k = 0  
        self.k0 = 0 
        self.j = 0  
        self._dirty_ending_tracker = ""

    def _cons(self, i):
        """Check if the character at index i is a consonant.
        
        Args:
            i: Index of the character to check
            
        Returns:
            True if the character is a consonant, False otherwise
        """
        if self.b[i] == 'a' or self.b[i] == 'e' or \
           self.b[i] == 'i' or self.b[i] == 'o' or \
           self.b[i] == 'u':
            return False
        if self.b[i] == 'y':
            if i == self.k0:
                return True
            else:
                return (not self._cons(i - 1))
        return True

    def _m(self):
        """Measure the number of consonant sequences between k0 and j.
        
        Returns:
            Number of consonant sequences between k0 and j
        """
        n = 0
        i = self.k0
        while True:
            if i > self.j:
                return n
            if not self._cons(i):
                break
            i += 1
        i += 1
        while True:
            while True:
                if i > self.j:
                    return n
                if self._cons(i):
                    break
                i += 1
            i += 1
            n += 1
            while True:
                if i > self.j:
                    return n
                if not self._cons(i):
                    break
                i += 1
            i += 1

    def _vowelinstem(self):
        """Check if there is a vowel in the stem.
        
        Returns:
            True if there is a vowel in the stem, False otherwise
        """
        for i in range(self.k0, self.j + 1):
            if not self._cons(i):
                return True
        return False

    def _doublec(self, idx):
        """Check if the character at idx and idx-1 are the same consonant.
        
        Args:
            idx: Index of the character to check
            
        Returns:
            True if the characters are the same, False otherwise
        """
        if idx < (self.k0 + 1):
            return False
        if (self.b[idx] != self.b[idx-1]):
            return False
        return self._cons(idx)

    def _cvc(self, i_idx):
        """Check if the sequence at i_idx is consonant-vowel-consonant.
        
        Args:
            i_idx: Index of the character to check
            
        Returns:
            True if the sequence is consonant-vowel-consonant, False otherwise
        """
        if i_idx < (self.k0 + 2) or \
           not self._cons(i_idx) or \
           self._cons(i_idx-1) or \
           not self._cons(i_idx-2):
            return False
        if self.b[i_idx] == 'w' or self.b[i_idx] == 'x' or self.b[i_idx] == 'y':
            return False
        return True

    def _ends(self, s_str):
        """Check if the word ends with the string s_str.
        
        Args:
            s_str: String to check
            
        Returns:
            True if the word ends with the string, False otherwise
        """
        length = len(s_str)
        s_list = list(s_str)
        if length > (self.k - self.k0 + 1):
            return False
        if self.b[self.k-length+1 : self.k+1] != s_list:
            return False
        self.j = self.k - length
        return True

    def _setto(self, s_str):
        """Set the end of the word to s_str.
        
        Args:
            s_str: String to set the end of the word to
        """
        s_list = list(s_str)
        length = len(s_list)
        self.b[self.j+1 : self.k+1] = s_list
        self.k = self.j + length

    def _step1ab(self):
        """Perform step 1a and 1b of the stemming algorithm."""
        if self.b[self.k] == 's':
            if self._ends("sses"):
                self._dirty_ending_tracker = "sses"
                self.k -= 2
            elif self._ends("ies"):
                self._dirty_ending_tracker = "ies"
                self._setto("i")
            elif self.b[self.k-1] != 's':
                self._dirty_ending_tracker = "s"
                self.k -= 1
        
        if self.k >= self.k0: 
            if self._ends("eed"):
                if self._m() > 0:
                    self._dirty_ending_tracker = "eed"
                    self.k -= 1
            elif self._ends("ed") or self._ends("ing"):
                original_suffix = "".join(self.b[self.j+1 : self.k+1])
                
                original_k_val = self.k 
                self.k = self.j 
                contains_vowel = False
                for i_char_idx in range(self.k0, self.j + 1):
                    if not self._cons(i_char_idx):
                        contains_vowel = True
                        break
                self.k = original_k_val

                if contains_vowel:
                    self.k = self.j 
                    self._dirty_ending_tracker = original_suffix
                    if self._ends("at"):
                        self._setto("ate")
                    elif self._ends("bl"):
                        self._setto("ble")
                    elif self._ends("iz"):
                        self._setto("ize")
                    elif self._doublec(self.k):
                        if not (self.b[self.k] == 'l' or self.b[self.k] == 's' or self.b[self.k] == 'z'):
                            self.k -= 1
                    else:
                        original_j_val = self.j 
                        self.j = self.k 
                        if self._m() == 1 and self._cvc(self.k):
                            self.b.append('e')
                            self.k +=1
                        self.j = original_j_val

    def _step1c(self):
        """Perform step 1c of the stemming algorithm."""
        if self._ends("y"):
            contains_vowel = False
            for i_char_idx in range(self.k0, self.j + 1):
                if not self._cons(i_char_idx):
                    contains_vowel = True
                    break
            if contains_vowel:
                self._dirty_ending_tracker = "y"
                self._setto("i")

    def _step2(self):
        """Perform step 2 of the stemming algorithm."""
        s1, s2 = "", ""
        if self.b[self.k] == 'l':
            if self._ends("ational"): s1, s2 = "ational", "ate"
            elif self._ends("tional"): s1, s2 = "tional", "tion"
            else: return
        elif self.b[self.k] == 'i':
            if self._ends("enci"): s1, s2 = "enci", "ence"
            elif self._ends("anci"): s1, s2 = "anci", "ance"
            elif self._ends("izer"): s1, s2 = "izer", "ize"
            elif self._ends("abli"): s1, s2 = "abli", "able" 
            elif self._ends("alli"): s1, s2 = "alli", "al"
            elif self._ends("entli"): s1, s2 = "entli", "ent"
            elif self._ends("eli"): s1, s2 = "eli", "e"
            elif self._ends("ousli"): s1, s2 = "ousli", "ous"
            else: return
        elif self.b[self.k] == 'n':
            if self._ends("ization"): s1, s2 = "ization", "ize"
            elif self._ends("ation"): s1, s2 = "ation", "ate"
            else: return
        elif self.b[self.k] == 'r':
            if self._ends("ator"): s1, s2 = "ator", "ate"
            else: return
        elif self.b[self.k] == 'm':
            if self._ends("alism"): s1, s2 = "alism", "al"
            else: return
        elif self.b[self.k] == 's':
            if self._ends("iveness"): s1, s2 = "iveness", "ive"
            elif self._ends("fulness"): s1, s2 = "fulness", "ful"
            elif self._ends("ousness"): s1, s2 = "ousness", "ous"
            else: return
        elif self.b[self.k] == 't':
            if self._ends("aliti"): s1, s2 = "aliti", "al"
            elif self._ends("iviti"): s1, s2 = "iviti", "ive"
            elif self._ends("biliti"): s1, s2 = "biliti", "ble"
            else: return
        elif self.b[self.k] == 'g':
             if self._ends("logi"): s1, s2 = "logi", "log"
             else: return
        else:
            return
        
        if self._m() > 0:
            self._dirty_ending_tracker = s1
            self._setto(s2)

    def _step3(self):
        """Perform step 3 of the stemming algorithm."""
        s1, s2 = "", ""
        if self.b[self.k] == 'e':
            if self._ends("icate"): s1, s2 = "icate", "ic"
            elif self._ends("ative"): s1, s2 = "ative", "" 
            elif self._ends("alize"): s1, s2 = "alize", "al"
            else: return
        elif self.b[self.k] == 'i':
            if self._ends("iciti"): s1, s2 = "iciti", "ic"
            else: return
        elif self.b[self.k] == 'l':
            if self._ends("ical"): s1, s2 = "ical", "ic"
            elif self._ends("ful"): s1, s2 = "ful", ""
            else: return
        elif self.b[self.k] == 's':
            if self._ends("ness"): s1, s2 = "ness", ""
            else: return
        else:
            return

        if self._m() > 0:
            self._dirty_ending_tracker = s1
            self._setto(s2)

    def _step4(self):
        """Perform step 4 of the stemming algorithm."""
        s1 = ""
        if self.k <= self.k0: return # Word too short for k-1 access

        char_k_minus_1 = self.b[self.k-1] 

        if char_k_minus_1 == 'a':
            if self._ends("al"): s1 = "al"
            else: return
        elif char_k_minus_1 == 'c':
            if self._ends("ance"): s1 = "ance"
            elif self._ends("ence"): s1 = "ence"
            else: return
        elif char_k_minus_1 == 'e':
            if self._ends("er"): s1 = "er"
            else: return
        elif char_k_minus_1 == 'i':
            if self._ends("ic"): s1 = "ic"
            else: return
        elif char_k_minus_1 == 'l':
            if self._ends("able"): s1 = "able"
            elif self._ends("ible"): s1 = "ible"
            else: return
        elif char_k_minus_1 == 'n':
            if self._ends("ant"): s1 = "ant"
            elif self._ends("ement"): s1 = "ement"
            elif self._ends("ment"): s1 = "ment"
            elif self._ends("ent"): s1 = "ent"
            else: return
        elif char_k_minus_1 == 'o':
            if self._ends("ion"): 
                if self.j > self.k0 and (self.b[self.j] == 's' or self.b[self.j] == 't'):
                    s1 = "ion" 
                else: 
                    return 
            elif self._ends("ou"): s1 = "ou"
            else: return
        elif char_k_minus_1 == 's':
            if self._ends("ism"): s1 = "ism"
            else: return
        elif char_k_minus_1 == 't':
            if self._ends("ate"): s1 = "ate"
            elif self._ends("iti"): s1 = "iti"
            else: return
        elif char_k_minus_1 == 'u':
            if self._ends("ous"): s1 = "ous"
            else: return
        elif char_k_minus_1 == 'v':
            if self._ends("ive"): s1 = "ive"
            else: return
        elif char_k_minus_1 == 'z':
            if self._ends("ize"): s1 = "ize"
            else: return
        else:
            return

        if s1 and self._m() > 1:
            self._dirty_ending_tracker = s1
            self._setto("") 

    def _step5a(self):
        """Perform step 5a of the stemming algorithm."""
        if self._ends("e"): 
            m_val = self._m()
            if m_val > 1:
                self._dirty_ending_tracker = "e"
                self.k -=1 
            elif m_val == 1 and not self._cvc(self.j): 
                self._dirty_ending_tracker = "e"
                self.k -=1 

    def _step5b(self):
        """Perform step 5b of the stemming algorithm."""
        if self.b[self.k] == 'l':
            original_j_val = self.j
            self.j = self.k 
            if self._m() > 1 and self._doublec(self.k): 
                self._dirty_ending_tracker = "l" 
                self.k -= 1
            self.j = original_j_val

    def stem(self, word):
        """Stem the given word and return the stem and the removed suffix.
        
        Args:
            word: String to stem
            
        Returns:
            Stemmed word and the removed suffix
        """
        if not word or len(word) <= 2:
            return word, ""
        
        self.b = list(word)
        self.k = len(word) - 1 
        self.k0 = 0
        self._dirty_ending_tracker = ""

        self._step1ab()
        if self.k > self.k0 : 
            self._step1c()
        if self.k > self.k0 :
            self._step2()
        if self.k > self.k0 :
            self._step3()
        if self.k > self.k0 :
            self._step4()
        if self.k > self.k0 :
            self._step5a()
        if self.k > self.k0 :
            self._step5b()
        
        final_stem = "".join(self.b[self.k0:self.k+1])
        
        return final_stem, self._dirty_ending_tracker