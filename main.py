# source bot_env/bin/activate

import os
import discord
from discord.ext import commands

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


bot = discord.Bot(intents = discord.Intents.all(), command_prefix='!')
@bot.event
async def on_ready():
    setup_db(bot)
    print(f"{bot.user} is ready and online!")
    await bot.change_presence(activity=discord.CustomActivity(name="Gambling 🎲"))


@bot.slash_command(name="help", description="Get info about the commands.")
@discord.option("command", description="Get info on a particular command.", choices=[x.name for x in bot.commands], required=False)
async def help(ctx: discord.ApplicationContext, command: str):
    help_embed = discord.Embed(title="Commands Info") 
    command_names_list = [x.name for x in bot.commands]
    if not command:
        help_embed.add_field(
            name="List of supported commands:",
            value="\n".join([". /"+x.name for x in enumerate(bot.commands)]),
            inline=False
        )
        help_embed.add_field(
        name="Details",
        value="Type `/help <command name>` for more details about each command.",
        inline=False
    )

    elif command in command_names_list:
        help_embed.add_field(
        name=command,
        value=bot.get_command(command).description
    )
    else:
        help_embed.add_field(
        name="Oh, no!",
        value="I didn't find command :("
    )
    await ctx.respond(embed=help_embed, ephemeral=True)


class SupremeHelpCommand(commands.HelpCommand):
    def get_command_signature(self, command):
        return '%s%s %s' % (self.context.clean_prefix, command.qualified_name, command.signature)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help", color=discord.Color.blurple())
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            if command_signatures := [
                self.get_command_signature(c) for c in filtered
            ]:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=self.get_command_signature(command) , color=discord.Color.blurple())
        if command.help:
            embed.description = command.help
        if alias := command.aliases:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_help_embed(self, title, description, commands): # a helper function to add commands to an embed
        embed = discord.Embed(title=title, description=description or "No help found...")

        if filtered_commands := await self.filter_commands(commands):
            for command in filtered_commands:
                embed.add_field(name=self.get_command_signature(command), value=command.help or "No help found...")

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        title = self.get_command_signature(group)
        await self.send_help_embed(title, group.help, group.commands)

    async def send_cog_help(self, cog):
        title = cog.qualified_name or "No"
        await self.send_help_embed(f'{title} Category', cog.description, cog.get_commands())

bot.help_command = SupremeHelpCommand()

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