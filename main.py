# source bot_env/bin/activate

import discord
import os # default module
from dotenv import load_dotenv

load_dotenv() # load all the variables from the env file
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

# Meter num cog de admin + deixar apenas admins usarem +  apenas admins verem (server settings -> integrations -> bot -> escolher role)
@bot.command(hidden=True)
#@commands.has_role("RoleName")
async def reload(ctx):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.unload_extension(f"cogs.{filename[:-3]}")
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f'{filename} successfully re-loaded')
    await ctx.respond('Extensions reloaded!', ephemeral=True)

for filename in os.listdir('./cogs'):
      if filename.endswith('.py'):
            bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(os.getenv('TOKEN')) # run the bot with the token