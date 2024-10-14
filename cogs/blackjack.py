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

adminRole = global_json["ROLES"]["ADMIN_ROLE"]

SPLIT_TEST = False

playerColours = [0xfc0377, 0x03fceb, 0xe7fc03, 0xfc7703]

cardSuits = [":diamond_suit:", ":club_suit:", ":heart_suit:", ":spade_suit:"]

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

cardRanksEmoji = {
    "A": ":a:", 
    "2": ":number_2:",
    "3": ":number_3:",
    "4": ":number_4:",
    "5": ":number_5:",
    "6": ":number_6:",
    "7": ":number_7:",
    "8": ":number_8:",
    "9": ":number_9:",
    "10": ":number_10:",
    "J": ":jack_o_lantern:",
    "Q": ":princess:",
    "K": ":crown:"
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

    sortedHand = sorted(hand, key=lambda x: x["value"], reverse=True)
    for card in sortedHand:
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
    value = evaluate_hand(hand)
    for card in hand:
        handStr += cardRanksEmoji[card["rank"]] + " of " + card["suit"] + "\n"
    handStr += "\nTotal value = **" + str(value) + "**"
    return handStr

def print_house_hand(hand, numHidden):
    handStr = "House's current hand:\n"
    value = 0
    
    if numHidden > 0:
        for card in hand:
            if numHidden > 0:
                handStr += "[redacted]\n"
                numHidden -= 1
                continue
            handStr += cardRanksEmoji[card["rank"]] + " of " + card["suit"] + "\n"
            value += evaluate_hand([card])
    else:
        for card in hand:
            handStr += cardRanksEmoji[card["rank"]] + " of " + card["suit"] + "\n"
        value = evaluate_hand(hand)
    handStr += "\nTotal value = **" + str(value) + "**"
    return handStr

async def update_wallet(ctx: discord.ApplicationContext, memberId, amount: int, remove: bool):
    #Check wallet
    userCheck = usersCol.find_one({"member_id": memberId, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
    if(userCheck is None): 
        await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
        return -1

    #When removing coins from wallet
    if remove:
        if(userCheck["coins"] < amount): 
            await ctx.respond("You seem to be too poor right now. Maybe apply for a small loan of a million <:beets:1245409413284499587>?", ephemeral=True)
            return -1
            
        removeCoins = 0 - amount
        myQuery= {"member_id": memberId, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(removeCoins), 'coins_bet': int(amount)}}
        usersCol.update_one(myQuery, newValues)

    # When adding coins to wallet
    else:
        myQuery= {"member_id": memberId, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(amount), 'earned_bet': int(amount), 'total_earned': int(amount)}}
        usersCol.update_one(myQuery, newValues)

async def calculate_player_reward(ctx: discord.ApplicationContext, player, houseValue):
    hand = player["hand"]
    bet = player["bet"]
    
    playerValue = evaluate_hand(hand)
            
    if playerValue > 21:
        await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + 
                          "> busted! You lost " + str(bet) + 
                          "<:beets:1245409413284499587>!")
                
    elif houseValue > 21 or playerValue > houseValue:
        if playerValue == 21:
            await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + 
                              "> had a **Blackjack**! You win **" + str(math.floor(bet*2.5)) + 
                              "**<:beets:1245409413284499587>!")
            await update_wallet(ctx, player["member_id"], math.floor(bet*2.5), False)
        else:
            await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + 
                            "> won **" + str(math.floor(bet*2)) + 
                            "**<:beets:1245409413284499587>!")
            await update_wallet(ctx, player["member_id"], math.floor(bet*2), False)
                
    elif playerValue == houseValue:
        await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + 
                          "> ties with the house! You got back your " + 
                          str(bet) + "<:beets:1245409413284499587>!")
        await update_wallet(ctx, player["member_id"], bet, False)
                
    else:
        await ctx.respond("[Blackjack] <@" + str(player["member_id"]) + 
                          "> loses " + str(bet) + "<:beets:1245409413284499587>!")

