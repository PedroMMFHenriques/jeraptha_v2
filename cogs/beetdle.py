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
    @discord.command(name="beetdle", description="Start/continue a game of beetdle. The first daily is equal to everyone and gives full reward.")
    @discord.option("guess", description="Your beetdle guess (5-letter English word)", required=True)
    async def start(self, ctx: discord.ApplicationContext, guess: str):
        # Check validity of guess
        if(len(guess) != 5):
            await ctx.respond("Invalid guess! Must be a 5-letter word.", ephemeral=True)
            return
        elif(not guess.lower() in full_dict):
            await ctx.respond("That word isn't in the English dictionary!", ephemeral=True)
            return
        
        guess = guess.upper()
        
        datetime_today = datetime.combine(datetime.today(), datetime.min.time())

        # Check if it is the first guess of the daily
        checkNewDailyGame = beetdleCol.find_one({"member_id": ctx.author.id, "date": datetime_today},{})
        if(checkNewDailyGame is None): # If it is the first guess of the daily
            seed = datetime_today - datetime.combine(date(1970, 1, 1), datetime.min.time()) # Current day's seed
            random.seed(seed)
            wotd = wotd_list[random.randint(0, len(wotd_list) - 1)]
            beetdleCol.insert_one({"member_id": ctx.author.id, "date": datetime_today, "daily": True, "word": wotd.upper(), "tries": 0, "ended": False, "won": False, "guesses": "", "guesses_print": ""})
        
        else:
            # Check if it is the first guess of a non-daily
            checkNewNonDailyGame = beetdleCol.find_one({"member_id": ctx.author.id, "date": datetime_today, "ended": False},{})
            if(checkNewNonDailyGame is None): # If it is the first guess of a non-daily
                random.seed()
                wotd = wotd_list[random.randint(0, len(wotd_list) - 1)]
                beetdleCol.insert_one({"member_id": ctx.author.id, "date": datetime_today, "daily": False, "word": wotd.upper(), "tries": 0, "ended": False, "won": False, "guesses": "", "guesses_print": ""})

        checkBeetdle = beetdleCol.find_one({"member_id": ctx.author.id, "date": datetime_today, "ended": False},{"_id": 0, "daily": 1, "word": 1, "tries": 1, "guesses": 1, "guesses_print": 1})

        daily = checkBeetdle["daily"]
        prev_guesses = checkBeetdle["guesses"]
        prev_guesses_print = checkBeetdle["guesses_print"]

        prev_guesses_list = prev_guesses.split(",")
        if(guess in prev_guesses_list):
            await ctx.respond("You already guessed that!", ephemeral=True)
            return

        game_won = False
        game_over = False
        n_tries = checkBeetdle["tries"] + 1
        # Process guess
        word = checkBeetdle["word"]
        if(guess == word): # Correct word, end game
            game_won = True
            game_over = True
            guesses = prev_guesses + "," + word
            guess_separated = ""
            for letter in word:
                guess_separated += letter + " "
            guesses_print = prev_guesses_print + "**" + guess_separated + "**"
            myQuery= {"member_id": ctx.author.id, "date": datetime_today, "ended": False}
            newValues = {'$set': {"ended": True, "won": True, "guesses": guesses, "guesses_print": guesses_print}, '$inc': {"tries": 1}}
            beetdleCol.update_one(myQuery, newValues)

            reward = np.random.normal(loc=global_vars["DAILY_MEAN"], scale=global_vars["DAILY_STD"], size = (1))[0]

            if(daily):
                emb_title = "[Daily Beetle] You got it! The daily beetdle is '" + word + "'!"
                emb_description = "It took you **" + str(n_tries) + "** tries.\nYou won " + str(int(reward)) + "<:beets:1245409413284499587>!"
                emb_field_name = "Your tries:"
                emb_ephemeral = True
            else:
                reward = reward / 10
                emb_title = "[Non-Daily Beetle] You got the beetdle '" + word + "'!"
                emb_description = "It took <@" + str(ctx.author.id) + "> " + str(n_tries) + " tries.\nThey won " + str(int(reward)) + "<:beets:1245409413284499587>!"
                emb_field_name = "Their tries:"
                emb_ephemeral = False

            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': int(reward)}}
            usersCol.update_one(myQuery, newValues)
        

        else: # Incorrect word, continue game
            word_count = {}
            for letter in word:
                if(not letter in word_count): # First occurence of letter
                    word_count[letter] = 1
                else: word_count[letter] += 1

            # First check exactly correct letters
            correction = "" #C correct, P possible correct wrong space, X incorrect
            for letter_g, letter_word in zip(guess, word):
                if(not letter_g in word_count): # Wrong letter
                    correction += "X"
                elif(letter_g == letter_word): # Correct letter in correct space
                    correction += "C" 
                    word_count[letter_g] -= 1
                else: # Possible correct letter in wrong space
                    correction += "S"


            # Now check correct letters in wrong places
            #C correct, S correct wrong space, X incorrect
            final_correction = ""
            for letter_g, letter_c in zip(guess, correction):
                if(letter_c == "X" or letter_c == "C"): # Wrong letter or correct letter
                    final_correction += letter_c
                elif(word_count[letter_g] >= 1): # Correct letter in wrong space
                    final_correction += "S"
                    word_count[letter_g] -= 1
                else:
                    final_correction += "X"

            guess_correction = ""
            for letter_g, letter_c in zip(guess, final_correction):
                if(letter_c == "C"): cor = "**"
                elif(letter_c == "S"): cor = "__"
                else: cor = "~~"
                guess_correction += cor + letter_g + cor + " "

            guesses = prev_guesses + "," + guess
            guesses_print = prev_guesses_print + guess_correction + "\n"
            if(n_tries >= 6): # Lost, end game
                game_over = True
                myQuery= {"member_id": ctx.author.id, "date": datetime_today, "ended": False}
                newValues = {'$set': {"ended": True, "won": False, "guesses": guesses, "guesses_print": guesses_print}, '$inc': {"tries": 1}}
                beetdleCol.update_one(myQuery, newValues)

                if(daily):
                    emb_title = "[Daily Beetle] You lost... The daily beetdle was '" + word + "'."
                    emb_description = "You didn't win any <:beets:1245409413284499587>..."
                    emb_field_name = "Your tries:"
                    emb_ephemeral = True
                else:
                    emb_title = "[Non-Daily Beetle] You lost... The beetdle was '" + word + "'."
                    emb_description = "<@" + str(ctx.author.id) + "> didn't win any <:beets:1245409413284499587>..."
                    emb_field_name = "Their tries:"
                    emb_ephemeral = False
            
            else: # Incorrect, but still has tries
                myQuery= {"member_id": ctx.author.id, "date": datetime_today, "ended": False}
                newValues = {'$set': {"guesses": guesses, "guesses_print": guesses_print}, '$inc': {"tries": 1}}
                beetdleCol.update_one(myQuery, newValues)

                if(daily):
                    emb_title = "[Daily Beetle] Try " + str(n_tries) + " '" + guess + "' wasn't correct."
                else:
                    emb_title = "[Non-Daily Beetle] Try " + str(n_tries) + " '" + guess + "' wasn't correct."
                emb_description = "**Bold** is correct letter in correct space, __underline__ is correct letter in wrong space and ~~strikethrough~~ is incorrect.\n"
                emb_description += "You have **" + str(6 - n_tries) + "** more tries."
                emb_field_name = "Your tries:"
                emb_ephemeral = True

        embed = discord.Embed(title=emb_title,
                      description=emb_description,
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.add_field(name=emb_field_name,
                        value=guesses_print,
                        inline=False)

        embed.set_footer(text="Beetdle",
                         icon_url="https://png.pngtree.com/png-vector/20220603/ourmid/pngtree-a-letter-b-for-beetle-chitinous-alphabet-capitalized-vector-png-image_36940140.png")

        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions(), ephemeral=emb_ephemeral)

        if(daily and game_over):
            if(game_won):
                await ctx.send("[Daily Beetdle] <@" + str(ctx.author.id) + "> got the daily beetdle correctly in " + str(n_tries) + " tries!")
            else:
                await ctx.send("[Daily Beetdle] <@" + str(ctx.author.id) + "> didn't get the daily beetle correctly...")


def setup(bot):
    bot.add_cog(Beetdle(bot))



