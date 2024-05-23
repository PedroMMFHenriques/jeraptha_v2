# source bot_env/bin/activate

# await asyncio.sleep(10)
import discord
import os
from dotenv import load_dotenv

load_dotenv() #Load the token
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

for filename in os.listdir('./cogs'):
      if filename.endswith('.py'):
            bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(os.getenv('TOKEN')) #Run the bot