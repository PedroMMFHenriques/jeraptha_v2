import discord
from discord.ext import commands

from datetime import datetime, date

import pymongo

import random

import numpy as np

import json
global_json = json.load(open('global.json'))

global_consts = global_json["CONSTS"]

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


    beetdle = discord.SlashCommandGroup("beetdle", "Play Beetdle: make a guess or remind your previous guesses.")
    
    # BEETDLE GUESS
    @beetdle.command(name="guess", description="Start/continue a game of beetdle. The first daily is equal to everyone and gives full reward.")
    @discord.option("your_guess", description="Your beetdle guess (5-letter English word)", required=True)
    async def guess(self, ctx: discord.ApplicationContext, your_guess: str):
        # Check validity of guess
        if(len(your_guess) != 5):
            await ctx.respond("Invalid guess! Must be a 5-letter word.", ephemeral=True)
            return
        elif(not your_guess.lower() in full_dict):
            await ctx.respond("That word isn't in the English dictionary!", ephemeral=True)
            return
        
        your_guess = your_guess.upper()
        
        datetime_today = datetime.combine(datetime.today(), datetime.min.time())

        # Check if it is the first guess of the daily
        checkNewDailyGame = beetdleCol.find_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today},{})
        if(checkNewDailyGame is None): # If it is the first guess of the daily
            seed = (datetime_today - datetime.combine(date(1970, 1, 1), datetime.min.time())).days + ctx.guild.id # Current day's seed of the guild
            random.seed(seed)
            wotd = wotd_list[random.randint(0, len(wotd_list) - 1)]
            random.seed()
            beetdleCol.insert_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "daily": True, "word": wotd.upper(), "tries": 0, "ended": False, "won": False, "guesses": "", "guesses_print": ""})
        
        else:
            # Check if it is the first guess of a non-daily
            checkNewNonDailyGame = beetdleCol.find_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": False},{})
            if(checkNewNonDailyGame is None): # If it is the first guess of a non-daily
                wotd = wotd_list[random.randint(0, len(wotd_list) - 1)]
                beetdleCol.insert_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "daily": False, "word": wotd.upper(), "tries": 0, "ended": False, "won": False, "guesses": "", "guesses_print": ""})

        checkBeetdle = beetdleCol.find_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": False},{"_id": 0, "daily": 1, "word": 1, "tries": 1, "guesses": 1, "guesses_print": 1})
        
        daily = checkBeetdle["daily"]
        prev_guesses = checkBeetdle["guesses"]
        prev_guesses_print = checkBeetdle["guesses_print"]

        prev_guesses_list = prev_guesses.split(",")
        if(your_guess in prev_guesses_list):
            await ctx.respond("You already guessed that!", ephemeral=True)
            return

        
        # Stores the list of unused letters (0: wrong; 1: unused; 2: wrong place; 3: correct)
        unused_letters = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 1,
                        'H': 1, 'I': 1, 'J': 1, 'K': 1, 'L': 1, 'M': 1, 'N': 1,
                        'O': 1, 'P': 1, 'Q': 1, 'R': 1, 'S': 1, 'T': 1, 'U': 1,
                        'V': 1, 'W': 1, 'X': 1, 'Y': 1, 'Z': 1}
        # Saves the correct letters so far, to facilitate guessing
        correct_letters = ["\_", "\_", "\_", "\_", "\_"]

        game_won = False
        game_over = False
        n_tries = checkBeetdle["tries"] + 1
        # Process guess
        word = checkBeetdle["word"]
        if(your_guess == word): # Correct word, end game
            game_won = True
            game_over = True
            guesses = prev_guesses + "," + word
            guess_separated = ""
            for letter in word:
                guess_separated += letter + " "
            guesses_print = prev_guesses_print + "**" + guess_separated + "**"
            myQuery= {"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": False}
            newValues = {'$set': {"ended": True, "won": True, "guesses": guesses, "guesses_print": guesses_print}, '$inc': {"tries": 1}}
            beetdleCol.update_one(myQuery, newValues)

            reward = np.random.normal(loc=global_consts["DAILY_MEAN"], scale=global_consts["DAILY_STD"], size = (1))[0]
            reward = reward*(1 + (6-n_tries)/5) # increase by 20% per try left

            if(daily):
                if(n_tries == 1):
                    emb_title = "[Daily Beetdle] WHAAAAT! You got the daily beetdle correctly in the first try! It is '" + word + "'."
                    emb_description = "You won " + str(int(reward)) + "<:beets:1245409413284499587>!"
                elif(n_tries == 6):
                    emb_title = "[Daily Beetdle] PHEW! You got the daily beetdle correctly in the last try! It is '" + word + "'."  
                    emb_description = "You won " + str(int(reward)) + "<:beets:1245409413284499587>!"              
                else:
                    emb_title = "[Daily Beetdle] You got it! The daily beetdle is '" + word + "'!"
                    emb_description = "It took you **" + str(n_tries) + "** tries.\nYou won " + str(int(reward)) + "<:beets:1245409413284499587>!"
                emb_field_name = "Your tries:"
                emb_ephemeral = True
            else:
                reward = reward / 10
                if(n_tries == 1):
                    emb_title = "[Non-Daily Beetdle] WHAAAAT! You got the beetdle correctly in the first try! It is '" + word + "'."
                    emb_description = "<@" + str(ctx.author.id) + "> won " + str(int(reward)) + "<:beets:1245409413284499587>!"
                elif(n_tries == 6):
                    emb_title = "[Non-Daily Beetdle] PHEW! You got the beetdle correctly in the last try! It is '" + word + "'."  
                    emb_description = "<@" + str(ctx.author.id) + "> won " + str(int(reward)) + "<:beets:1245409413284499587>!"              
                else:
                    emb_title = "[Non-Daily Beetdle] You got it! The beetdle is '" + word + "'!"
                    emb_description = "It took <@" + str(ctx.author.id) + "> **" + str(n_tries) + "** tries.\nThey won " + str(int(reward)) + "<:beets:1245409413284499587>!"
                emb_field_name = "Their tries:"
                emb_ephemeral = False
                
            # Check maximum games per day
            myQuery = {"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": True}
            if(beetdleCol.count_documents(myQuery, limit=10) >= 10):
                emb_description = "<@" + str(ctx.author.id) + "> already completed 10 Beetdles today, so they did't get more rewards."
                reward = 0
            else:
                myQuery= {"guild_id": ctx.guild.id, "member_id": ctx.author.id, "guild_id": ctx.guild.id}
                newValues = {'$inc': {'coins': int(reward), 'total_earned': int(reward)}}
                usersCol.update_one(myQuery, newValues)
            

        else: # Incorrect word, continue game
            word_count = {}
            for letter in word:
                if(not letter in word_count): # First occurence of letter
                    word_count[letter] = 1
                else: word_count[letter] += 1

            # First check exactly correct letters
            correction = "" #C correct, P possible correct wrong space, X incorrect
            for letter_g, letter_word in zip(your_guess, word):
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
            for letter_g, letter_c in zip(your_guess, correction):
                if(letter_c == "X" or letter_c == "C"): # Wrong letter or correct letter
                    final_correction += letter_c
                elif(word_count[letter_g] >= 1): # Correct letter in wrong space
                    final_correction += "S"
                    word_count[letter_g] -= 1
                else:
                    final_correction += "X"

            guess_correction = ""
            for letter_g, letter_c in zip(your_guess, final_correction):
                if(letter_c == "C"): cor = "**"
                elif(letter_c == "S"): cor = "__"
                else: cor = "~~"
                guess_correction += cor + letter_g + cor + " "

            guesses = prev_guesses + "," + your_guess
            guesses_print = prev_guesses_print + guess_correction + "\n"
            if(n_tries >= 6): # Lost, end game
                game_over = True
                myQuery= {"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": False}
                newValues = {'$set': {"ended": True, "won": False, "guesses": guesses, "guesses_print": guesses_print}, '$inc': {"tries": 1}}
                beetdleCol.update_one(myQuery, newValues)

                
                if(daily):
                    emb_title = "[Daily Beetdle] Oh, you lost... The daily beetdle was '" + word + "'."
                    emb_description = "You didn't win any <:beets:1245409413284499587>..."
                    emb_field_name = "Your tries:"
                    emb_ephemeral = True
                else:
                    emb_title = "[Non-Daily Beetdle] Oh, you lost... The beetdle was '" + word + "'."
                    emb_description = "<@" + str(ctx.author.id) + "> didn't win any <:beets:1245409413284499587>..."
                    emb_field_name = "Their tries:"
                    emb_ephemeral = False

                if(beetdleCol.count_documents(myQuery, limit=10) >= 10):
                    emb_description = "<@" + str(ctx.author.id) + "> already completed 10 Beetdles today, so they didn't get more rewards."
            
            else: # Incorrect, but still has tries
                myQuery= {"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": False}
                newValues = {'$set': {"guesses": guesses, "guesses_print": guesses_print}, '$inc': {"tries": 1}}
                beetdleCol.update_one(myQuery, newValues)
                
                emb_description = ""
                # Check if already reach maximum number of rewarded games
                myQuery = {"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": True}
                if(beetdleCol.count_documents(myQuery, limit=10) >= 10):
                    emb_description += "*You already completed 10 Beetdles today, so you won't get more rewards.*\n\n"

                if(daily):
                    emb_title = "[Daily Beetdle] Try " + str(n_tries) + " '" + your_guess + "' wasn't correct."
                else:
                    emb_title = "[Non-Daily Beetdle] Try " + str(n_tries) + " '" + your_guess + "' wasn't correct."
                emb_description += "**Bold** is correct letter in correct space, __underline__ is correct letter in wrong space and ~~strikethrough~~ is incorrect.\n\n"
                if(n_tries == 5):
                    emb_description += "You only have **one last try**!"
                else:
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
        
        # embed for the unused letters
        temp_guess_list = guesses_print.split("\n")
        for words_formatted in temp_guess_list[:-1]:
            letters_formatted = words_formatted.split(" ")
            for iterator in range(5):
                temp_letter = letters_formatted[iterator]
                if(len(temp_letter) == 5):
                    if(temp_letter[0] == "*"):
                        unused_letters[temp_letter[2]] = 3
                        correct_letters[iterator] = temp_letter
                    elif(temp_letter[0] == "_"):
                        unused_letters[temp_letter[2]] = 2
                    elif(temp_letter[0] == "~"):
                        unused_letters[temp_letter[2]] = 0
        
        unused_letters_print = ""
        wrong_place_letters_print = ""
        for key, value in unused_letters.items():
            if value == 1:
                unused_letters_print += key + " "
            elif value == 2:
                wrong_place_letters_print += key + " "
                    

        embed.add_field(name="Unused Letters:",
                        value=unused_letters_print,
                        inline=False)
        
        embed.add_field(name="Wrong Place Letters:",
                        value=wrong_place_letters_print,
                        inline=False)
        
        embed.add_field(name="Correct Letters:",
                        value=correct_letters[0] + " " + correct_letters[1] + " " + correct_letters[2] + " " + correct_letters[3] + " " + correct_letters[4],
                        inline=False)
        
        embed.set_footer(text="Beetdle",
                         icon_url="https://png.pngtree.com/png-vector/20220603/ourmid/pngtree-a-letter-b-for-beetle-chitinous-alphabet-capitalized-vector-png-image_36940140.png")

        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions(), ephemeral=emb_ephemeral)

        if(daily and game_over):
            if(game_won):
                if(n_tries == 1):
                    await ctx.send("[Daily Beetdle] WHAAAAT! <@" + str(ctx.author.id) + "> got the daily beetdle correctly in the first try and won " + str(int(reward)) + "<:beets:1245409413284499587>!")
                elif(n_tries == 6):
                    await ctx.send("[Daily Beetdle] PHEW! <@" + str(ctx.author.id) + "> got the daily beetdle correctly in the last try and won " + str(int(reward)) + "<:beets:1245409413284499587>!")
                else:
                    await ctx.send("[Daily Beetdle] <@" + str(ctx.author.id) + "> got the daily beetdle correctly in " + str(n_tries) + " tries and won " + str(int(reward)) + "<:beets:1245409413284499587>!")
            else:
                await ctx.send("[Daily Beetdle] <@" + str(ctx.author.id) + "> didn't get the daily beetdle correctly...")



    @beetdle.command(name="remind", description="Remind yourself of your previous guesses.")
    async def remind(self, ctx: discord.ApplicationContext):
        datetime_today = datetime.combine(datetime.today(), datetime.min.time())

        checkBeetdle = beetdleCol.find_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "date": datetime_today, "ended": False},{"_id": 0, "daily": 1, "guesses_print": 1})
        if(checkBeetdle is None):
            await ctx.respond("You don't have a game currently in progress.", ephemeral=True)
            return
        
        if(checkBeetdle["daily"]):
            emb_title = "[Daily Beetdle] Guesses Reminder"
        else:
            emb_title = "[Non-Daily Beetdle] Guesses Reminder"

        embed = discord.Embed(title=emb_title,
                      description="",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.add_field(name="Here are your previous guesses:",
                        value=checkBeetdle["guesses_print"],
                        inline=False)

        embed.set_footer(text="Beetdle",
                         icon_url="https://png.pngtree.com/png-vector/20220603/ourmid/pngtree-a-letter-b-for-beetle-chitinous-alphabet-capitalized-vector-png-image_36940140.png")

        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions(), ephemeral=True)


def setup(bot):
    bot.add_cog(Beetdle(bot))



