import os
import discord
from discord.ext import commands

import math, time
from datetime import datetime

import pymongo

import asyncio
import random

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
blackjackGameCol = myDB["BLACKJACK_GAME"]
blackjackUserCol = myDB["BLACKJACK_USER"]

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
    
    def to_dict(self):
        return {
            "rank": self.rank,
            "suit": self.suit,
            "value": cardRanks[self.rank]
        }

class Deck:
    def __init__(self):
        self.stack = []
        self.total = 0
        for suit in cardSuits:
            for rank in cardRanks:
                self.stack.append(Card(rank,suit))
                self.total += 1

    def draw(self):
        if self.total <= 0:
            return -1
        
        num = random.randint(0,self.total-1)
        self.total -= 1

        card = self.stack[num]
        self.stack.pop(num)

        return card

    def shuffle(self):
        random.shuffle(self.stack)

def evaluate_hand(hand):
    handValue = 0

    for card in hand:
        cardRank = int(card["value"])
        if(cardRank == 1):
            if(handValue + 11 <= 21):
                cardRank = 11
            else:
                cardRank = 1
        handValue += cardRank

    return handValue

def draw_card(playDeck):
    deck = random.choice(playDeck)
    card = deck.draw()
    if(card == -1):
        playDeck.remove(deck)
        return draw_card(playDeck)
    return card

def print_hand(hand):
    handStr = "Your current hand:\n"
    for card in hand:
        handStr += card["rank"] + " of " + card["suit"] + "\n"
    handStr += "\nTotal value = " + str(evaluate_hand(hand))
    return handStr

def print_house_hand(hand, numHidden):
    handStr = "House's current hand:\n"
    value = 0
    for card in hand:
        if numHidden > 0:
            handStr += "Hidden card\n"
            numHidden -= 1
            continue
        handStr += card["rank"] + " of " + card["suit"] + "\n"
        value += evaluate_hand([card])
    handStr += "\nTotal value = " + str(value)
    return handStr

async def update_wallet(ctx: discord.ApplicationContext, amount: int, remove: bool):
    #Check wallet
    userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
    if(userCheck is None): 
        await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
        return -1

    if remove:
        if(userCheck["coins"] < amount): 
            await ctx.respond("You seem to be too poor right now. Maybe apply for a small loan of a million <:beets:1245409413284499587>?", ephemeral=True)
            return -1
            
        #Update wallet before game
        removeCoins = 0 - amount
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(removeCoins), 'coins_bet': int(amount)}}
        usersCol.update_one(myQuery, newValues)

    else:
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(amount), 'earned_bet': int(amount), 'total_earned': int(amount)}}
        usersCol.update_one(myQuery, newValues)

