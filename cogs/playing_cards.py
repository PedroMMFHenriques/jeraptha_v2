import random
from enum import Enum

cardSuits = ["♦︎", "♣︎", "♥︎", "♠︎"]
cardRanks = {
    "A": 1, 
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10
}

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def get_rank(self):
        return self.rank
    
    def get_suit(self):
        return self.suit
    
    def get_value(self):
        return cardRanks[self.rank]

class Deck:
    def __init__(self):
        self.stack = []
        self.total = 0
        for suit in cardSuits:
            for rank in cardRanks:
                self.stack.append(Card(rank,suit))
                self.total += 1

    def draw(self):
        num = random.randint(0,self.total-1)
        self.total -= 1
        if self.total < 0:
            return -1

        card = self.stack[num]
        self.stack.pop(num)

        return card

    def shuffle(self):
        random.shuffle(self.stack)
