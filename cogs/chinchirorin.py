import os
import discord
from discord.ext import commands

import time, math
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
# chinchiroGameCol = myDB["ChinchirorinGame"] 
# chinchiroUserCol = myDB["ChinchirorinUser"]


def evaluate_hand(dice):
    hand = dice.get()

    #RULESET: Underground Chinchirorin https://games.porg.es/games/cee-lo/
    #1-1-1 = 999 points (5x payout)
    #Triple = 7 points + dice value (3x payout)
    #4-5-6 = 7 points (2x payout)
    #Double with any other valur = point of the 3rd dice (1x payout)
    #Not a hand = 0 points (1x loss)
    #1-2-3 = = -1 points (2x loss)

    #Triples
    if hand[0] == hand[1] and hand[1] == hand[2]:
        #1-1-1
        if hand[0] == 1:
            return 999
        #Other triple
        else:
            return 7 + hand[0]

    #4-5-6
    if hand[0] == 4 and hand[1] == 5 and hand[2] == 6:
        return 7

    #Doubles
    if hand[0] == hand[1]:
        return hand[2]
    elif hand[1] == hand[2]:
        return hand[0]
    elif hand[0] == hand[2]:
        return hand[1]

    #1-2-3
    if (hand[0] == 1) and (hand[1] == 2) and (hand[2] == 3):
        return -1
    
    #Not a hand
    return 0

class Die:
    def __init__(self, sides=6):
        self.sides = sides
        self.roll_value = 0

    def roll(self):
        self.roll_value = random.randint(1,self.sides)

    def get(self):
        return self.roll_value

class Dice:
    def __init__(self, number=3):
        self.set = []
        for i in range(number):
            self.set.append(Die(sides=6))

    def roll(self):
        for x in self.set:
            x.roll()

    def get(self):
        results = []
        for x in self.set:
            results.append(x.get())

        results.sort()
        return results

class Player:
    def __init__(self, betAmmount, playerName):
        self.betAmmount = betAmmount
        self.playerName = playerName
        self.score = 0
        self.dice = Dice(3)

    def play(self):
        self.dice.roll()
        self.score = evaluate_hand(self.dice)

    def get_roll(self):
        return self.dice.get()

    def get_score(self):
        return self.score

class Chinchirorin(commands.Cog):
    """
    Start a game of Chinchirorin
    Default rules: https://en.wikipedia.org/wiki/Cee-lo
    """

    def __init__(self, bot):
        self.bot = bot

    chinchirorin = discord.SlashCommandGroup("chinchirorin", "Chinchirorin related commands.")

    # CHINCHIRORIN START
    @chinchirorin.command(name="play", description="Play a game of Cee-lo (Underground Chinchirorin ruleset).")
    @discord.option("bet_amount", description="Your bet amount against the bank", required=True)
    async def play(self, ctx: discord.ApplicationContext, bet_amount: int):
        #Verify bet amount
        if(bet_amount <= 0):
            await ctx.respond("<@" + str(ctx.author.id) + "Nice try! However, Zǎoshang hǎo zhōngguó xiànzài wǒ yǒu BING CHILLING 🥶🍦 wǒ hěn xǐhuān BING CHILLING 🥶🍦 dànshì sùdù yǔ jīqíng 9 bǐ BING CHILLING 🥶🍦 sùdù yǔ jīqíng sùdù yǔ jīqíng 9 wǒ zuì xǐhuān suǒyǐ…xiànzài shì yīnyuè shíjiān zhǔnbèi 1 2 3 liǎng gè lǐbài yǐhòu sùdù yǔ jīqíng 9 ×3 bùyào wàngjì bùyào cu òguò jìdé qù diànyǐngyuàn kàn sùdù yǔ jīqíng 9 yīn wéi fēicháng hǎo diànyǐng dòngzuò fēicháng hǎo chàbùduō yīyàng BING CHILLING 🥶🍦zàijiàn 🥶🍦")
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

        if(userCheck["coins"] < bet_amount): 
            await ctx.respond("You intend to pay with your kneecaps or <:beets:1245409413284499587>? Because you seem to be out of <:beets:1245409413284499587>.", ephemeral=True)
            return
        elif(userCheck["coins"] < 2*bet_amount): 
            await ctx.respond("This game has a 1/216 chance of losing double the amount of <:beets:1245409413284499587> bet, so we need you to have at least that amount of liquidity.", ephemeral=True)
        
        #Update wallet before game
        removeCoins = 0 - bet_amount
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(removeCoins), 'coins_bet': int(bet_amount)}}
        usersCol.update_one(myQuery, newValues)

        bank = Player(betAmmount=bet_amount,playerName="Jeraptha")
        player = Player(betAmmount=bet_amount,playerName=ctx.author.id)

        # BANK'S TURN
        for i in range(3):
            bank.play()
            #INSERT DISCORD EMBEDS FOR ROLLS HERE
            if bank.get_score() != 0:
                break

        # PLAYER'S TURN
        for i in range(3):
            player.play()
            #INSERT DISCORD EMBED FOR ROLLS HERE
            if player.get_score() != 0:
                break

        # Win protocol
        if player.get_score() > bank.get_score() :
            winnings = bet_amount
            if player.get_score() == 99:
                winnings += bet_amount*5
            elif player.get_score() > 7:
                winnings += bet_amount*3
            elif(player.get_score() == 7):
                winnings += bet_amount*2
            else:
                winnings += bet_amount

            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': winnings, 'earned_bet': winnings, 'total_earned': winnings}}
            usersCol.update_one(myQuery, newValues)
            #INSERT DISCORD EMBED FOR WINNINGS HERE

        # Tie protocol
        elif player.get_score() == bank.get_score() :
            winnings = bet_amount
            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': winnings, 'earned_bet': winnings, 'total_earned': winnings}}
            usersCol.update_one(myQuery, newValues)
            #INSERT DISCORD EMBED FOR TIES HERE

        # Loss protocol
        else :
            if player.get_score() == -1:
                extraLoss = 0 - bet_amount
                myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
                newValues = {'$inc': {'coins': int(extraLoss)}}
                usersCol.update_one(myQuery, newValues)
                #INSERT DISCORD EMBED FOR FAT L
            
            #INSERT DISCORD EMBED FOR NORMAL L

# bank = Player(betAmmount=100,playerName="Jeraptha")
# player = Player(betAmmount=100,playerName="Asdrubal")

# bank.play()
# print(bank.get_score())

# player.play()
# print(player.get_score())

