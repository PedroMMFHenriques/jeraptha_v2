import discord
from discord.ext import commands

class Basic(commands.Cog): # create a class for our cog that inherits from commands.Cog
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    @discord.slash_command(name="hello", description="Say hello to the bot")
    async def hello(self, ctx: discord.ApplicationContext):
        await ctx.respond("Hey!")

    """@discord.slash_command(name="gtn", description="Play a Guess-the-Number game")
    async def gtn(self, ctx: discord.ApplicationContext):
        await ctx.respond('Guess a number between 1 and 10.')
        guess = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author)

        if int(guess.content) == 5:
            await ctx.send('You guessed it!')
        else:
            await ctx.send('Nope, try again.')"""

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Basic(bot)) # add the cog to the bot



