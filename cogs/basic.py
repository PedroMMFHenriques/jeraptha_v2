import discord
from discord.ext import commands

class Basic(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    @discord.slash_command(name="hello", description="Say hello to the bot")
    async def hello(self, ctx: discord.ApplicationContext):
        await ctx.respond("Hey!")

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Basic(bot)) # add the cog to the bot



