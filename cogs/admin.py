import os
import discord
from discord.ext import commands

import pymongo

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]

AdminRole = global_json["ROLES"]["ADMIN_ROLE"]


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

    

    """# SEND_FILE
    @discord.slash_command(name="send_file", description="[ADMIN] Sends file.", hidden=True)
    async def send_file(self, ctx: discord.ApplicationContext):
        role = discord.utils.get(ctx.author.roles, name=AdminRole) #Check if user has the correct role
        if role is None:
            await ctx.respond("You don't have the necessary role!", ephemeral=True)
            return
        
        else:
            with open('images/roulette/roulette_0.gif', 'rb') as f:
                picture = discord.File(f)
                await ctx.respond(file=picture)"""
    

    
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


    # BETA COMMAND REMOVE LATER
    @discord.command(name="beg", description="Ask daddy J. Pow for a small loan of a million beets.")
    async def beg(self, ctx: discord.ApplicationContext):

        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$set': {'coins': 1000000}}
        usersCol.update_one(myQuery, newValues)

        with open("images/money-printer.gif", "rb") as fh:
            file = discord.File(fh, filename="money-printer.gif")
        await ctx.respond(content="<@" + str(ctx.author.id) + "> asked daddy J. Pow for a small loan of a million <:beets:1245409413284499587>!", file=file)
    

    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after): # this is called when a member changes voice state
        print(before)
        print(after)
        if(before.channel is None and after.mute == True): # if member enters a voice channel
            print("oi mute")
            member.edit(mute=False)


def setup(bot):
    bot.add_cog(Admin(bot))



