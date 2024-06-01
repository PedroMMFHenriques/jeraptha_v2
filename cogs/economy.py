import os
import math
import discord
from discord.ext import commands

import random

import numpy as np

import pymongo

from datetime import datetime, timedelta, date

import json
global_json = json.load(open('global.json'))

global_vars = global_json["VARS"]

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
beetdleCol = myDB[db["BEETDLE_COL"]]

class Economy(commands.Cog):
    """
    Check wallets and daily rewards.
    """
    def __init__(self, bot): 
        self.bot = bot

    # WALLET
    @discord.slash_command(name="wallet", description="Check your wallet.")
    async def wallet(self, ctx: discord.ApplicationContext):
        myWallet = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})["coins"]
        if(myWallet is None): await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)

        await ctx.respond(f"You have {myWallet}<:beets:1245409413284499587>.", ephemeral=True)


    # DAILY
    @discord.slash_command(name="daily", description="Get your free daily reward!")
    async def daily(self, ctx: discord.ApplicationContext):
        checkUser = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1, "last_daily": 1})
        if(checkUser is None): await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)

        # Check didn't do /daily today
        if(date.today() >= checkUser["last_daily"].date() + timedelta(days=1)):
            daily_coins = np.random.normal(loc=global_vars["DAILY_MEAN"], scale=global_vars["DAILY_STD"], size = (1))[0]

            daily_coins = daily_coins
            extra_msg = ""
            if(random.SystemRandom().randint(1, 101) >= 96): 
                daily_coins = daily_coins*3
                extra_msg = "a **CRIT**, winning "
            elif(random.SystemRandom().randint(1, 101) <= 5 and checkUser["coins"] > 1000):
                daily_coins = daily_coins/3
                extra_msg = "a **CRIT FAILURE**, winning only "
            
            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {"$set": {"last_daily": datetime.now()},'$inc': {'coins': int(daily_coins), 'total_earned': int(daily_coins)}}
            usersCol.update_one(myQuery, newValues)

            myWallet = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})["coins"]
            if(myWallet is None): await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)

            await ctx.respond(f"[Daily] <@{ctx.author.id}> used daily and got {extra_msg}{int(daily_coins)}<:beets:1245409413284499587>, totalling {myWallet}.")
        
        else:
            timeLeft = (datetime.combine(date.today() + timedelta(days=1), datetime.min.time()) - datetime.now())
            hoursLeft = math.floor(timeLeft.seconds/3600)
            minutesLeft = math.floor((timeLeft.seconds-hoursLeft*3600)/60)
            secondsLeft = timeLeft.seconds - hoursLeft*3600 - minutesLeft*60
            await ctx.respond(f"You already used /daily today! Time left: {hoursLeft}h:{minutesLeft}m:{secondsLeft}s.", ephemeral=True)
    

    # LEADERBOARD
    @discord.slash_command(name="leaderboard", description="Check leaderboards.")
    @discord.option("option", description="Choose what leaderboard to check.", required=True, choices=['Wallet', 'Total Earned', 'Total Bet', 'Bet Net Result'])
    async def leaderboard(self, ctx: discord.ApplicationContext, option: str):
        if(option == "Wallet" or option == "Total Earned" or option == "Total Bet" or option == "Bet Net Result"): 
            if(option == "Wallet"):
                check_value = "coins"
                embed_title = "Check out the richest dudes!"
                embed_subtitle = "Most beets <:beets:1245409413284499587>:"
                myLeaderboard = usersCol.find({"guild_id": ctx.guild.id},{"member_id": 1, check_value: 1}).sort(check_value, -1)
            
            elif(option == "Total Earned"):
                check_value = "total_earned"
                embed_title = "Check out the biggest winners!"
                embed_subtitle = "Most beets <:beets:1245409413284499587> earned:"
                myLeaderboard = usersCol.find({"guild_id": ctx.guild.id},{"member_id": 1, check_value: 1}).sort(check_value, -1)
    
            elif(option == "Total Bet"):
                check_value = "coins_bet"
                embed_title = "Check out the problem gamblers!"
                embed_subtitle = "Most beets <:beets:1245409413284499587> bet:"
                myLeaderboard = usersCol.find({"guild_id": ctx.guild.id},{"member_id": 1, check_value: 1}).sort(check_value, -1)
            
            elif(option == "Bet Net Result"):
                check_value = "bet_net"
                embed_title = "Check out the least losers!"
                embed_subtitle = "Best net bet result:"
                userList = usersCol.find({"guild_id": ctx.guild.id},{"member_id": 1, "earned_bet": 1, "coins_bet": 1})
                
                myLeaderboard = []
                for user in userList:
                    myLeaderboard.append({"member_id": user["member_id"], check_value: int(user["earned_bet"] - user["coins_bet"])})
                
                myLeaderboard = sorted(myLeaderboard, key=lambda d: d[check_value], reverse=True)


            if(myLeaderboard is None):
                await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)

            # Get leaderboard
            embedString = ""
            for user in myLeaderboard:
                user_name = str(user["member_id"])
                user_value = str(user[check_value])
                embedString += "<@" + user_name + ">: " + user_value + "\n"

                
        # Generate embed
        embed = discord.Embed(title= option + " Leaderboard",
                              description=embed_title,
                      colour=0x009900)
        
        """embed.set_author(name="Leaderboard",
                        icon_url="https://cdn3d.iconscout.com/3d/premium/thumb/wallet-with-money-5200708-4357253.png")"""
        
        
        embed.add_field(name=embed_subtitle,
                        value=embedString,
                        inline=False)

        await ctx.respond(embed=embed)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Economy(bot)) # add the cog to the bot



