import os
import math
import discord
from discord.ext import commands

import pymongo

from datetime import datetime, timedelta, date

init_coins = os.getenv("INIT_COINS")
daily_coins = os.getenv("DAILY_COINS")

myClient = pymongo.MongoClient(os.getenv("CLIENT"))
myDB = myClient[os.getenv("DB")]
usersCol = myDB[os.getenv("USERS_COL")]

class Economy(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot


    # WALLET
    @discord.slash_command(name="wallet", description="Check your wallet.")
    async def wallet(self, ctx: discord.ApplicationContext):
        myWallet = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})["coins"]
        await ctx.respond(f"<@{ctx.author.id}> has {myWallet} coins.")


    # DAILY
    @discord.slash_command(name="daily", description="Get your free daily reward!")
    async def daily(self, ctx: discord.ApplicationContext):
        myLastDaily = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "last_daily": 1})["last_daily"]

        if(date.today() >= myLastDaily.date() + timedelta(days=1)):
            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {"$set": {"last_daily": datetime.now()},'$inc': {'coins': int(daily_coins)}}
            usersCol.update_one(myQuery, newValues)

            myWallet = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})["coins"]
            await ctx.respond(f"<@{ctx.author.id}> used daily and got {int(daily_coins)} coins, totalling {myWallet}.")
        
        else:
            timeLeft = (datetime.combine(date.today() + timedelta(days=1), datetime.min.time()) - datetime.now())
            hoursLeft = math.floor(timeLeft.seconds/3600)
            minutesLeft = math.floor((timeLeft.seconds-hoursLeft*3600)/60)
            secondsLeft = timeLeft.seconds - hoursLeft*3600 - minutesLeft*60
            await ctx.respond(f"You already used /daily today! Time left: {hoursLeft}h:{minutesLeft}m:{secondsLeft}s.", ephemeral=True)
    

    # LEADERBOARD
    @discord.slash_command(name="leaderboard", description="Check coins leaderboard.")
    async def leaderboard(self, ctx: discord.ApplicationContext):
        myLeaderboard = usersCol.find({"guild_id": ctx.guild.id},{"member_id": 1, "coins": 1}).sort("coins", -1)
        
        # Get leaderboard
        embedString = ""
        for user in myLeaderboard:
            user_name = self.bot.get_user(user["member_id"]).name
            user_coins = user["coins"]
            embedString += user_name + ": " + user_coins + "\n"

        # Generate embed
        embed = discord.Embed(title="Coins Leaderboard",
                      description="Check out the richest dudes!",
                      colour=0x009900)
        
        embed.add_field(name="Most Coins:",
                        value=embedString,
                        inline=False)

        await ctx.send(embed=embed)


    # INIT NEW USER
    @commands.Cog.listener() 
    async def on_member_join(self, member): # this is called when a member joins the server
        usersCol.update_one(
            {
                "member_id": member.id, "guild_id": member.guild.id
            }, 
            {
                "$setOnInsert": {"member_id": member.id, "guild_id": member.guild.id, "coins": init_coins, "last_daily": datetime.datetime(2000, 1, 1)}
            },
            upsert = True
        )
        await member.send("Welcome to the server!")

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Economy(bot)) # add the cog to the bot



