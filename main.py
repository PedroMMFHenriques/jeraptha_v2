# source bot_env/bin/activate

import os
import discord
from dotenv import load_dotenv

import datetime

import pymongo

load_dotenv() # Load vars

# Init vars
init_coins = os.getenv("INIT_COINS")

# Setup database
myClient = pymongo.MongoClient(os.getenv("CLIENT"))
myDB = myClient[os.getenv("DB")]
usersCol = myDB[os.getenv("USERS_COL")]


bot = discord.Bot(intents = discord.Intents.all())
@bot.event
async def on_ready():
    setup_db(bot)
    print(f"{bot.user} is ready and online!")
    await bot.change_presence(activity=discord.CustomActivity(name="Gambling 🎲"))

# Check for new users and add to database
def setup_db(bot):
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:
                usersCol.update_one(
                    {
                        "member_id": member.id, "guild_id": guild.id
                    }, 
                    {
                        "$setOnInsert": {"member_id": member.id, "guild_id": guild.id, "coins": int(init_coins), "last_daily": datetime.datetime(2000, 1, 1)}
                    },
                    upsert = True
                )

    """for x in usersCol.find({},{ "_id": 1, "member_id": 1, "guild_id": 1, "coins": 1, "last_daily": 1 }):
        print(x)"""
     
# Load cogs
for filename in os.listdir('./cogs'):
      if filename.endswith('.py'):
            bot.load_extension(f"cogs.{filename[:-3]}")


bot.run(os.getenv("TOKEN")) #Run the bot