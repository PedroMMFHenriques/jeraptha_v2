# source bot_env/bin/activate

import os
import discord
from dotenv import load_dotenv

from datetime import datetime

import pymongo

import json

# Load vars
global_json = json.load(open('global.json'))
load_dotenv() 

# Init vars
init_coins = global_json["VARS"]["INIT_COINS"]

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
rewardsCol = myDB[db["REWARDS_COL"]]


bot = discord.Bot(intents = discord.Intents.all())
@bot.event
async def on_ready():
    setup_db(bot)
    print(f"{bot.user} is ready and online!")
    await bot.change_presence(activity=discord.CustomActivity(name="Gambling 🎲"))



@bot.slash_command(name="help", description="This is a test")
async def help(ctx: discord.ApplicationContext, args: discord.Option(discord.SlashCommandOptionType.string, "args", required=False, default=None)): 
    help_embed = discord.Embed(title="My Bot's Help!") 
    command_names_list = [x.name for x in bot.commands]
    if not args:
        help_embed.add_field(
            name="List of supported commands:",
            value="\n".join([str(i+1)+". "+x.name for i,x in enumerate(bot.commands)]),
            inline=False
        )
        help_embed.add_field(
        name="Details",
        value="Type `.help <command name>` for more details about each command.",
        inline=False
    )

    elif args in command_names_list:
        help_embed.add_field(
        name=args,
        value=bot.get_command(args).description
    )
    else:
        help_embed.add_field(
        name="Oh, no!",
        value="I didn't find command :("
    )
    await ctx.send(embed=help_embed)


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
                        "$setOnInsert": {"member_id": member.id, "guild_id": guild.id, "coins": int(init_coins), "last_daily": datetime(2000, 1, 1)}
                    },
                    upsert = True
                )

                rewardsCol.update_one(
                    {
                        "member_id": member.id, "guild_id": guild.id
                    }, 
                    {
                        "$setOnInsert": {"member_id": member.id, "guild_id": guild.id, "daily_boost_tier": "TIER_0", "daily_crit_tier": "TIER_0"}
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