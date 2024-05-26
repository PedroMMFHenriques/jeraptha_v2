import os
import discord
from discord.ext import commands

import pymongo

# Setup database
myClient = pymongo.MongoClient(os.getenv("CLIENT"))
myDB = myClient[os.getenv("DB")]
usersCol = myDB[os.getenv("USERS_COL")]

AdminRole = os.getenv("ADMIN_ROLE")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="reload", description="Reload extensions.", hidden=True)
    async def reload(self, ctx: discord.ApplicationContext):
        role = discord.utils.get(ctx.author.roles, name=AdminRole) #Check if user has the correct role
        if role is None:
            await ctx.respond("You don't have the necessary role!", ephemeral=True)
        
        else:
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    self.bot.unload_extension(f"cogs.{filename[:-3]}")
                    self.bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f'{filename} successfully re-loaded')
            await ctx.respond('Extensions reloaded!', ephemeral=True)



def setup(bot):
    bot.add_cog(Admin(bot))



