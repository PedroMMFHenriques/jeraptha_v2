import os
import discord
from discord.ext import commands

import pymongo

# Setup database
myClient = pymongo.MongoClient(os.getenv("CLIENT"))
myDB = myClient[os.getenv("DB")]
usersCol = myDB[os.getenv("USERS_COL")]

AdminRole = os.getenv("ADMIN_ROLE")


async def get_all_members(ctx: discord.AutocompleteContext):
        members_list = await ctx.interaction.guild.fetch_members(limit=100).flatten()

        all_members_list = []
        for member in members_list:
            if not member.bot:
                all_members_list.append(member.name)

        return sorted([i for i in all_members_list if i.startswith(ctx.value.lower())])


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="reload", description="[ADMIN] Reload extensions.", hidden=True)
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

    
    # RENAME
    @discord.command(name="set_wallet", description="[ADMIN] Set a user's wallet.")
    @discord.option("user", description="Choose what user to target.", required=True, autocomplete=get_all_members)
    @discord.option("new_balance", description="Choose their new balance.", required=True)
    async def set_wallet(self, ctx: discord.ApplicationContext, user: str, new_balance: int):
        user_change = discord.utils.get(ctx.guild.members, name=user)
        
        myQuery= {"member_id": user_change.id, "guild_id": ctx.guild.id}
        newValues = {'$set': {'coins': int(new_balance)}}
        usersCol.update_one(myQuery, newValues)

        await ctx.respond("You set " + user + "'s balance to " + str(new_balance) + " coins!", ephemeral=True)



def setup(bot):
    bot.add_cog(Admin(bot))



