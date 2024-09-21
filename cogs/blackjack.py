import os
import discord
from discord.ext import commands

import time, math
from datetime import datetime

import pymongo

import asyncio
import random
import playing_cards as pc

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
blackjackGameCol = myDB[db["BLACKJACK_GAME"]]
blackjackUserCol = myDB[db["BLACKJACK_USER"]]

def evaluate_hand(hand):
    handValue = 0

    for card in hand:
        cardRank = card.get_value()
        if(cardRank == 1):
            if(handValue + 11 <= 21):
                cardRank = 11
            else:
                cardRank = 1
        handValue += cardRank

    return handValue

class Blackjack(commands.cog):

    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    blackjack = discord.SlashCommandGroup("blackjack", "Blackjack related commands.")

    @blackjack.command(name="start", description="Start a game of Blackjack")
    @discord.option("wait_time", description="Time to wait before starting the game", required=False, default=30)
    async def start(self, ctx: discord.ApplicationContext, wait_time: int):
        blackjackGameCheck = blackjackGameCol.find_one({"guild_id": ctx.guild.id},{"_id": 0, "running": 1})
        if(blackjackGameCheck is None):
            newGame = {
                "guild_id": ctx.guild.id,
                "author_id": ctx.author.id,
                "running": True,
                "rolling": False
            }
            blackjackGameCol.insert_one(newGame)
            self.queue.clear()

        elif(blackjackGameCheck is not None and blackjackGameCheck["running"] == True):
            await ctx.respond("There is already a game running in this server!", ephemeral=True)
            return
    
        if(wait_time < 0):
            await ctx.respond("Blud must be using a time machine...", ephemeral=True)
            return
        
        if(wait_time > 60):
            await ctx.respond("Max waiting time is limited to 60 seconds!", ephemeral=True)
            return
        
        if(wait_time < 10):
            await ctx.respond("Min waiting time is 10 seconds!", ephemeral=True)
            return
        
        # Waiting for players to join
        await asyncio.sleep(wait_time)

        # Check if there are enough players to start the game
        if(len(self.queue) < 1):
            await ctx.respond("Not enough players to start the game! Aborting...", ephemeral=True)
            return
        
        #INITIAL DRAW
        playDeck = []
        for i in range(6 + len(self.queue)%4):
            playDeck.append(pc.Deck())
            playDeck[i].shuffle()

        houseHand = []

        # Draw house hand
        while len(houseHand) < 2:
            deck = random.choice(playDeck)
            card = deck.draw()
            houseHand.append(card)

        # Draw player hands
        for player in self.queue:
            playerHand = []

            while len(playerHand) < 2:
                deck = random.choice(playDeck)
                card = deck.draw()
                if(card == -1):
                    playDeck.remove(deck)
                    continue
                playerHand.append(card)

            blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                        {"$set": {"hand": playerHand}})

        # PLAYERS TURN (BY SEQUENCE OF JOINING)
        while len(self.queue) > 0:
            player = self.queue.pop()
            blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                        {"$set": {"playing": True}})
            
            # Check if player has blackjack
            playerHand = blackjackUserCol.find_one({"member_id": player, "guild_id": ctx.guild.id},{"_id": 0, "hand": 1})
            if evaluate_hand(playerHand) == 21:
                await ctx.respond("[Blackjack] <@" + str(player) + "> has a Blackjack! ", ephemeral=True)
                blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                        {"$set": {"playing": False}})
                continue
            
            await ctx.respond("[Blackjack] <@" + str(player) + "> it's your turn! Type (................) to continue!", ephemeral=True)
            
        


    @blackjack.command(name="bet", description="Participate in a game of Blackjack.")
    @discord.option("amount", description="Your bet amount against the house.", required=True)
    async def bet(self, ctx: discord.ApplicationContext, amount: int):
        if(amount <= 0):
            await ctx.respond("<@" + str(ctx.author.id) + "Buddy, ya ain't slick.")
            try:
                await ctx.author.edit(nick=ctx.author.display_name + " 🤡", reason="Tried to cheat Jeraptha")
            except:
                pass
            return
    
        #Check wallet
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(userCheck is None): 
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        if(userCheck["coins"] < amount): 
            await ctx.respond("You seem to be too poor right now. Maybe apply for a small loan of a million <:beets:1245409413284499587>?", ephemeral=True)
            return
        
        #Update wallet before game
        removeCoins = 0 - amount
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(removeCoins), 'coins_bet': int(amount)}}
        usersCol.update_one(myQuery, newValues)

        newPlayer = {
            "member_id": ctx.author.id,
            "guild_id": ctx.guild.id,
            "bet": amount,
            "playing": False,
            "hand": []
        }
        blackjackUserCol.insert_one(newPlayer)
        self.queue.append(ctx.author.id)

        await ctx.respond("[Blackjack] <@" + str(ctx.author.id) + "> entered the table with a " + str(amount) + "**<:beets:1245409413284499587> bet!")

        
    
def setup(bot):
    bot.add_cog(Blackjack(bot))

# #INITIAL DRAW
# playDeck = pc.Deck()
# playDeck.shuffle

# houseHand = []
# playerHand = []

# for i in range(2):
#     houseHand.append(playDeck.draw())
#     playerHand.append(playDeck.draw())

# print("House hand:")
# for card in houseHand:
#     print(card.get_rank() + " of " + card.get_suit())

# print("Player hand:")
# for card in playerHand:
#     print(card.get_rank() + " of " + card.get_suit())

# houseHandValue = evaluate_hand(houseHand)
# print("House hand value: " + str(houseHandValue))
# playerHandValue = evaluate_hand(playerHand)
# print("Player hand value: " + str(playerHandValue))



