import os
import discord
from discord.ext import commands

import time, math
from datetime import datetime, timedelta, date

import pymongo

# Setup database
myClient = pymongo.MongoClient(os.getenv("CLIENT"))
myDB = myClient[os.getenv("DB")]
usersCol = myDB[os.getenv("USERS_COL")]
wagersCol = myDB["Wagers"]
wagersSubCol = myDB["WagersSub"]

AdminRole = os.getenv("ADMIN_ROLE")
WagerRole = os.getenv("WAGER_ROLE")

class Wager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    """role = discord.utils.get(ctx.author.roles, name=AdminRole) #Check if user has the correct role
        if role is None:
            await ctx.respond("You don't have the necessary role!", ephemeral=True)"""
    
    wager = discord.SlashCommandGroup("wager", "Wager related commands.")

    #DISPLAY UNIQUE ID + nome da wager, para saber qual dar update e qual dar settle
    #SÓ MOSTRAR AS ABERTAS

    #MUDAR DURATION PARA O DATATIME EM Q ACABA

    #USAR wagersSub_id = wagersSubCol.count_documents({})
    # wagersub: id sub wager, guild id, id da wager, o id membro, em qual apostou e quanto 
    # -> NÃO DEIXAR APOSTAR EM OPÇÕES DIFERENTES E TMB QUANDO ACABA O TEMPO E DEPOIS DE TER SIDO SETTLED

    #bet #deixar varias vezes
    #info: a pool de cada opção e payouts possiveis
    #settle #só admin ou quem criou
    #cancel #só admin ou quem criou
    #history?
    
    @wager.command(name="start", description="Start wager. Default duration is 10 minutes")
    @discord.option("title", description="Title of the wager.", required=True)
    @discord.option("option_a", description="Description of the first option.", required=True)
    @discord.option("option_b", description="Description of the second option.", required=True)
    @discord.option("option_c", description="Description of the third option.", required=False, default='')
    @discord.option("option_d", description="Description of the fourth option.", required=False, default='')
    @discord.option("duration_seconds", description="Duration of the wager in seconds.", required=False, default=0)
    @discord.option("duration_minutes", description="Duration of the wager in minutes.", required=False, default=0)
    @discord.option("duration_hours", description="Duration of the wager in hours.", required=False, default=0)
    async def start(self, ctx: discord.ApplicationContext, title: str, option_a: str, option_b: str, option_c: str, option_d: str, duration_seconds: int, duration_minutes: int, duration_hours: int):
        if(duration_hours == 0 and duration_minutes == 0 and duration_seconds == 0):
            duration_minutes = 10

        duration_s = duration_hours*3600 + duration_minutes*60 + duration_seconds
        end_wager = duration_s + math.floor(time.time())

        # wager: wager id, guild id, quem criou, duração, title, descrição das opções
        wager_id = wagersCol.count_documents({})
        wagersCol.insert_one({"_id": wager_id, "guild_id": ctx.guild.id, "author_id": ctx.author.id, "duration_s": duration_s, "title": title, "option_a": option_a, "option_b": option_b, "option_c": option_c, "option_d": option_d})

        wagerRoleId = discord.utils.get(ctx.guild.roles, name=WagerRole).id
        embed = discord.Embed(title=title,
                      description="<@&" + str(wagerRoleId) + ">\n<@" + str(ctx.author.id) + "> just started a wager with **ID " + str(wager_id) + "**.\nBetting will end <t:" + str(end_wager) + ":R>!",
                      colour=0x009900,
                      timestamp=datetime.now())

        option_string = "**A:** " + option_a + "\n**B:** " + option_b
        if(option_c != ""): 
            option_string += "\n**C:** " + option_c
            if(option_d != ""): option_string += "\n**D:** " + option_d
        
        embed.add_field(name="Betting options:",
                        value=option_string,
                        inline=False)

        embed.set_footer(text="Wager ID " + str(wager_id))

        await ctx.send(embed=embed)
    

    
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



