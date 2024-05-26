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
    
    wager = discord.SlashCommandGroup("wager", "Wager related commands.")
    
    # wager start
    @wager.command(name="start", description="Start wager. Default duration is 10 minutes.")
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
        end_wager_time = duration_s + math.floor(time.time())

        # wager: wager id, guild id, quem criou, duração, title, descrição das opções
        wager_id = wagersCol.count_documents({})
        wagersCol.insert_one({"_id": wager_id, "guild_id": ctx.guild.id, "author_id": ctx.author.id, 
                              "settled": False, "canceled": False, "end_wager": end_wager_time, "title": title, "winning_option": None,
                              "option_a": option_a, "option_b": option_b, "option_c": option_c, "option_d": option_d})

        wagerRoleId = discord.utils.get(ctx.guild.roles, name=WagerRole).id
        embed = discord.Embed(title="Bet Started: " + title,
                      description="<@&" + str(wagerRoleId) + ">\n<@" + str(ctx.author.id) + "> just started a wager with **ID " + str(wager_id) + "**.\nBetting will end <t:" + str(end_wager_time) + ":R>!",
                      colour=0x009900,
                      timestamp=datetime.now())

        option_string = "**A:** " + option_a + "\n**B:** " + option_b
        if(option_c != ""): 
            option_string += "\n**C:** " + option_c
            if(option_d != ""): option_string += "\n**D:** " + option_d
        
        embed.add_field(name="Betting options:",
                        value=option_string,
                        inline=False)

        embed.set_footer(text="Wager ID: " + str(wager_id),
                         icon_url="https://toppng.com/uploads/thumbnail/hands-holding-playing-cards-royalty-free-vector-clip-hand-holding-playing-cards-clipart-11563240429mbkjvlaujb.png")

        await ctx.respond(embed=embed)



    # wager bet
    @wager.command(name="bet", description="Bet in a wager.")
    @discord.option("wager_id", description="ID of the wager.", required=True)
    @discord.option("bet_option", description="Choose what option to bet on.", required=True, choices=['option_a', 'option_b', 'option_c', 'option_d'])
    @discord.option("bet_amount", description="Bet amount.", required=True)
    async def bet(self, ctx: discord.ApplicationContext, wager_id: int, bet_option: str, bet_amount: int):

        # Checks
        wagerCheck = wagersCol.find_one({"_id": wager_id},{"_id": 0, "title": 1, "settled": 1, "canceled": 1, "end_wager": 1, "option_a": 1, "option_b": 1, "option_c": 1, "option_d": 1})
        if(wagerCheck is None): 
            await ctx.respond("That wager doesn't exist!", ephemeral=True)
            return
        
        elif(wagerCheck["canceled"] == True): 
            await ctx.respond("That wager has been canceled!", ephemeral=True)
            return

        elif(wagerCheck["settled"] == True): 
            await ctx.respond("That wager was already settled!", ephemeral=True)
            return
        
        elif(wagerCheck["end_wager"] < math.floor(time.time())): 
            await ctx.respond("The betting interval is over!", ephemeral=True)
            return
        elif((wagerCheck["option_c"] == "" and bet_option == "option_c") or (wagerCheck["option_d"] == "" and bet_option == "option_d")): 
            await ctx.respond("That option isn't available!", ephemeral=True)
            return
        
        wagerSubCheck = wagersSubCol.find_one({"wager_id": wager_id, "member_id": ctx.author.id},{"_id": 0, "bet_option": 1})
        if(wagerSubCheck is not None):
            if(wagerSubCheck["bet_option"] is not None and wagerSubCheck["bet_option"] != bet_option): 
                await ctx.respond("You already bet in another option!", ephemeral=True)
                return

        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(userCheck["coins"] < bet_amount): 
            await ctx.respond("You don't have enough coins, scrub!", ephemeral=True)
            return

        # If already bet, increase bet
        if(wagerSubCheck is not None):
            #remove from wallet
            remove_coins = 0 - bet_amount
            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {'$inc': {'coins': int(remove_coins)}}
            usersCol.update_one(myQuery, newValues)

            #add to bet
            myQuery = {"wager_id": wager_id, "member_id": ctx.author.id}
            newValues = {'$inc': {'total_bet': int(bet_amount)}}
            wagersSubCol.update_one(myQuery, newValues)
            
            total_bet = wagersSubCol.find_one({"wager_id": wager_id, "member_id": ctx.author.id},{"_id": 0, "total_bet": 1})["total_bet"]
            await ctx.respond("<@"+ str(ctx.author.id) + "> increased their bet on **" + wagerCheck["title"] + "** in option **" + wagerCheck[bet_option] + "**, totalling **" + str(total_bet) + "** coins!")
        
        # New bet
        else:
            # wagersub: id sub wager, id da wager, o id membro, em qual apostou e quanto 
            wagersSubCol.insert_one({"wager_id": wager_id, "member_id": ctx.author.id, "bet_option": bet_option, "total_bet": int(bet_amount)})
            await ctx.respond("<@" + str(ctx.author.id) + "> bet on **" + wagerCheck["title"] + "** in option **" + wagerCheck[bet_option] + "** with **" + str(bet_amount) + "** coins!")
    
    
    #wager settle
    @wager.command(name="settle", description="Settle a wager.")
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

        await ctx.respond(embed=embed)



    # wager info
    @wager.command(name="info", description="Get info on the wager.")
    @discord.option("wager_id", description="ID of the wager.", required=True)
    async def start(self, ctx: discord.ApplicationContext, wager_id: int):

        wagerCheck = wagersCol.find_one({"_id": wager_id},{"_id": 0, "title": 1, "author_id": 1, "settled": 1, "canceled": 1, "winning_option": 1, "option_a": 1, "option_b": 1, "option_c": 1, "option_d": 1})
        
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
        else: option_a_odds = 0.99 * total_bet / option_wager["option_a"]

        if(option_wager["option_b"] == 0): option_b_odds = "N/A"
        else: option_b_odds = 0.99 * total_bet / option_wager["option_b"]

        if(option_wager["option_c"] == 0): option_c_odds = "N/A"
        else: option_c_odds = 0.99 * total_bet / option_wager["option_c"]

        if(option_wager["option_d"] == 0): option_d_odds = "N/A"
        else: option_d_odds = 0.99 * total_bet / option_wager["option_d"]

        description_embed = ""
        if(wagerCheck["canceled"]): description_embed = "**CANCELED**\n"
        elif(wagerCheck["settled"]): description_embed = "**SETTLED**\nWinning option: **" + wagerCheck["winning_option"] + "**\n"
        
        description_embed += "**" + wagerCheck["option_a"] + "**: " + str(option_wager["option_a"]) + " coins, " + str(round(option_a_odds,2)) + " odds\n"
        description_embed += "**" + wagerCheck["option_b"] + "**: " + str(option_wager["option_b"]) + " coins, " + str(round(option_b_odds,2)) + " odds\n"
        if(wagerCheck["option_c"] != ""):
            description_embed += "**" + wagerCheck["option_c"] + "**: " + str(option_wager["option_c"]) + " coins, " + str(round(option_c_odds,2)) + " odds\n"
        if(wagerCheck["option_d"] != ""):
            description_embed += "**" + wagerCheck["option_d"] + "**: " + str(option_wager["option_d"]) + " coins, " + str(round(option_d_odds,2)) + " odds\n"

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

        await ctx.respond(embed=embed)



    #wager cancel
    @wager.command(name="cancel", description="Cancel a wager.")
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
                      description="<@&" + str(wagerRoleId) + ">\n<@" + str(ctx.author.id) + "> canceled the bet!\nThe bets have been returned.",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.set_footer(text="Wager ID: " + str(wager_id),
                        icon_url="https://toppng.com/uploads/thumbnail/hands-holding-playing-cards-royalty-free-vector-clip-hand-holding-playing-cards-clipart-11563240429mbkjvlaujb.png")

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Wager(bot))



