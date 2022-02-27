# converted to Python (with improvements) - based on this:
# https://github.com/pritam-moodbidri/ghost-game-ai/blob/master/src/AlphaBetaPruning.java

from .helpers import *
import random
import sys

class AI(object):
    
    def __init__(self):
        self.allowedDepth = 2
        self.pInfinity = 99999
        self.nInfinity = -99999
        self.selectedWord = []
        self.currentLettersLength = 0
        
    def getWord(self, currentLetters):
        
        length = len(currentLetters)
        newWords = self.alphaBetaSearch(currentLetters)
        
        # get letter after previous word
        nextLetter = newWords[length]
        return currentLetters + nextLetter
        
    def alphaBetaSearch(self, currentLetters):
        
        self.currentLettersLength = len(currentLetters)
        value = self.maxValue(self.nInfinity, self.pInfinity, currentLetters, self.allowedDepth, self.currentLettersLength)
        
        # randomly select from among best words
        return random.choice(self.selectedWord)
    
    def maxValue(self, alpha, beta, letters, depth, length):
        
        if (trie.has_key(letters[:length]) and length >= 4) or depth == 0:
            return self.heuristic(letters)
            

        value = self.nInfinity
        prevValue = value
        successors = trie.keys(prefix=letters[:length])
        
        for s in successors:
            
            v = self.minValue(alpha, beta, s, depth-1, length+1)
            
            if v > value:
                value = v
                
            if value >= beta:
                return value
            
            if alpha < value:
                alpha = value
            
            if depth == self.allowedDepth and v == value:
                if prevValue < value:
                    selectedWord = ""
                    prevValue = value
                
                self.selectedWord.append(s)
            
        return value
    
    def minValue(self, alpha, beta, letters, depth, length):
    
        if (trie.has_key(letters[:length]) and length >= 4) or depth == 0:
            return self.heuristic(letters)
            
        value = self.pInfinity
        successors = trie.keys(prefix=letters[:length])
        
        for s in successors:
            
            v = self.maxValue(alpha, beta, s, depth-1, length+1)
            
            if v < value:
                value = v
                
            if value <= alpha:
                return value
            
            if beta > value:
                beta = value
            
        return value
        
    def heuristic(self, word):
        
        value = 0
        
        # check whether the selected chracter would form a word
        if trie.has_key(word[:self.currentLettersLength+1]):
            return -20
        
        # since user plays first, computer wins when number of letters in word is odd (so user finishes last)
        if (len(word) % 2) != 0:
            value += 20
        else:
            value -= 10
        
        # chances of extending the game and choosing more words increases when words are lengthy
        
        if (len(word) > 4):
            value += (len(word) - 4)
        
        return value