class Blackjack(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    blackjack = discord.SlashCommandGroup("blackjack", "Blackjack related commands.")

    @blackjack.command(name="start", description="Start a game of Blackjack")
    @discord.option("wait_time", description="Time to wait before starting the game", required=False, default=30)
    async def start(self, ctx: discord.ApplicationContext, wait_time: int):
        # Check if there is already a game running in the server
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
        
        end_betting_time = wait_time + math.floor(time.time())
        
        embed = discord.Embed(title="Blackjack starting!",
                      description="<@" + str(ctx.author.id) + "> initiated a game of Blackjack!\n\
                      Betting will end in <t:" + str(end_betting_time) + ":R>!\
                      \nDo `/blackjack bet` to join.",
                      colour=0x009900,
                      timestamp=datetime.now())
        
        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
        
        # Waiting for players to join
        await asyncio.sleep(wait_time)

        # Check if there are enough players to start the game
        if(len(self.queue) < 1):
            await ctx.respond("[Blackjack] Not enough players to start a game! Aborting...")
            myQuery = {"guild_id": ctx.guild.id}
            newValues = {'$set': {'running': False}}
            blackjackGameCol.update_one(myQuery, newValues)
            return
        
        #INITIAL DRAW
        playDeck = []
        for i in range(6 + len(self.queue)%4):
            # playDeck.append(pc.Deck())
            playDeck.append(Deck())
            playDeck[i].shuffle()

        houseHand = []

        # Draw house hand
        for i in range(2):
            houseHand.append(draw_card(playDeck).to_dict())

        # Draw player hands
        playerHand = []
        for player in self.queue:
            playerHand.clear()

            for i in range(2):
                playerHand.append(draw_card(playDeck).to_dict())

            blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                        {"$set": {"hand": playerHand}})

        # PLAYER'S TURN (BY SEQUENCE OF JOINING)
        while len(self.queue) > 0:
            player = self.queue.pop()
            blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                        {"$set": {"playing": True}})
            
            # Check if player has blackjack
            playerHand = blackjackUserCol.find_one({"member_id": player, "guild_id": ctx.guild.id},{"_id": 0, "hand": 1})["hand"]

            if evaluate_hand(playerHand) == 21:
                await ctx.respond("[Blackjack] <@" + str(player) + "> has a Blackjack! ", ephemeral=True)
                blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                        {"$set": {"playing": False}})
                continue
            
            timeout = 10
            end_action_time = timeout + math.floor(time.time())
            playerHandDesc = print_hand(playerHand)
            houseHandDesc = print_house_hand(houseHand,1)
            
            embed = discord.Embed(title="[Blackjack] New player's turn!",
                                  description="Now playing - <@" + str(ctx.author.id) + ">\n\n" + 
                                  playerHandDesc + "\n\n" + houseHandDesc + 
                                  "\n\nType your action: `hit`, `stand`, `double`, or `split`.\n\n\
                                  You have <t:" + str(end_action_time) + ":R> to make your move!",
                                  colour=0x009900,
                                  timestamp=datetime.now())

            await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
            
            def check(m):
                return m.author.id == player and m.channel.id == ctx.channel.id

            # PLAYER ACTIONS
            flag = 0
            while flag != 1:
                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=timeout)
                    message = msg.content.strip().lower()
                    # HIT
                    if message == "hit" or message == "h":
                        playerHand.append(draw_card(playDeck).to_dict())
                        
                        # PRINT NEW HAND
                        end_action_time = timeout + math.floor(time.time())
                        playerHandDesc = print_hand(playerHand)
                        houseHandDesc = print_house_hand(houseHand,1)
                        embed = discord.Embed(title="[Blackjack] Player used HIT!",
                                              description="Now playing - <@" + str(ctx.author.id) + ">\n\n" + 
                                              playerHandDesc + "\n\n" + houseHandDesc + 
                                              "\n\nType your action: `hit`, `stand`, `double`, or `split`.\n\n\
                                              You have <t:" + str(end_action_time) + ":R> to make your move!",
                                              colour=0x009900,
                                              timestamp=datetime.now())
                        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
                    
                    # STAND
                    elif message == "stand" or message == "st":
                        flag = 1
                        blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                                    {"$set": {"playing": False}})

                    # DOUBLE    
                    elif message == "double" or message == "d":
                        #Change bet to double if possible
                        amount = blackjackUserCol.find_one({"member_id": player, "guild_id": ctx.guild.id},{"_id": 0, "bet": 1})["bet"]
                        if await update_wallet(ctx, amount, True) == -1:
                            await ctx.respond("You cannot double your bet! You don't have enough <:beets:1245409413284499587>!", ephemeral=True)
                            continue
                        
                        blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id},
                                                    {"$set": {"bet": amount*2}})

                        #Draw a card
                        playerHand.append(draw_card(playDeck).to_dict())
                        
                        playerHandDesc = print_hand(playerHand)
                        houseHandDesc = print_house_hand(houseHand,1)
                        embed = discord.Embed(title="[Blackjack] Player used DOUBLE!",
                                              description="Player - <@" + str(ctx.author.id) + ">\n\n" + 
                                              playerHandDesc + "\n\n" + houseHandDesc,
                                              colour=0x009900,
                                              timestamp=datetime.now())
                        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
                        
                        flag = 1
                        blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                                    {"$set": {"playing": False}})

                    # SPLIT    
                    elif message == "split" or message == "sp":
                        #WHAT TO DO WHEN SPLIT
                        print("SPLIT")
                    else:
                        await ctx.respond("Invalid action! Please type `hit`, `stand`, `double`, or `split`.", ephemeral=True)
                        continue
                    
                except asyncio.TimeoutError:
                    await ctx.respond("[Blackjack] <@" + str(player) + "> took too long to respond! Standing their hand...")
                    blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                            {"$set": {"playing": False}})
                    flag = 1
                
                playerScore = evaluate_hand(playerHand)
                if playerScore >= 21:
                    flag = 1
                    blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id},
                                                {"$set": {"playing": False}})
                    if(playerScore == 21):
                        await ctx.respond("[Blackjack] <@" + str(player) + "> has a Blackjack! Advancing to next player...")
                        
                    elif(playerScore > 21):
                        await ctx.respond("[Blackjack] <@" + str(player) + "> busted! Advancing to next player...")


            # Update final hand to database
            myQuery= {"member_id": player, "guild_id": ctx.guild.id}
            newValues = {'$set': {'hand': playerHand}}
            blackjackUserCol.update_one(myQuery, newValues)

        embed = discord.Embed(title="[Blackjack] House's turn!",
                              description="Revealing house's hand...\n\n" + print_house_hand(houseHand, 0),
                              colour=0x009900,
                              timestamp=datetime.now())
        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())

        # HOUSE TURN
        while evaluate_hand(houseHand) < 17:
            await asyncio.sleep(3)
            houseHand.append(draw_card(playDeck).to_dict())
            embed = discord.Embed(title="[Blackjack] House's turn!",
                                  description="Drawing cards...\n\n" + print_house_hand(houseHand, 0),
                                  colour=0x009900,
                                  timestamp=datetime.now())
            await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
            
        # CHECK WINNERS
        houseValue = evaluate_hand(houseHand)
        for player in blackjackUserCol.find({"guild_id": ctx.guild.id},{"_id": 0, "member_id": 1, "hand": 1, "bet": 1}):
            playerHand = player["hand"]
            playerValue = evaluate_hand(playerHand)
            bet = player["bet"]
            if playerValue > 21:
                await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + "> busted! You lost " + str(bet) + "<:beets:1245409413284499587>!")
            elif houseValue > 21 or playerValue > houseValue:
                if playerValue == 21:
                    await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + "> has a Blackjack! You win " + str(bet*2.5) + "<:beets:1245409413284499587>!")
                    await update_wallet(ctx, math.floor(bet*2.5), False)
                await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + "> wins " + str(bet*2) + "<:beets:1245409413284499587>!")
                await update_wallet(ctx, math.floor(bet*2), False)
            elif playerValue == houseValue:
                await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + "> ties with the house! You get back your " + str(bet) + "<:beets:1245409413284499587>!")
                await update_wallet(ctx, bet, False)
            else:
                await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + "> loses " + str(bet) + "<:beets:1245409413284499587>!")

        # Clean up from database
        myQuery = {"guild_id": ctx.guild.id}
        newValues = {'$set': {'running': False}}
        blackjackGameCol.update_one(myQuery, newValues)
        blackjackUserCol.delete_many(myQuery)


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
        
        if await update_wallet(ctx, amount, True) == -1:
            return
    
        # #Check wallet
        # userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        # if(userCheck is None): 
        #     await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
        #     return

        # if(userCheck["coins"] < amount): 
        #     await ctx.respond("You seem to be too poor right now. Maybe apply for a small loan of a million <:beets:1245409413284499587>?", ephemeral=True)
        #     return
        
        # #Update wallet before game
        # removeCoins = 0 - amount
        # myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        # newValues = {'$inc': {'coins': int(removeCoins), 'coins_bet': int(amount)}}
        # usersCol.update_one(myQuery, newValues)

        newPlayer = {
            "member_id": ctx.author.id,
            "guild_id": ctx.guild.id,
            "bet": amount,
            "playing": False,
            "hand": []
        }
        blackjackUserCol.insert_one(newPlayer)
        self.queue.append(ctx.author.id)

        await ctx.respond("[Blackjack] <@" + str(ctx.author.id) + "> entered the table with a **" + str(amount) + "**<:beets:1245409413284499587> bet!")

    @blackjack.command(name="reset", description="Reset Blackjack DB.")
    async def reset(self, ctx: discord.ApplicationContext):
        blackjackGameCol.delete_many({})
        blackjackUserCol.delete_many({})
        await ctx.respond("Blackjack database reset!")

def setup(bot):
    bot.add_cog(Blackjack(bot))