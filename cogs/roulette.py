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
rouletteGameCol = myDB["RouletteGame"] #ONLY 1 GAME AT A TIME IN THE GUILD
rouletteUserCol = myDB["RouletteUser"]

AdminRole = os.getenv("ADMIN_ROLE")
#WagerRole = os.getenv("WAGER_ROLE")

#rouletteGameCol = 

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    #roulette = discord.SlashCommandGroup("roulette", "Roulette related commands.")
    
    # roulette start
    """@roulette.command(name="start", description="Start a game of roulette.")
    @discord.option("betting_time", description="Duration of the betting time in seconds.", required=False, default=0)
    async def start(self, ctx: discord.ApplicationContext, betting_time: int):
        rouletteGameCheck = rouletteGameCol.find_one({"guild_id": ctx.guild.id},{"_id": 0, "running": 1})
        if(rouletteGameCheck["running"]):
            await ctx.respond("A roulette game is already running!", ephemeral=True)
            return
        
        if(betting_time < 0):
            await ctx.respond("I can't travel back in time!", ephemeral=True)
            return

        end_betting_time = betting_time + math.floor(time.time())

        if(rouletteGameCheck is None):
            rouletteGameCol.insert_one({"guild_id": ctx.guild.id, "author_id": ctx.author.id, "running": True, "rolling": False, "end_betting": end_betting_time})
        else:
            myQuery= {"guild_id": ctx.guild.id}
            newValues = {'$set': {"author_id": ctx.author.id, "running": True, "rolling": False, "end_betting": end_betting_time}}
            rouletteGameCol.update_one(myQuery, newValues)

        embed = discord.Embed(title="Roulette Started !",
                      description="<@" + str(ctx.author.id) + "> just started a roulette!\nBetting will end <t:" + str(end_betting_time) + ":R>!\nDo '/roulette bet' to join.",
                      colour=0x009900,
                      timestamp=datetime.now())

        file = discord.File("images/roulette/roulette_info.png", filename="roulette_info.png")
        embed.set_image(url="attachment://roulette_info.png")

        embed.set_footer(text="Roulette",
                         icon_url="https://www.pamp.com/sites/pamp/files/2023-02/roulette_rev.png")

        await ctx.respond(embed=embed, file=file, allowed_mentions=discord.AllowedMentions())"""


    #color, parity, duzia, half, numeros    #CHECK SE NÃO FEZ BET EM NENHUM NÚMERO
    # roulette bet
    """@roulette.command(name="bet", description="Bet in the roulette game.")
    @discord.option("bet_amount", description="Bet amount.", required=True)
    @discord.option("bet_option", description="Choose what option to bet on.", required=False, choices=['option_a', 'option_b', 'option_c', 'option_d'])
    async def bet(self, ctx: discord.ApplicationContext, bet_amount: int):
        rouletteGameCheck = rouletteGameCol.find_one({"guild_id": ctx.guild.id},{"_id": 0, "running": 1, "rolling": 1})
        if(rouletteGameCheck["running"] == False):
            await ctx.respond("Start a roulette game first with . '/roulette start'.", ephemeral=True)
            return
        
        if(rouletteGameCheck["rolling"] == True):
            await ctx.respond("Too late! You have to wait for the previous game to end.", ephemeral=True)
            return
        
        if(bet_amount <= 0):
            await ctx.respond("<@" + str(ctx.author.id) + "> tried to cheat, what a clown! 🤡")
            try:
                await ctx.author.edit(nick=ctx.author.display_name + " 🤡", reason="Tried to cheat Jeraptha")
            except:
                pass
            return


        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})

        if(userCheck["coins"] < bet_amount): 
            await ctx.respond("You don't have enough coins, scrub!", ephemeral=True)
            return
        
        #remove from wallet
        remove_coins = 0 - bet_amount
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)
        
        #bet_numbers convert to str of numbers separated by /
        rouletteUserCol.insert_one({"guild_id": ctx.guild.id, "member_id": ctx.author.id, "total_bet": int(bet_amount), "bet_numbers": bet_numbers_str})
        await ctx.respond("<@" + str(ctx.author.id) + "> bet on the roulette with **" + str(bet_amount) + "** coins!")"""

    #color, parity, duzia, half, numeros    
    #!!!!!!!!!!! FAZER DROP DE rouletteUserCol EM CANCEL E QND ACABA O JOGO !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    #wager settle
    """@wager.command(name="settle", description="Settle a wager.")
    @discord.option("wager_id", description="ID of the wager.", required=True)
    @discord.option("winning_option", description="What option won the bet.", required=True, choices=['option_a', 'option_b', 'option_c', 'option_d'])
    async def settle(self, ctx: discord.ApplicationContext, wager_id: int, winning_option: str):

        # Checks
        wagerCheck = wagersCol.find_one({"_id": wager_id},{"_id": 0, "title": 1, "author_id": 1, "settled": 1, "canceled": 1, "option_a": 1, "option_b": 1, "option_c": 1, "option_d": 1})
        
        if(wagerCheck is None): 
            await ctx.respond("That wager doesn't exist!", ephemeral=True)
            return
        
        elif(wagerCheck["canceled"] == True): 
            await ctx.respond("That wager has been canceled!", ephemeral=True)
            return

        elif(wagerCheck["settled"] == True): 
            await ctx.respond("That wager was already settled!", ephemeral=True)
            return

        role = discord.utils.get(ctx.author.roles, name=AdminRole)
        if(role is None and wagerCheck["author_id"] != ctx.author.id):
            await ctx.respond("You didn't start this bet, so you can't settle!", ephemeral=True)
            return

        if((wagerCheck["option_c"] == "" and winning_option == "option_c") or (wagerCheck["option_d"] == "" and winning_option == "option_d")):
            await ctx.respond("That option isn't available!", ephemeral=True)
            return


        # Settle
        myQuery= {"_id": wager_id}
        newValues = {'$set': {"settled": True, "winning_option": winning_option}}
        wagersCol.update_one(myQuery, newValues)
        
        wagersSub_bettors = wagersSubCol.find({"wager_id": wager_id},{"_id": 0, "member_id": 1, "bet_option": 1, "total_bet": 1})

        option_wager = {"option_a": 0, "option_b": 0, "option_c": 0, "option_d": 0}
        winners_list = []
        for bettor in wagersSub_bettors:
            option_wager[bettor["bet_option"]] += bettor["total_bet"]
            if(bettor["bet_option"] == winning_option): winners_list.append({"id": bettor["member_id"], "bet": bettor["total_bet"]})
        
        winning_bet = option_wager[winning_option]
        total_bet = option_wager["option_a"] + option_wager["option_b"] + option_wager["option_c"] + option_wager["option_d"] 
        winnings_embed = ""
        for winner in winners_list:
            winnings = 0.99 * winner["bet"] * total_bet / winning_bet

            myQuery= {"member_id": int(winner["id"]), "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': math.floor(winnings)}}
            usersCol.update_one(myQuery, newValues)

            winnings_embed += "<@" + str(winner["id"]) + "> won **" + str(math.floor(winnings)) + "** coins!\n"

        if(winnings_embed == ""): winning_msg = "Nobody won, suckers!"
        else: winning_msg = "Here are the winners, congrats!"

        # Embed
        wagerRoleId = discord.utils.get(ctx.guild.roles, name=WagerRole).id
        embed = discord.Embed(title="Bet Settled: " + wagerCheck["title"],
                      description="<@&" + str(wagerRoleId) + ">\nWinning option: **" + wagerCheck[winning_option] + "**\nWinning pool: **" + str(total_bet) + "** coins!",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.add_field(name=winning_msg,
                        value=winnings_embed,
                        inline=False)

        embed.set_footer(text="Wager ID: " + str(wager_id),
                        icon_url="https://toppng.com/uploads/thumbnail/hands-holding-playing-cards-royalty-free-vector-clip-hand-holding-playing-cards-clipart-11563240429mbkjvlaujb.png")

        await ctx.respond(content="<@&" + str(wagerRoleId) + ">\n", embed=embed, allowed_mentions=discord.AllowedMentions())"""



    # wager info
    """@wager.command(name="info", description="Get info on the wager.")
    @discord.option("wager_id", description="ID of the wager.", required=True)
    async def start(self, ctx: discord.ApplicationContext, wager_id: int):

        wagerCheck = wagersCol.find_one({"_id": wager_id},{"_id": 0, "title": 1, "author_id": 1, "settled": 1, "canceled": 1, "winning_option": 1, "end_wager": 1, "option_a": 1, "option_b": 1, "option_c": 1, "option_d": 1})
        
        if(wagerCheck is None): 
            await ctx.respond("That wager doesn't exist!", ephemeral=True)
            return
        
        wagersSub_bettors = wagersSubCol.find({"wager_id": wager_id},{"_id": 0, "member_id": 1, "bet_option": 1, "total_bet": 1})

        option_wager = {"option_a": 0, "option_b": 0, "option_c": 0, "option_d": 0}
        option_a_embed = ""
        option_b_embed = ""
        option_c_embed = ""
        option_d_embed = ""
        for bettor in wagersSub_bettors:
            option_wager[bettor["bet_option"]] += bettor["total_bet"]
            string_embed = "<@" + str(bettor["member_id"]) + "> bet " +  str(bettor["total_bet"]) + " coins."
            if(bettor["bet_option"] == "option_a"): option_a_embed += string_embed
            elif(bettor["bet_option"] == "option_b"): option_b_embed += string_embed
            elif(bettor["bet_option"] == "option_c"): option_c_embed += string_embed
            elif(bettor["bet_option"] == "option_d"): option_d_embed += string_embed
        
        total_bet = option_wager["option_a"] + option_wager["option_b"] + option_wager["option_c"] + option_wager["option_d"]

        if(option_wager["option_a"] == 0): option_a_odds = "N/A"
        else: option_a_odds = round(0.99 * total_bet / option_wager["option_a"], 2)

        if(option_wager["option_b"] == 0): option_b_odds = "N/A"
        else: option_b_odds = round(0.99 * total_bet / option_wager["option_b"], 2)

        if(option_wager["option_c"] == 0): option_c_odds = "N/A"
        else: option_c_odds = round(0.99 * total_bet / option_wager["option_c"], 2)

        if(option_wager["option_d"] == 0): option_d_odds = "N/A"
        else: option_d_odds = round(0.99 * total_bet / option_wager["option_d"], 2)

        description_embed = ""
        if(wagerCheck["canceled"]): description_embed = "**CANCELED**\n"
        elif(wagerCheck["settled"]): description_embed = "**SETTLED**\nWinning option: **" + wagerCheck["winning_option"] + "**\n"
        elif(wagerCheck["end_wager"] < math.floor(time.time())): description_embed = "Betting ended <t:" + str(wagerCheck["end_wager"]) + ":R>\n"
        else: description_embed = "Betting will end <t:" + str(wagerCheck["end_wager"]) + ":R>\n"
        
        description_embed += "**" + wagerCheck["option_a"] + "**: " + str(option_wager["option_a"]) + " coins, " + str(option_a_odds) + " odds\n"
        description_embed += "**" + wagerCheck["option_b"] + "**: " + str(option_wager["option_b"]) + " coins, " + str(option_b_odds) + " odds\n"
        if(wagerCheck["option_c"] != ""):
            description_embed += "**" + wagerCheck["option_c"] + "**: " + str(option_wager["option_c"]) + " coins, " + str(option_c_odds) + " odds\n"
        if(wagerCheck["option_d"] != ""):
            description_embed += "**" + wagerCheck["option_d"] + "**: " + str(option_wager["option_d"]) + " coins, " + str(option_d_odds) + " odds\n"

        embed = discord.Embed(title="Bet Info: " + wagerCheck["title"],
                      description=description_embed,
                      colour=0x009900,
                      timestamp=datetime.now())

        if(option_wager["option_a"] == 0): option_a_embed_name = "Nobody bet on **" + wagerCheck["option_a"] + "**!"
        else: option_a_embed_name = "Bettors on **" + wagerCheck["option_a"] + "**:"

        if(option_wager["option_b"] == 0): option_b_embed_name = "Nobody bet on **" + wagerCheck["option_b"] + "**!"
        else: option_b_embed_name = "Bettors on **" + wagerCheck["option_b"] + "**:"

        if(wagerCheck["option_c"] != ""):
            if(option_wager["option_c"] == 0): option_c_embed_name = "Nobody bet on **" + wagerCheck["option_c"] + "**!"
            else: option_c_embed_name = "Bettors on **" + wagerCheck["option_c"] + "**:"
        
        if(wagerCheck["option_d"] != ""):
            if(option_wager["option_d"] == 0): option_d_embed_name = "Nobody bet on **" + wagerCheck["option_d"] + "**!"
            else: option_d_embed_name = "Bettors on **" + wagerCheck["option_d"] + "**:"

        embed.add_field(name=option_a_embed_name,
                        value=option_a_embed,
                        inline=False)
        
        embed.add_field(name=option_b_embed_name,
                        value=option_b_embed,
                        inline=False)
        
        if(wagerCheck["option_c"] != ""):
            embed.add_field(name=option_c_embed_name,
                            value=option_c_embed,
                            inline=False)

        
        if(wagerCheck["option_d"] != ""):
            embed.add_field(name=option_d_embed_name,
                            value=option_d_embed,
                            inline=False)

        embed.set_footer(text="Wager ID: " + str(wager_id),
                         icon_url="https://toppng.com/uploads/thumbnail/hands-holding-playing-cards-royalty-free-vector-clip-hand-holding-playing-cards-clipart-11563240429mbkjvlaujb.png")

        await ctx.respond(embed=embed)"""



    #wager cancel
    """@wager.command(name="cancel", description="Cancel a wager.")
    @discord.option("wager_id", description="ID of the wager.", required=True)
    async def cancel(self, ctx: discord.ApplicationContext, wager_id: int):

        # Checks
        wagerCheck = wagersCol.find_one({"_id": wager_id},{"_id": 0, "title": 1, "author_id": 1, "settled": 1, "canceled": 1, "option_a": 1, "option_b": 1, "option_c": 1, "option_d": 1})
        
        if(wagerCheck is None): 
            await ctx.respond("That wager doesn't exist!", ephemeral=True)
            return
        
        elif(wagerCheck["canceled"] == True): 
            await ctx.respond("That wager has been canceled!", ephemeral=True)
            return
        
        elif(wagerCheck["settled"] == True): 
            await ctx.respond("That wager was already settled!", ephemeral=True)
            return

        role = discord.utils.get(ctx.author.roles, name=AdminRole)
        if(role is None and wagerCheck["author_id"] != ctx.author.id):
            await ctx.respond("You didn't start this bet, so you can't cancel!", ephemeral=True)
            return


        # Cancel and return bets
        myQuery= {"_id": wager_id}
        newValues = {'$set': {"canceled": True,}}
        wagersCol.update_one(myQuery, newValues)
        
        wagersSub_bettors = wagersSubCol.find({"wager_id": wager_id},{"_id": 0, "member_id": 1, "bet_option": 1, "total_bet": 1})

        for bettor in wagersSub_bettors:
            myQuery= {"member_id": int(bettor["member_id"]), "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': bettor["total_bet"]}}
            usersCol.update_one(myQuery, newValues)

        # Embed
        wagerRoleId = discord.utils.get(ctx.guild.roles, name=WagerRole).id
        embed = discord.Embed(title="Bet Canceled: " + wagerCheck["title"],
                      description="<@&" + str(wagerRoleId) + ">\n<@" + str(ctx.author.id) + "> canceled the bet!\nThe coins have been returned.",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.set_footer(text="Wager ID: " + str(wager_id),
                        icon_url="https://toppng.com/uploads/thumbnail/hands-holding-playing-cards-royalty-free-vector-clip-hand-holding-playing-cards-clipart-11563240429mbkjvlaujb.png")

        await ctx.respond(content="<@&" + str(wagerRoleId) + ">\n", embed=embed, allowed_mentions=discord.AllowedMentions())"""


def setup(bot):
    bot.add_cog(Roulette(bot))



