import random

cardSuits = ["♦︎", "♣︎", "♥︎", "♠︎"]
cardRanks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def get_rank(self):
        return self.rank
    
    def get_suit(self):
        return self.suit

#standard deck of cards
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
        card = self.stack[num]
        self.stack.pop(num)

        return card

    def shuffle(self):
        random.shuffle(self.stack)