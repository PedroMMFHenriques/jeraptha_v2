import os
import discord
from discord.ext import commands

import pymongo

# Setup database
myClient = pymongo.MongoClient(os.getenv("CLIENT"))
myDB = myClient[os.getenv("DB")]
usersCol = myDB[os.getenv("USERS_COL")]
wagersCol = myDB[os.getenv("WAGERS_COL")]

AdminRole = os.getenv("ADMIN_ROLE")

class Wager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """role = discord.utils.get(ctx.author.roles, name=AdminRole) #Check if user has the correct role
        if role is None:
            await ctx.respond("You don't have the necessary role!", ephemeral=True)"""
    
    """wager = discord.SlashCommandGroup("wager", "Wager related commands.")

    #DISPLAY UNIQUE ID + nome da wager, para saber qual dar update e qual dar settle
    #SÓ MOSTRAR AS ABERTAS

    #bet #deixar varias vezes
    #update? #só admin ou quem criou
    #settle #só admin ou quem criou
    #cancel
    #history?
    
    @wager.slash_command(name="start", description="Start wager.")
    @discord.option("title", description="Title of the wager.", required=True, default='')
    @discord.option("option_a", description="Description of the first option.", required=True, default='')
    @discord.option("option_b", description="Description of the second option.", required=True, default='')
    @discord.option("option_c", description="Description of the third option.", required=True, default='')
    @discord.option("option_d", description="Description of the fourth option.", required=True, default='')
    @discord.option("duration_seconds", description="Duration of the wager in seconds.", required=False, default=0)
    @discord.option("duration_minutes", description="Duration of the wager in minutes.", required=False, default=10)
    @discord.option("duration_hours", description="Duration of the wager in hours.", required=False, default=0)
    async def start(self, ctx: discord.ApplicationContext, title: str, description: str, duration_seconds: int, duration_minutes: int, duration_hours: int):
        # wager id, guild id, title, descrição, quem criou, pool total, pool opção a, pool opção b, pool opção c, pool opção d, quem votou na opção a, quem votou na opção b, quem votou na opção c, quem votou na opção d 
        # ou então fazer sub table com id da wager, o id de cada membro + guild, em qual apostou e quanto -> NÃO DEIXAR APOSTAR EM OPÇÕES DIFERENTES
        wagersCol.update_one(
                    {
                        "member_id": member.id, "guild_id": guild.id
                    }, 
                    {
                        "$setOnInsert": {"member_id": member.id, "guild_id": guild.id, "coins": int(init_coins), "last_daily": datetime.datetime(2000, 1, 1)}
                    },
                    upsert = True
                )
        
        await ctx.respond('Extensions reloaded!')"""
    

    
    """@discord.slash_command(name="add_coins", description="Adds coins.", hidden=True)
    async def add_coins(self, ctx: discord.ApplicationContext, n_coins: int):
        role = discord.utils.get(ctx.author.roles, name=AdminRole) #Check if user has the correct role
        if role is None:
            await ctx.respond("You don't have the necessary role!", ephemeral=True)
        
        else:
            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': n_coins}}

            usersCol.update_one(myQuery, newValues)
            await ctx.respond('Coins added!', ephemeral=True)"""



def setup(bot):
    bot.add_cog(Wager(bot))



