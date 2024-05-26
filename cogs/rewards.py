import os
import discord
from discord.ext import commands

import pymongo

from datetime import datetime, timedelta, date

init_coins = os.getenv("INIT_COINS")

myClient = pymongo.MongoClient(os.getenv("CLIENT"))
myDB = myClient[os.getenv("DB")]
usersCol = myDB[os.getenv("USERS_COL")]

reason = "Jeraptha punishment"
rename_cost = 1000


async def get_all_members(ctx: discord.AutocompleteContext):
        members_list = await ctx.interaction.guild.fetch_members(limit=100).flatten()

        all_members_list = []
        for member in members_list:
            if not member.bot:
                all_members_list.append(member.name + "#" + member.discriminator)

        return sorted([i for i in all_members_list if i.startswith(ctx.value.lower())])



class Rewards(commands.Cog): 
    def __init__(self, bot): 
        self.bot = bot

    """# RENAME
    @discord.command(name="rename", description="Rename an user. Costs " + str(rename_cost) + " coins.")
    @discord.option("user", description="Choose what user to target.", required=True, autocomplete=discord.utils.basic_autocomplete(get_all_members))
    @discord.option("new_nick", description="Choose the new nick for the user.", required=True)
    async def rename(self, ctx: discord.ApplicationContext, user: str, new_nick: str):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(userCheck["coins"] < rename_cost): 
            await ctx.respond("You don't have enough coins, scrub!", ephemeral=True)
            return
        
        remove_coins = 0 - rename_cost
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)
        
        user_split = user.split("#")
        user_change = discord.utils.get(ctx.guild.members, name=user_split[0], discriminator=user_split[1])

        await discord.user_change.edit(nick=new_nick, reason=reason)

        await ctx.respond("You changed " + user + "'s nick!", ephemeral=True)"""



def setup(bot):
    bot.add_cog(Rewards(bot))



