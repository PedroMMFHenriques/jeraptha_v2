import os
import discord
from discord.ext import commands

import pymongo

from datetime import datetime, timedelta, date

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]

reason = "Jeraptha punishment"
punishments = global_json["PUNISHMENTS"]


class Rewards(commands.Cog): 
    def __init__(self, bot): 
        self.bot = bot

    # RENAME
    @discord.command(name="rename", description="Rename an user. Costs " + str(punishments["RENAME_COST"]) + " coins.")
    @discord.option("user", description="@ the target user.", required=True)
    @discord.option("new_nick", description="Choose the new nick for the user.", required=True)
    async def rename(self, ctx: discord.ApplicationContext, user: str, new_nick: str):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(userCheck is None):
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)

        if(userCheck["coins"] < punishments["RENAME_COST"]): 
            await ctx.respond("You don't have enough coins, scrub!", ephemeral=True)
            return
        
        #Check user argument
        try:
            user_change = user.split("@")[1][:-1]
            user_change = ctx.guild.get_member(int(user_change))
        except:
            await ctx.respond("Wrong user argument! Make sure you @ an user.", ephemeral=True)
            return

        if user_change.bot:
            await ctx.respond("You can't change a bot's nickname!", ephemeral=True)
            return

        #Check perms
        try:
            await user_change.edit(nick=new_nick, reason=reason)
        except:
            await ctx.respond("You can't change " + user + "'s nickame!", ephemeral=True)
            return
        
        remove_coins = 0 - punishments["RENAME_COST"]
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)

        await ctx.respond("You changed " + user + "'s nickname!", ephemeral=True)



def setup(bot):
    bot.add_cog(Rewards(bot))



