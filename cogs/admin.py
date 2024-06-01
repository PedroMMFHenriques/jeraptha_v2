import os
import discord
from discord.ext import commands

import pymongo

from datetime import datetime

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
rewardsCol = myDB[db["REWARDS_COL"]]

AdminRole = global_json["ROLES"]["ADMIN_ROLE"]

global_vars = global_json["VARS"]


class Admin(commands.Cog):
    """
    Admin commands.
    """
        
    def __init__(self, bot):
        self.bot = bot
    
    # RELOAD
    @discord.slash_command(name="reload", description="[ADMIN] Reload extensions.", hidden=True)
    async def reload(self, ctx: discord.ApplicationContext):
        role = discord.utils.get(ctx.author.roles, name=AdminRole) #Check if user has the correct role
        if role is None:
            await ctx.respond("You don't have the necessary role!", ephemeral=True)
            return
        
        else:
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    self.bot.unload_extension(f"cogs.{filename[:-3]}")
                    self.bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f'{filename} successfully re-loaded')
            await ctx.respond('Extensions reloaded!', ephemeral=True)

    
    # SET WALLET
    @discord.command(name="set_wallet", description="[ADMIN] Set a user's wallet.")
    @discord.option("user", description="@ the target user.", required=True)
    @discord.option("new_balance", description="Choose their new balance.", required=True)
    async def set_wallet(self, ctx: discord.ApplicationContext, user: str, new_balance: int):

        try:
            user_change = user.split("@")[1][:-1]
            user_change = ctx.guild.get_member(int(user_change))
        except:
            await ctx.respond("Wrong user argument! Make sure you @ an user.", ephemeral=True)
            return

        if user_change.bot:
            await ctx.respond("Can't change a bot's wallet!", ephemeral=True)
            return
        
        if(new_balance < 0):
            await ctx.respond("The balance can't be negative!", ephemeral=True)
            return
        
        myQuery= {"member_id": user_change.id, "guild_id": ctx.guild.id}
        newValues = {'$set': {'coins': int(new_balance)}}
        usersCol.update_one(myQuery, newValues)

        await ctx.respond("You set " + user + "'s balance to " + str(new_balance) + " <:beets:1245409413284499587>!", ephemeral=True)


    # UNMUTE USERS WHEN JOINING A VOICE CHANNEL
    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after): # this is called when a member changes voice state
        if(before.channel is None and after.mute == True): # if member enters a voice channel and is muted
            await member.edit(mute=False)


    # INIT NEW USER
    @commands.Cog.listener() 
    async def on_member_join(self, member): # this is called when a member joins the server
        usersCol.update_one(
            {
                "member_id": member.id, "guild_id": member.guild.id
            }, 
            {
                "$setOnInsert": {"member_id": member.id, "guild_id": member.guild.id, "coins": global_vars["INIT_COINS"], "last_daily": datetime(2000, 1, 1), 
                                 "last_punish": datetime(2000, 1, 1), "coins_bet": 0, "earned_bet": 0, "total_earned": 0, "wagers_won": 0}
            },
            upsert = True
        )
        rewardsCol.update_one(
                    {
                        "member_id": member.id, "guild_id": member.guild.id
                    }, 
                    {
                        "$setOnInsert": {"member_id": member.id, "guild_id": member.guild.id, "daily_boost_tier": "TIER_0", "daily_crit_tier": "TIER_0"}
                    },
                    upsert = True
                )


def setup(bot):
    bot.add_cog(Admin(bot))