class Blackjack(commands.Cog):
    """
    Start a table of Blackjack to play and place your bets.
    """

    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    blackjack = discord.SlashCommandGroup("blackjack", "Blackjack related commands.")

    @blackjack.command(name="start", description="Start a game of Blackjack")
    @discord.option("wait_time", description="Time to wait before starting the game (10-120)", required=False, default=30)
    async def start(self, ctx: discord.ApplicationContext, wait_time: int):
        # Check if there is already a game running in the server
        blackjackGameCheck = blackjackGameCol.find_one({"guild_id": ctx.guild.id},{"_id": 0, "running": 1, "rolling": 1})
        if(blackjackGameCheck is None):
            newGame = {
                "guild_id": ctx.guild.id,
                "running": True,
                "rolling": False
            }
            blackjackGameCol.insert_one(newGame)
            self.queue.clear()

        elif(blackjackGameCheck["running"] == True or blackjackGameCheck["rolling"] == True):
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
        
        myQuery = {"guild_id": ctx.guild.id}
        newValues = {'$set': {'running': True}}
        blackjackGameCol.update_one(myQuery, newValues)
        
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
        
        myQuery = {"guild_id": ctx.guild.id}
        newValues = {'$set': {'rolling': True}}
        blackjackGameCol.update_one(myQuery, newValues)
        
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
                
            if SPLIT_TEST:
                playerHand.clear()
                playerHand.append(Card("10",":diamond_suit:").to_dict())
                playerHand.append(Card("10",":club_suit:").to_dict())

            blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id}, 
                                        {"$set": {"hand": playerHand}})
        
        await ctx.respond("[Blackjack] Game is starting now!")
        # PLAYER'S TURN (BY SEQUENCE OF JOINING)
        colorPicker = 0
        while len(self.queue) > 0:
            player = self.queue.pop()
            playerColor = playerColours[colorPicker%len(playerColours)]
            colorPicker += 1
            
            # Send message to player
            await ctx.respond("[Blackjack] <@" + str(player) + "> is playing next!")
            await asyncio.sleep(2)
            
            # Check if player has blackjack
            for entry in blackjackUserCol.find({"member_id": player, "guild_id": ctx.guild.id},
                                              {"_id": 1, "hand": 1, "playing": 1, "bet": 1}):
                if entry["playing"]:
                    playerHand = entry["hand"]
                    playerId = entry["_id"]
                    playerBet = entry["bet"]
                else:
                    continue
                
            playerHandDesc = print_hand(playerHand)
            houseHandDesc = print_house_hand(houseHand,1)

            if evaluate_hand(playerHand) == 21:                
                embed = discord.Embed(title="[Blackjack] New player's turn!",
                                    description="Now playing - <@" + str(player) + ">\n\n" + 
                                    playerHandDesc + "\n\n" + houseHandDesc,
                                    colour=playerColor,
                                    timestamp=datetime.now())
                await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
                await ctx.respond("[Blackjack] <@" + str(player) + "> has a Blackjack! Lucky bastard")
                continue
            
            timeout = 30
            end_action_time = timeout + math.floor(time.time())
            
            embed = discord.Embed(title="[Blackjack] New player's turn!",
                                  description="Now playing - <@" + str(player) + ">\n\n" + 
                                  playerHandDesc + "\n\n" + houseHandDesc + 
                                  "\n\nType your action: `hit`, `stand`, `double`, or `split`.\n\n\
                                  You have <t:" + str(end_action_time) + ":R> to make your move!",
                                  colour=playerColor,
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
                        if SPLIT_TEST:
                            playerHand.append(Card("10",":heart_suit:").to_dict())
                        else:
                            playerHand.append(draw_card(playDeck).to_dict())
                        
                        
                        # PRINT NEW HAND
                        end_action_time = timeout + math.floor(time.time())
                        playerHandDesc = print_hand(playerHand)
                        houseHandDesc = print_house_hand(houseHand,1)
                        embed = discord.Embed(title="[Blackjack] Player used HIT!",
                                              description="Now playing - <@" + str(player) + ">\n\n" + 
                                              playerHandDesc + "\n\n" + houseHandDesc + 
                                              "\n\nType your action: `hit`, `stand`, `double`, or `split`.\n\n\
                                              You have <t:" + str(end_action_time) + ":R> to make your move!",
                                              colour=playerColor,
                                              timestamp=datetime.now())
                        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
                    
                    # STAND
                    elif message == "stand" or message == "st":
                        flag = 1
                        await ctx.respond("Gotcha, passing your turn to the next person in queue...")
                    
                    # DOUBLE    
                    elif message == "double" or message == "d":
                        #Change bet to double if possible
                        if await update_wallet(ctx, player, playerBet, True) == -1:
                            await ctx.respond("You cannot double your bet! You don't have enough <:beets:1245409413284499587>!", ephemeral=True)
                            continue
                        
                        blackjackUserCol.update_one({"member_id": player, "guild_id": ctx.guild.id, "_id": playerId},
                                                    {"$set": {"bet": playerBet*2}})

                        #Draw a card
                        playerHand.append(draw_card(playDeck).to_dict())
                        
                        playerHandDesc = print_hand(playerHand)
                        houseHandDesc = print_house_hand(houseHand,1)
                        embed = discord.Embed(title="[Blackjack] Player used DOUBLE!",
                                              description="Player - <@" + str(player) + ">\n\n" + 
                                              playerHandDesc + "\n\n" + houseHandDesc +
                                              "\n\nType your action: `hit`, `stand`, `double`, or `split`.\n\n\
                                              You have <t:" + str(end_action_time) + ":R> to make your move!",
                                              colour=playerColor,
                                              timestamp=datetime.now())
                        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
                        flag = 1

                    # SPLIT    
                    elif message == "split" or message == "sp":
                        #Search if hand can be split
                        split1 = -1
                        split2 = -1
                        if len(playerHand) >= 2:
                            for i in range(len(playerHand)):
                                for j in range(i+1, len(playerHand)):
                                    if playerHand[i]["value"] == playerHand[j]["value"]:
                                        split1 = i
                                        split2 = j
                                        break
                        
                        if split1 == -1:
                            await ctx.respond("You cannot split your hand! You don't have a pair of cards with the same value.")
                            continue

                        #Search if player has enough beets to split
                        if await update_wallet(ctx, player, playerBet, True) == -1:
                            await ctx.respond("You cannot split your hand! You don't have enough <:beets:1245409413284499587>!", ephemeral=True)
                            continue

                        #Separate the hand into two
                        playerHand2 = [playerHand[split2]]
                        playerHand.pop(split2)
                        

                        newPlayer = {
                            "member_id": player,
                            "guild_id": ctx.guild.id,
                            "bet": playerBet,
                            "hand": playerHand2,
                            "playing": True
                        }
                        blackjackUserCol.insert_one(newPlayer)

                        #Add player back to queue so they can play their new hand
                        self.queue.append(player)

                        playerHandDesc = print_hand(playerHand)
                        houseHandDesc = print_house_hand(houseHand,1)
                        embed = discord.Embed(title="[Blackjack] Player used SPLIT!",
                                              description="Player - <@" + str(player) + ">\n\n" + 
                                              playerHandDesc + "\n\n" + houseHandDesc +
                                              "\n\nType your action: `hit`, `stand`, `double`, or `split`.\n\n\
                                              You have <t:" + str(end_action_time) + ":R> to make your move!",
                                              colour=playerColor,
                                              timestamp=datetime.now())
                        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())

                    else:
                        await ctx.respond("Invalid action! Please type `hit`, `stand`, `double`, or `split`.", ephemeral=True)
                        continue
                    
                except asyncio.TimeoutError:
                    await ctx.respond("[Blackjack] <@" + str(player) + "> took too long to respond! Standing their hand...")
                    flag = 1
                
                playerScore = evaluate_hand(playerHand)
                if playerScore >= 21:
                    flag = 1
                    if(playerScore == 21):
                        await ctx.respond("[Blackjack] <@" + str(player) + "> finally has a Blackjack! Not even close :sunglasses:. Advancing to next player...")
                        
                    elif(playerScore > 21):
                        await ctx.respond("[Blackjack] <@" + str(player) + "> busted! Advancing to next player...")


            # Update final hand to database
            myQuery= {"member_id": player, "guild_id": ctx.guild.id, "_id": playerId}
            newValues = {'$set': {'hand': playerHand, 'playing': False}}
            blackjackUserCol.update_one(myQuery, newValues)

        embed = discord.Embed(title="[Blackjack] House's turn!",
                              description="Revealing house's hand...\n\n" + print_house_hand(houseHand, 0),
                              colour=0x009900,
                              timestamp=datetime.now())
        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())

        # HOUSE TURN
        while evaluate_hand(houseHand) < 17:
            #Suspense...
            await asyncio.sleep(3)
            houseHand.append(draw_card(playDeck).to_dict())
            embed = discord.Embed(title="[Blackjack] House's turn!",
                                  description="Drawing cards...\n\n" + print_house_hand(houseHand, 0),
                                  colour=0x009900,
                                  timestamp=datetime.now())
            await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())
            
        # CHECK WINNERS
        await asyncio.sleep(1)
        houseValue = evaluate_hand(houseHand)
        for player in blackjackUserCol.find({"guild_id": ctx.guild.id},
                                            {"_id": 0, "member_id": 1, "hand": 1, "bet": 1}):
            await calculate_player_reward(ctx, player, houseValue)

        # Clean up from database
        myQuery = {"guild_id": ctx.guild.id}
        newValues = {'$set': {'running': False, 'rolling': False}}
        blackjackGameCol.update_one(myQuery, newValues)
        blackjackUserCol.delete_many(myQuery)


    @blackjack.command(name="bet", description="Participate in a game of Blackjack.")
    @discord.option("amount", description="Your bet amount against the house.", required=True)
    async def bet(self, ctx: discord.ApplicationContext, amount: int):
        # Check if there is a game running in the server
        blackjackGameCheck = blackjackGameCol.find_one({"guild_id": ctx.guild.id},{"_id": 0, "running": 1, "rolling": 1})
        if(blackjackGameCheck is None or blackjackGameCheck["running"] == False):
            await ctx.respond("There is no game running in this server! Start one yourself :)", ephemeral=True)
            return
        
        # Check if the game is already rolling
        if(blackjackGameCheck["rolling"] == True):
            await ctx.respond("The game is already rolling! Wait for the next round to bet.", ephemeral=True)
            return
        
        # Check if user is already in the queue
        if ctx.author.id in self.queue:
            await ctx.respond("You are already in the queue! Wait a sec lil bro", ephemeral=True)
            return

        if(amount <= 0):
            await ctx.respond("<@" + str(ctx.author.id) + "Buddy, ya ain't slick.")
            try:
                await ctx.author.edit(nick=ctx.author.display_name + " 🤡", reason="Tried to cheat Jeraptha")
            except:
                pass
            return
        
        if await update_wallet(ctx, ctx.author.id, amount, True) == -1:
            return

        newPlayer = {
            "member_id": ctx.author.id,
            "guild_id": ctx.guild.id,
            "bet": amount,
            "hand": [],
            "playing": True
        }
        blackjackUserCol.insert_one(newPlayer)
        self.queue.insert(0, ctx.author.id)

        await ctx.respond("[Blackjack] <@" + str(ctx.author.id) + "> entered the table with a **" + str(amount) + "**<:beets:1245409413284499587> bet!")

    @blackjack.command(name="reset", description="[ADMIN] Reset Blackjack table.")
    async def reset(self, ctx: discord.ApplicationContext):
        role = discord.utils.get(ctx.author.roles, name=adminRole) #Check if user has the correct role
        if role is None:
            await ctx.respond("You don't have the necessary role!", ephemeral=True)
            return
        
        for player in blackjackUserCol.find({"guild_id": ctx.guild.id},{"_id": 0, "member_id": 1,
                                                                        "bet": 1, "split": 1}):
            await update_wallet(ctx, player["member_id"], player["bet"], False)

        blackjackGameCol.delete_many({})
        blackjackUserCol.delete_many({})
        await ctx.respond("Blackjack table reset!")

def setup(bot):
    bot.add_cog(Blackjack(bot))