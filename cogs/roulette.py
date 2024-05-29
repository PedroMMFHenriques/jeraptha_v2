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
rouletteGameCol = myDB["RouletteGame"] #ONLY 1 GAME AT A TIME IN THE GUILD
rouletteUserCol = myDB["RouletteUser"]

#AdminRole = global_json["ROLES"]["ADMIN_ROLE"]
#WagerRole = global_json["ROLES"]["WAGER_ROLE"]

class Roulette(commands.Cog):
    """
    Start or bet on a roulette game.
    """
        
    def __init__(self, bot):
        self.bot = bot
    
    roulette = discord.SlashCommandGroup("roulette", "Roulette related commands.")

    @staticmethod
    def find_index(lst, key, value):
        for i, dic in enumerate(lst):
            if dic[key] == value:
                return i
        return -1
    
    # ROULETTE START
    @roulette.command(name="start", description="Start a game of roulette.")
    @discord.option("betting_time", description="Duration of the betting time in seconds (max 120).", required=False, default=30)
    async def start(self, ctx: discord.ApplicationContext, betting_time: int):
        rouletteGameCheck = rouletteGameCol.find_one({"guild_id": ctx.guild.id},{"_id": 0, "running": 1})
        if(rouletteGameCheck is None):
            rouletteGameCol.insert_one({"guild_id": ctx.guild.id, "author_id": ctx.author.id, "running": True, "rolling": False})

        elif(rouletteGameCheck["running"]):
            await ctx.respond("A roulette game is already running!", ephemeral=True)
            return
        
        if(betting_time < 0):
            await ctx.respond("I can't travel back in time!", ephemeral=True)
            return

        if(betting_time > 120):
            await ctx.respond("Max betting time is 120 seconds!", ephemeral=True)
            return

        end_betting_time = betting_time + math.floor(time.time())


        myQuery= {"guild_id": ctx.guild.id}
        newValues = {'$set': {"author_id": ctx.author.id, "running": True, "rolling": False, "end_betting": end_betting_time}}
        rouletteGameCol.update_one(myQuery, newValues)

        embed = discord.Embed(title="Roulette Started!",
                      description="<@" + str(ctx.author.id) + "> just started a roulette!\nBetting will end <t:" + str(end_betting_time) + ":R>!\nDo '/roulette bet' to join.",
                      colour=0x009900,
                      timestamp=datetime.now())

        file = discord.File("images/roulette/roulette_info.png", filename="roulette_info.png")
        embed.set_image(url="attachment://roulette_info.png")

        embed.set_footer(text="Roulette",
                         icon_url="https://www.pamp.com/sites/pamp/files/2023-02/roulette_rev.png")

        await ctx.respond(embed=embed, file=file, allowed_mentions=discord.AllowedMentions())

        # Waiting for bets
        await asyncio.sleep(betting_time)

        # Close bets
        myQuery= {"guild_id": ctx.guild.id}
        newValues = {'$set': {"running": True, "rolling": True}}
        rouletteGameCol.update_one(myQuery, newValues)
        
        winning_number = random.SystemRandom().randint(0, 36)

        with open("images/roulette/roulette_" + str(winning_number) + ".gif", 'rb') as f:
                picture = discord.File(f)
                await ctx.send(file=picture)
        
        # Suspense
        await asyncio.sleep(8)

        # Award winners (if any)
        bets_check = rouletteUserCol.find({"guild_id": ctx.guild.id},{"_id": 0, "member_id": 1, "bet": 1, "bet_numbers": 1})

        bettors_list = []
        bets_list = []
        for bet in bets_check:
            bettors_list.append(bet["member_id"])
            bets_list.append(bet)
        bettors_list = list(dict.fromkeys(bettors_list)) # Get non-duplicate bettors

        winners_list = []
        for bettor in bettors_list:
            winners_list.append({"id": bettor, "winnings": 0})

        for bet in bets_list:
            number_list = bet["bet_numbers"].split(",")

            for number in number_list:
                if(int(number) == winning_number):
                    idx = self.find_index(winners_list, "id", bet["member_id"])
                    winners_list[idx]["winnings"] += bet["bet"] * 36 / len(number_list)
                    break

        winnings_embed = ""
        for winner in winners_list:
            if(winner["winnings"] > 0):
                myQuery= {"member_id": int(winner["id"]), "guild_id": ctx.guild.id}
                newValues = {'$inc': {'coins': math.floor(winner["winnings"])}}
                usersCol.update_one(myQuery, newValues)

                winnings_embed += "<@" + str(winner["id"]) + "> won **" + str(math.floor(winner["winnings"])) + "**<:beets:1245409413284499587>!\n"
            
        if(winnings_embed == ""): winning_msg = "Nobody won, suckers!"
        else: winning_msg = "Here are the winners, congrats!"

        if(winning_number == 0): winning_color = " (Green)"
        elif(winning_number in [1,3,5,7,9,12,14,15,16,18,19,21,23,25,27,30,34,36]): winning_color = " (Black)"
        else: winning_color = " (Red)"


        # Embed
        embed = discord.Embed(title="Roulette Ended!",
                      description="Winning number: **" + str(winning_number) + winning_color + "**\n",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.add_field(name=winning_msg,
                        value=winnings_embed,
                        inline=False)

        embed.set_footer(text="Roulette",
                         icon_url="https://www.pamp.com/sites/pamp/files/2023-02/roulette_rev.png")

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions())


        # Reset vars
        myQuery= {"guild_id": ctx.guild.id}
        newValues = {'$set': {"running": False, "rolling": False}}
        rouletteGameCol.update_one(myQuery, newValues)

        rouletteUserCol.drop()



    # Helper functions for /roulette bet
    async def betOptionAutocomplete(ctx: discord.AutocompleteContext):
        option = ctx.options["option"]
        if option == "Color":
            return ["Red", "Black"]
        
        elif option ==  "Parity":
            return ["Odd", "Even"]
        
        elif option ==  "Half":
            return ["1st Half", "2nd Half"]
        
        elif option ==  "Dozen":
            return ["1st Dozen", "2nd Dozen", "3rd Dozen"]
        
        elif option ==  "Line":
            return ["1st Line", "2nd Line", "3rd Line"]
        
        elif option ==  "Numbers":
            return ["[DONT CLICK] List numbers 0-36 separated by ','. Example: 0,1,5,10,36"]

        else:
            return ["OOPS"]
            

    @staticmethod
    def getNumberString(self, sub_option):
        if sub_option == "Black":
            return "1,3,5,7,9,12,14,15,16,18,19,21,23,25,27,30,34,36"
        
        elif sub_option == "Red":
            return "2,4,6,8,10,11,13,17,20,22,24,26,28,29,31,32,33,35"
        
        elif sub_option == "Odd":
            return "1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35"
        
        elif sub_option == "Even":
            return "2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36"
        
        elif sub_option == "1st Half":
            return "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18"
        
        elif sub_option == "2nd Half":
            return "19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36"
        
        elif sub_option == "1st Dozen":
            return "1,2,3,4,5,6,7,8,9,10,11,12"
        
        elif sub_option == "2nd Dozen":
            return "13,14,15,16,17,18,19,20,21,22,23,24"
        
        elif sub_option == "3rd Dozen":
            return "25,26,27,28,29,30,31,32,33,34,35,36"
        
        elif sub_option == "1st Line":
            return "1,4,7,10,13,16,19,22,25,28,31,34"
        
        elif sub_option == "2nd Line":
            return "2,5,8,11,14,17,20,23,26,29,32,35"
        
        elif sub_option == "3rd Line":
            return "3,6,9,12,15,18,21,24,27,30,33,36"
        
        elif sub_option == "[DONT CLICK] List numbers 0-36 separated by ','. Example: 0,1,5,10,36":
            return "NUMBER_MISTAKE"
        
        else:
            return "MISTAKE"
    
    @staticmethod
    def checkNumbers(self, list_numbers):
        number_list = list_numbers.split(",")

        if(len(number_list) != len(set(number_list))):
            return False

        for number in number_list:
            try:
                if(int(number) < 0 or int(number) > 36): return False
            except:
                return False
        return True

    # ROULETTE BET
    @roulette.command(name="bet", description="Bet in the roulette game.")
    @discord.option("amount", description="Bet amount.", required=True)
    @discord.option("option", description="Choose what option to bet on.", required=True, choices=['Color', 'Parity', 'Half', 'Dozen', 'Line', 'Numbers'])
    @discord.option("sub_option", description="Specify the option.", required=True, autocomplete=discord.utils.basic_autocomplete(betOptionAutocomplete))
    async def bet(self, ctx: discord.ApplicationContext, amount: int, option: str, sub_option: str):
        rouletteGameCheck = rouletteGameCol.find_one({"guild_id": ctx.guild.id},{"_id": 0, "running": 1, "rolling": 1})
        if(rouletteGameCheck is None):
            await ctx.respond("Start a roulette game first with '/roulette start'.", ephemeral=True)
            return

        if(rouletteGameCheck["running"] == False):
            await ctx.respond("Start a roulette game first with '/roulette start'.", ephemeral=True)
            return
        
        if(rouletteGameCheck["rolling"] == True):
            await ctx.respond("Too late! You have to wait for the previous game to end.", ephemeral=True)
            return
        
        if(amount <= 0):
            await ctx.respond("<@" + str(ctx.author.id) + "> tried to cheat, what a clown! 🤡")
            try:
                await ctx.author.edit(nick=ctx.author.display_name + " 🤡", reason="Tried to cheat Jeraptha")
            except:
                pass
            return


        # Check number list
        numbers_str = self.getNumberString(self, sub_option=sub_option)
        if(numbers_str == "MISTAKE" and option != "Numbers"): # Wrote something on sub_option instead of choosing
            await ctx.respond("Invalid sub option!", ephemeral=True)
            return
        elif(numbers_str == "NUMBER_MISTAKE"): # Clicked the sub_option instead of writing the number list
            await ctx.respond("Don't choose the sub_option, just write the number list!", ephemeral=True)
            return
        elif(option == "Numbers"):
            if(self.checkNumbers(self, list_numbers=sub_option)): # Valid number list
                numbers_str = sub_option
            else:
                await ctx.respond("Invalid number list! Numbers 0-36 separated by ','. Example: 0,1,5,10,36", ephemeral=True)
                return

        print_msg = sub_option

        # Check wallet
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(userCheck is None): 
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        if(userCheck["coins"] < amount): 
            await ctx.respond("You don't have enough <:beets:1245409413284499587>, scrub!", ephemeral=True)
            return
        
        # Remove from wallet
        remove_coins = 0 - amount
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)
        
        rouletteUserCol.insert_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "bet": int(amount), "bet_numbers": numbers_str})

        await ctx.respond("[Roulette] <@" + str(ctx.author.id) + "> bet on **" + print_msg + "** with **" + str(amount) + "**<:beets:1245409413284499587>!")


    #roulette cancel ?????????????????????????????????????????????????????
    """@wager.command(name="cancel", description="Cancel a wager.")
    @discord.option("wager_id", description="ID of the wager.", required=True)
    async def cancel(self, ctx: discord.ApplicationContext, wager_id: int):

        # Checks
        wagerCheck = wagersCol.find_one({"_id": wager_id},{"_id": 0, "title": 1, "author_id": 1, "settled": 1, "canceled": 1, "option_a": 1, "option_b": 1, "option_c": 1, "option_d": 1})
        
        if(wagerCheck is None): 
            await ctx.respond("That wager doesn't exist!", ephemeral=True)
            return
        
        elif(wagerCheck["canceled"] == True): 
            await ctx.respond("That wager has been canceled!", ephemeral=True)
            return
        
        elif(wagerCheck["settled"] == True): 
            await ctx.respond("That wager was already settled!", ephemeral=True)
            return

        role = discord.utils.get(ctx.author.roles, name=AdminRole)
        if(role is None and wagerCheck["author_id"] != ctx.author.id):
            await ctx.respond("You didn't start this bet, so you can't cancel!", ephemeral=True)
            return


        # Cancel and return bets
        myQuery= {"_id": wager_id}
        newValues = {'$set': {"canceled": True,}}
        wagersCol.update_one(myQuery, newValues)
        
        wagersSub_bettors = wagersSubCol.find({"wager_id": wager_id},{"_id": 0, "member_id": 1, "bet_option": 1, "total_bet": 1})

        for bettor in wagersSub_bettors:
            myQuery= {"member_id": int(bettor["member_id"]), "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': bettor["total_bet"]}}
            usersCol.update_one(myQuery, newValues)

        # Embed
        wagerRoleId = discord.utils.get(ctx.guild.roles, name=WagerRole).id
        embed = discord.Embed(title="Bet Canceled: " + wagerCheck["title"],
                      description="<@&" + str(wagerRoleId) + ">\n<@" + str(ctx.author.id) + "> canceled the bet!\nThe <:beets:1245409413284499587> have been returned.",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.set_footer(text="Wager ID: " + str(wager_id),
                        icon_url="https://toppng.com/uploads/thumbnail/hands-holding-playing-cards-royalty-free-vector-clip-hand-holding-playing-cards-clipart-11563240429mbkjvlaujb.png")

        await ctx.respond(content="<@&" + str(wagerRoleId) + ">\n", embed=embed, allowed_mentions=discord.AllowedMentions())"""


def setup(bot):
    bot.add_cog(Roulette(bot))



