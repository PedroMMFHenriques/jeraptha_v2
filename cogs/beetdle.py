import os
import discord
from discord.ext import commands

import time, math
from datetime import datetime, timedelta, date

import pymongo

import asyncio
import random

import numpy as np

import json
global_json = json.load(open('global.json'))

global_vars = global_json["VARS"]

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
beetdleCol = myDB[db["BEETDLE_COL"]]



wotd_list = [] # Get word of the day list: faster to get a random word
full_dict = {} # All guesses dictionary: faster to verify if word is valid
with open("data/beetdle_dict/wordle-La.txt", 'r') as file:
    for line in file:
        word = line.strip()
        if word:  # Ensure the line is not empty
            wotd_list.append(word)
            full_dict[word] = ''

with open("data/beetdle_dict/wordle-Ta.txt", 'r') as file:
    for line in file:
        word = line.strip()
        if word:  # Ensure the line is not empty
            full_dict[word] = ''


#AdminRole = global_json["ROLES"]["ADMIN_ROLE"]
#WagerRole = global_json["ROLES"]["WAGER_ROLE"]

class Beetdle(commands.Cog):
    """
    Play a beetdle game: guess 5-letter English word.
    """
        
    def __init__(self, bot):
        self.bot = bot

    
    # BEETDLE
    @discord.command(name="beetdle", description="Start/continue a game of beetdle.")
    @discord.option("guess", description="Your beetdle guess (5-letter English word)", required=True)
    async def start(self, ctx: discord.ApplicationContext, guess: str):
        # Check validity of guess
        if(len(guess) != 5):
            await ctx.respond("Invalid guess! Must be a 5-letter word.", ephemeral=True)
            return
        elif(not guess in full_dict):
            await ctx.respond("That word isn't in the English dictionary!", ephemeral=True)
            return
        
        datetime_today = datetime.combine(datetime.today(), datetime.min.time())

        # Check if it is the first guess of the daily
        checkNewDailyGame = beetdleCol.find_one({"member_id": ctx.author.id, "date": datetime_today},{})
        if(checkNewDailyGame is None): # If it is the first guess of the daily
            seed = datetime_today - datetime.combine(date(1970, 1, 1), datetime.min.time()) # Current day's seed
            random.seed(seed)
            wotd = wotd_list[random.randint(0, len(wotd_list) - 1)]
            beetdleCol.insert_one({"member_id": ctx.author.id, "date": datetime_today, "daily": True, "word": wotd, "tries": 0, "ended": False, "won": False, "guesses": guess})
        
        else:
            # Check if it is the first guess of a non-daily
            checkNewNonDailyGame = beetdleCol.find_one({"member_id": ctx.author.id, "date": datetime_today, "ended": False},{})
            if(checkNewNonDailyGame is None): # If it is the first guess of a non-daily
                random.seed()
                wotd = wotd_list[random.randint(0, len(wotd_list) - 1)]
                beetdleCol.insert_one({"member_id": ctx.author.id, "date": datetime_today, "daily": False, "word": wotd, "tries": 0, "ended": False, "won": False, "guesses": ""})

        checkBeetdle = beetdleCol.find_one({"member_id": ctx.author.id, "date": datetime_today, "ended": False},{"_id": 0, "daily": 1, "word": 1, "tries": 1, "guesses": 1})

        daily = checkBeetdle["daily"]
        n_tries = checkBeetdle["tries"] + 1
        prev_guesses = checkBeetdle["guesses"]

        won = False

        # Process guess
        word = checkBeetdle["word"]
        if(guess == word): # Correct word, end game
            won = True
            guesses = prev_guesses + str(n_tries) + ") **" + word + "**"
            myQuery= {"member_id": ctx.author.id, "date": datetime_today, "ended": False}
            newValues = {'$set': {"ended": True, "won": True, "guesses": guesses}, '$inc': {"tries": 1}}
            beetdleCol.update_one(myQuery, newValues)

            reward = np.random.normal(loc=global_vars["DAILY_MEAN"], scale=global_vars["DAILY_STD"], size = (1))[0]

            if(daily):
                emb_title = "You got it! The daily beetdle is **" + word + "**!"
                emb_description = "It took you " + str(n_tries) + " tries."
                emb_field_name = "Your tries:"
                emb_ephemeral = True
            else:
                reward = reward / 10
                emb_title = "<@" + str(ctx.author.id) + "> got the beetdle **" + word + "**!"
                emb_description = "It took them " + str(n_tries) + " tries."
                emb_field_name = "Their tries:"
                emb_ephemeral = False

            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {"$set": {"last_daily": datetime.now()},'$inc': {'coins': int(reward)}}
            usersCol.update_one(myQuery, newValues)
        

        else: # Incorrect word, continue game
            word_count = {}
            for letter in word:
                if(not letter in word_count): # First occurence of letter
                    word_count[letter] = 1
                else: word_count[letter] += 1

            correction = "" #C correct, S correct wrong space, X incorrect
            for letter_g, letter_word in zip(guess, word):
                if(not letter_g in word_count): # Wrong letter
                    correction += "X"
                elif(letter_g == letter_word): # Correct letter in correct space
                    correction += "C" 
                    word_count[letter_g] -= 1
                elif(word_count[letter_g] >= 1): # Correct letter in wrong space
                    correction += "S"
                    word_count[letter_g] -= 1
                else: # The letter is there, but there are too many already
                    correction += "X"

            guess_correction = ""
            for letter_g, letter_c in zip(guess, correction):
                if(letter_c == "C"): cor = "**"
                elif(letter_c == "S"): cor = "__"
                else: cor = "~~"
                guess_correction += cor + letter_g + cor

            guesses = prev_guesses + str(n_tries) + ") " + guess_correction
            if(n_tries >= 6): # Lost, end game
                myQuery= {"member_id": ctx.author.id, "date": datetime_today, "ended": False}
                newValues = {'$set': {"ended": True, "won": False, "guesses": guesses}, '$inc': {"tries": 1}}
                beetdleCol.update_one(myQuery, newValues)

                if(daily):
                    emb_title = "You lost... The daily beetdle was **" + word + "**."
                    emb_description = ""
                    emb_field_name = "Your tries:"
                    emb_ephemeral = True
                else:
                    emb_title = "<@" + str(ctx.author.id) + "> lost... The beetdle was **" + word + "**."
                    emb_description = ""
                    emb_field_name = "Their tries:"
                    emb_ephemeral = False
            
            else: # Incorrect, but still has tries
                myQuery= {"member_id": ctx.author.id, "date": datetime_today, "ended": False}
                newValues = {'$set': {"guesses": guesses}, '$inc': {"tries": 1}}
                beetdleCol.update_one(myQuery, newValues)

                emb_title = "[Try " + str(n_tries) + "] " + guess + " wasn't correct."
                emb_description = "**Bold** is correct letter in correct space, __underline__ is correct letter in wrong space and ~~strikethrough~~ is incorrect.\n\n"
                emb_description += "You have **" + str(6 - n_tries) + "** more tries."
                emb_field_name = "Your tries:"
                emb_ephemeral = True

        embed = discord.Embed(title=emb_title,
                      description=emb_description,
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.add_field(name=emb_field_name,
                        value=guesses,
                        inline=False)

        embed.set_footer(text="Beetdle",
                         icon_url="https://png.pngtree.com/png-vector/20220603/ourmid/pngtree-a-letter-b-for-beetle-chitinous-alphabet-capitalized-vector-png-image_36940140.png")

        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions(), ephemeral=emb_ephemeral)

        if(daily):
            if(won):
                await ctx.send("[Beetdle] <@" + str(ctx.author.id) + "> got the daily beetdle correctly in " + str(n_tries) + " tries!")
            else:
                await ctx.send("[Beetdle] <@" + str(ctx.author.id) + "> didn't get the daily beetle correctly...")

        print(word)


def setup(bot):
    bot.add_cog(Beetdle(bot))



