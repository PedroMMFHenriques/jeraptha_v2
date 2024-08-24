import discord
from discord.ext import commands

import numpy as np

import pymongo

import asyncio

from datetime import datetime, timedelta, date
import math
import random

import json
global_json = json.load(open('global.json'))
img_json = json.load(open("img_2_link.json"))

global_consts = global_json["CONSTS"]

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
rewardsCol = myDB[db["REWARDS_COL"]]

eight_ball_json = global_json["FUN"]["8BALL"]
fortune_cookie_json = global_json["FUN"]["FORTUNE_COOKIE"]
lootbox_json = global_json["FUN"]["LOOTBOX"]

reason = "Jeraptha punishment"

perk_list = list(global_json["TIERED_REWARDS"].keys())
punishment_list = list(global_json["PUNISHMENTS"].keys())
for i in range(len(punishment_list)):
    punishment_list[i] += " (costs " +  str(global_json["PUNISHMENTS"][punishment_list[i]]["COST"]) + ")"

class Rewards(commands.Cog): 
    """
    Check and upgrade perks. Buy punishments for other users.
    """
        
    def __init__(self, bot): 
        self.bot = bot

    
    """perks = discord.SlashCommandGroup("perks", "Perk info and upgrades.")


    # PERKS_INFO
    @perks.command(name="info", description="Info about the perks and their upgrades.")
    async def info(self, ctx: discord.ApplicationContext):
        userCheck = rewardsCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "daily_boost_tier": 1, "daily_crit_tier": 1})
        if(userCheck is None): 
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        embed = discord.Embed(title="Perks Info",
                            description="Upgrade with `/perks upgrade`",
                            colour=0x009900)
        
        rewards_list = global_json["TIERED_REWARDS"]

        for reward_name in rewards_list.keys():
            reward_tiers = rewards_list[reward_name]

            if(reward_name == "DAILY_BOOST"):
                user_tier = userCheck["daily_boost_tier"]
                reward_description = "Multiplier of the /daily reward.\n"
                n_rewards = 1
                

            elif(reward_name == "DAILY_CRIT"):
                user_tier = userCheck["daily_crit_tier"]
                reward_description = "Increase the % chance and multiplier of a CRIT /daily, gaining increased <:beets:1245409413284499587>.\n"
                n_rewards = 2
                
            else:
                await ctx.respond("Invalid reward name!", ephemeral=True)
                return
            
            user_tier_num = int(user_tier.split("_")[1])
            n_tiers = len(list(rewards_list[reward_name].keys()))
            for tier in reward_tiers.keys():
                tier_info = reward_tiers[tier]
                tier_num = int(tier.split("_")[1])
    
                if(tier_num < user_tier_num): continue #Skip previous tiers to the user's tier
                elif(tier_num == user_tier_num):
                    if(n_rewards == 1):
                        reward_title = "`" + reward_name + "` (" + user_tier + ":  " + list(tier_info.keys())[1] + " = " + str(list(tier_info.values())[1]) + ")"
                    elif(n_rewards == 2):
                        reward_title = "`" + reward_name + "` (" + user_tier + ":  " + list(tier_info.keys())[1] + " = " + str(list(tier_info.values())[1]) + ", " + list(tier_info.keys())[2] + " = " + str(list(tier_info.values())[2]) + ")"

                    if(user_tier_num + 1 >= n_tiers):
                        reward_description += "**MAX TIER**"
                else:
                    if(tier_num == user_tier_num + 1): reward_description += "**NEXT** "
                    if(n_rewards == 1):
                        reward_description += tier + ": " + list(tier_info.keys())[1] + " = " + str(list(tier_info.values())[1]) + ", costs " + str(list(tier_info.values())[0]) + " <:beets:1245409413284499587>.\n"
                    elif(n_rewards == 2):
                        reward_description += tier + ": " + list(tier_info.keys())[1] + " = " + str(list(tier_info.values())[1]) + ", " + list(tier_info.keys())[2] + " = " + str(list(tier_info.values())[2]) + ", costs " + str(list(tier_info.values())[0]) + " <:beets:1245409413284499587>.\n"


            embed.add_field(name=reward_title,
                            value=reward_description,
                            inline=False)
            
            embed.add_field(name="\n",
                            value="\n",
                            inline=False)

        await ctx.respond(embed=embed, ephemeral=True)


    
    # PERKS UPGRADE
    @perks.command(name="upgrade", description="Upgrade your perks.")
    @discord.option("perk", description="Choose what perk to upgrade.", required=True, choices=perk_list)
    async def upgrade(self, ctx: discord.ApplicationContext, perk: str):
        rewardsCheck = rewardsCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "daily_boost_tier": 1, "daily_crit_tier": 1})
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(rewardsCheck is None or userCheck is None): 
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        rewards_dict = global_json["TIERED_REWARDS"]
        if(perk == "DAILY_BOOST"):
            userTier = rewardsCheck["daily_boost_tier"]
            reward_db = "daily_boost_tier"

        elif(perk == "DAILY_CRIT"):
            userTier = rewardsCheck["daily_crit_tier"]
            reward_db = "daily_crit_tier"

        else:
            await ctx.respond("Invalid perk name!", ephemeral=True)
            return

        n_tiers = len(list(rewards_dict[perk].keys()))
        user_tier_int = int(userTier.split("_")[1])
        if(user_tier_int + 1 >= n_tiers):
            await ctx.respond("You have reached the max tier!", ephemeral=True)
            return

        next_tier = "TIER_" + str(user_tier_int + 1)
        cost = rewards_dict[perk][next_tier]["COST"]

        # Check wallet
        if(userCheck["coins"] < cost): 
            await ctx.respond("You don't have enough <:beets:1245409413284499587>, scrub!", ephemeral=True)
            return
        
        # Remove from wallet
        remove_coins = 0 - cost
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)
        
        # Upgrade
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$set': {reward_db: next_tier}}
        rewardsCol.update_one(myQuery, newValues)

        await ctx.respond("[Perk] <@" + str(ctx.author.id) + "> upgraded **" + perk + "** to **" + next_tier + "**!")"""


    # PUNISH
    @discord.command(name="punish", description="Punish an user.")
    @discord.option("punishment", description="What punishment to apply.", required=True, choices = punishment_list)
    @discord.option("target_user", description="@ the target user.", required=True)
    @discord.option("new_nick", description="[RENAME] Choose the new nick for the user.", required=False)
    async def rename(self, ctx: discord.ApplicationContext, punishment: str, target_user: str, new_nick: str):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(userCheck is None):
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return
        
        punishment = punishment.split(" ")[0]
        target_punishment = global_json["PUNISHMENTS"][punishment]
        if(userCheck["coins"] < target_punishment["COST"]): 
            await ctx.respond("You don't have enough <:beets:1245409413284499587>, scrub!", ephemeral=True)
            return
        
        #Check user argument
        try:
            user_change = target_user.split("@")[1][:-1]
            user_change = ctx.guild.get_member(int(user_change))
        except:
            await ctx.respond("Wrong user argument! Make sure you @ an user.", ephemeral=True)
            return

        if user_change.bot:
            await ctx.respond("You can't target a bot!", ephemeral=True)
            return
        

        # Don't punish if user was punished less than 1 hour ago
        targetCheck = usersCol.find_one({"member_id": user_change.id, "guild_id": ctx.guild.id},{"_id": 0, "last_punish": 1})
        if(targetCheck["last_punish"] + timedelta(hours=1) >  datetime.now()):
            timeLeft = targetCheck["last_punish"] + timedelta(hours=1) - datetime.now()
            minutesLeft = math.floor(timeLeft.seconds/60)
            secondsLeft = timeLeft.seconds - minutesLeft*60
            await ctx.respond(target_user + " was punished less than an hour ago! Time left: " + str(minutesLeft) + "m:" + str(secondsLeft) + "s.", ephemeral=True)
            return
        
        #Check perms and apply punishment
        if(punishment == "RENAME"):
            if(new_nick is None):
                await ctx.respond("You have to choose the option 'new_nick'!", ephemeral=True)
                return
            try:
                await user_change.edit(nick=new_nick, reason=reason)
                response_msg = "<@" + str(ctx.author.id) + "> changed " + target_user + "'s nickname!"
            except:
                await ctx.respond("You can't change " + target_user + "'s nickame! They're an admin.", ephemeral=True)
                return
            
        elif(punishment == "MUTE"):
            if(user_change.voice is None):
                await ctx.respond("You can't mute " + target_user + " while they're not on a voice channel!", ephemeral=True)
                return
            elif(user_change.voice.mute == True):
                await ctx.respond(target_user + " is already muted!", ephemeral=True)
                return
            try:
                await user_change.edit(mute=True, reason=reason)
                response_msg = "<@" + str(ctx.author.id) + "> muted " + target_user + "!"
            except:
                await ctx.respond("You can't mute " + target_user + "! They're an admin.", ephemeral=True)
                return
            
        elif(punishment == "DISCONNECT"):
            if(user_change.voice is None):
                await ctx.respond("You can't disconnect " + target_user + " while they're not on a voice channel!", ephemeral=True)
                return
            
            try:
                await user_change.edit(voice_channel=None, reason=reason)
                response_msg = "<@" + str(ctx.author.id) + "> disconnected " + target_user + "!"
            except:
                await ctx.respond("You can't disconnect " + target_user + "! They're an admin.", ephemeral=True)
                return
        

        # Limit punishing time to the punished
        myQuery= {"member_id": user_change.id, "guild_id": ctx.guild.id}
        newValues = {'$set': {'last_punish': datetime.now()}}
        usersCol.update_one(myQuery, newValues)

        # Remove coins from punisher
        remove_coins = 0 - target_punishment["COST"]
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)

        await ctx.respond(response_msg)


        if(punishment == "MUTE"):
            # Mute duration
            await asyncio.sleep(10)

            if(user_change.voice is not None):
                if(user_change.voice.mute == True):
                    await user_change.edit(mute=False, reason=reason)
                    await ctx.send(target_user + " has been unmuted.")



    eightBall = discord.SlashCommandGroup("8ball", "Roll or add phrases to the 8-ball")
    
    # 8-BALL ROLL
    @eightBall.command(name="roll", description="Roll the 8-Ball for its wisdom. (Costs " + str(eight_ball_json["ROLL_COST"]) + ")")
    @discord.option("question", description="Ask it a Yes or No question. (Costs " + str(eight_ball_json["ROLL_COST"]) + ")", required=True)
    async def roll(self, ctx: discord.ApplicationContext, question: str):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1, "last_8ball": 1})
        if(userCheck is None):
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        if(userCheck["coins"] < eight_ball_json["ROLL_COST"]): 
            await ctx.respond("You don't have enough <:beets:1245409413284499587>, scrub!", ephemeral=True)
            return
        
        # Don't roll if user already did less than 1 hour ago
        if(userCheck["last_8ball"] + timedelta(minutes=30) >  datetime.now()):
            timeLeft = userCheck["last_8ball"] + timedelta(minutes=30) - datetime.now()
            minutesLeft = math.floor(timeLeft.seconds/60)
            secondsLeft = timeLeft.seconds - minutesLeft*60
            await ctx.respond("You rolled the 8-Ball less than an 30 minutes ago, please trust its prediction!\nTime left: " + str(minutesLeft) + "m:" + str(secondsLeft) + "s.", ephemeral=True)
            return
        
        # Reset roll time
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$set': {'last_8ball': datetime.now()}}
        usersCol.update_one(myQuery, newValues)

        # Remove coins from the roller
        remove_coins = 0 - eight_ball_json["ROLL_COST"]
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)

        answer_list = []
        with open(eight_ball_json["FILE"], 'r') as file:
            for line in file:
                phrase = line.strip()
                if phrase:
                    answer_list.append(phrase)
        
        answer = random.choice(answer_list)

        embed = discord.Embed(title="",
                      description="<@" + str(ctx.author.id) + ">  payed " + str(eight_ball_json["ROLL_COST"]) + "<:beets:1245409413284499587> to ask the 8-Ball: \n**" + question + "**\n\nTo which it responded:\n```" + answer + "```",
                      colour=0x009900,
                      timestamp=datetime.now())


        embed.set_footer(text="8-Ball",
                         icon_url="https://t4.ftcdn.net/jpg/02/13/01/79/360_F_213017967_z1SLHuRCxHNpCBxUlid4lxuq7q6n16Qr.jpg")

        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())

    
    # 8-BALL ADD
    @eightBall.command(name="add", description="Add an answer to the 8-Ball. (Costs " + str(eight_ball_json["ADD_COST"]) + ")")
    @discord.option("answer", description="Give an answer to a yes or no question. (Costs " + str(eight_ball_json["ADD_COST"]) + ")", required=True)
    async def add(self, ctx: discord.ApplicationContext, answer: str):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1, "last_8ball": 1})
        if(userCheck is None):
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        if(userCheck["coins"] < eight_ball_json["ADD_COST"]): 
            await ctx.respond("You don't have enough <:beets:1245409413284499587>, scrub!", ephemeral=True)
            return

        answer_list = []
        with open(eight_ball_json["FILE"], 'r') as file:
            for line in file:
                phrase = line.strip()
                if phrase:  
                    answer_list.append(phrase)
        
        if answer in answer_list:
            await ctx.respond("That answer already exists!", ephemeral=True)
            return
        
        with open(eight_ball_json["FILE"], 'a') as file:
            file.write(answer + '\n')

        # Remove coins from the adder
        remove_coins = 0 - eight_ball_json["ADD_COST"]
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)

        await ctx.respond("[8-Ball] You added a new answer:\n**" + answer + "**", ephemeral=True)


        embed = discord.Embed(title="",
                      description="<@" + str(ctx.author.id) + "> added a new answer to the 8-Ball for " + str(eight_ball_json["ADD_COST"]) + "<:beets:1245409413284499587>.",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.set_footer(text="8-Ball",
                         icon_url="https://t4.ftcdn.net/jpg/02/13/01/79/360_F_213017967_z1SLHuRCxHNpCBxUlid4lxuq7q6n16Qr.jpg")

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions())



    fortune = discord.SlashCommandGroup("fortune_cookie", "Get wisdom or add phrases to the fortune cookie.")

    # FORTUNE COOKIE WISDOM
    @fortune.command(name="wisdom", description="As the fortune cookie for wisdom. (Costs " + str(fortune_cookie_json["FORTUNE_COST"]) + ")")
    async def wisdom(self, ctx: discord.ApplicationContext):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1, "last_fortune": 1})
        if(userCheck is None):
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        if(userCheck["coins"] < fortune_cookie_json["FORTUNE_COST"]): 
            await ctx.respond("You don't have enough <:beets:1245409413284499587>, scrub!", ephemeral=True)
            return
        
        # Don't ask for wisdom if user already did less than 30 mins ago
        if(userCheck["last_fortune"] + timedelta(minutes=30) >  datetime.now()):
            timeLeft = userCheck["last_fortune"] + timedelta(minutes=30) - datetime.now()
            minutesLeft = math.floor(timeLeft.seconds/60)
            secondsLeft = timeLeft.seconds - minutesLeft*60
            await ctx.respond("You used the fortune cookie less than 30 minutes ago, please interiorize its wisdom!\nTime left: " + str(minutesLeft) + "m:" + str(secondsLeft) + "s.", ephemeral=True)
            return
        
        # Reset roll time
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$set': {'last_fortune': datetime.now()}}
        usersCol.update_one(myQuery, newValues)

        # Remove coins from the roller
        remove_coins = 0 - fortune_cookie_json["FORTUNE_COST"]
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)

        answer_list = []
        with open(fortune_cookie_json["FILE"], 'r') as file:
            for line in file:
                phrase = line.strip()
                if phrase:
                    answer_list.append(phrase)
        
        answer = random.choice(answer_list)

        embed = discord.Embed(title="",
                      description="<@" + str(ctx.author.id) + "> asked the fortune cookie for wisdom for " + str(fortune_cookie_json["FORTUNE_COST"]) + "<:beets:1245409413284499587>.\n\nIt responded:\n```" + answer + "```",
                      colour=0x009900,
                      timestamp=datetime.now())


        embed.set_footer(text="Fortune",
                         icon_url="https://images.emojiterra.com/google/noto-emoji/unicode-15.1/color/1024px/1f960.png")

        await ctx.respond(embed=embed, allowed_mentions=discord.AllowedMentions())

    # FORTUNE COOKIE ADD
    @fortune.command(name="add", description="Add wisdom to the fortune cookie. (Costs " + str(fortune_cookie_json["ADD_COST"]) + ")")
    @discord.option("wisdom", description="Give wisdom to the fortune cookie. (Costs " + str(fortune_cookie_json["ADD_COST"]) + ")", required=True)
    async def add(self, ctx: discord.ApplicationContext, wisdom: str):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1, "last_fortune": 1})
        if(userCheck is None):
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return
        
        if(userCheck["coins"] < fortune_cookie_json["ADD_COST"]): 
            await ctx.respond("You don't have enough <:beets:1245409413284499587>, scrub!", ephemeral=True)
            return

        answer_list = []
        with open(fortune_cookie_json["FILE"], 'r') as file:
            for line in file:
                phrase = line.strip()
                if phrase:  
                    answer_list.append(phrase)
        
        if wisdom in answer_list:
            await ctx.respond("That wisdom already exists!", ephemeral=True)
            return
        
        with open(fortune_cookie_json["FILE"], 'a') as file:
            file.write(wisdom + '\n')

        # Remove coins from the adder
        remove_coins = 0 - fortune_cookie_json["ADD_COST"]
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)
        
        await ctx.respond("[Fortune Cookie] You added new wisdom for " + str(fortune_cookie_json["ADD_COST"]) + "<:beets:1245409413284499587>:\n**" + wisdom + "**", ephemeral=True)

        embed = discord.Embed(title="",
                      description="<@" + str(ctx.author.id) + "> added a new wisdom to the fortune cookie.",
                      colour=0x009900,
                      timestamp=datetime.now())

        embed.set_footer(text="Fortune",
                         icon_url="https://images.emojiterra.com/google/noto-emoji/unicode-15.1/color/1024px/1f960.png")

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions())



    # LOOTBOX 
    @discord.slash_command(name="lootbox", description="Open a lootbox. The first daily is free, the rest costs " + str(lootbox_json["COST"]) + ".")
    async def start(self, ctx: discord.ApplicationContext):
        checkUser = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1, "last_lootbox": 1})
        if(checkUser is None): await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)

        free = False
        # Check didn't do /lootbox today, it's free
        if(date.today() >= checkUser["last_lootbox"].date() + timedelta(days=1)):
            free = True
            myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
            newValues = {"$set": {"last_lootbox": datetime.now()}}
            usersCol.update_one(myQuery, newValues)
            await ctx.respond(f"[Lootbox] <@{ctx.author.id}> is opening their daily free lootbox!")

        else:
            timeLeft = (datetime.combine(date.today() + timedelta(days=1), datetime.min.time()) - datetime.now())
            hoursLeft = math.floor(timeLeft.seconds/3600)
            minutesLeft = math.floor((timeLeft.seconds-hoursLeft*3600)/60)
            secondsLeft = timeLeft.seconds - hoursLeft*3600 - minutesLeft*60

            if(checkUser["coins"] < lootbox_json["COST"]): 
                await ctx.respond(f"You don't have enough <:beets:1245409413284499587>, scrub! Time left for your free lootbox: {hoursLeft}h:{minutesLeft}m:{secondsLeft}s.", ephemeral=True)
                return
            else:
                # Remove coins from the lootbox opener
                remove_coins = 0 - lootbox_json["COST"]
                myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
                newValues = {'$inc': {'coins': int(remove_coins), 'coins_bet': int(lootbox_json["COST"])}}
                usersCol.update_one(myQuery, newValues)

                await ctx.send("[Lootbox] <@" + str(ctx.author.id) + "> is opening a lootbox for "+ str(lootbox_json["COST"]) + "<:beets:1245409413284499587>!")
                await ctx.respond(f"Time left for your free lootbox: {hoursLeft}h:{minutesLeft}m:{secondsLeft}s.", ephemeral=True)
        


        cycle = True
        while(cycle):
            cycle = False

            rng = random.SystemRandom().randint(1, 100) 

            if(rng <= 23): # Trash
                img_link = img_json["LOOTBOX"]["TRASH"]
                reward = "Trash"
            
            elif(24 <= rng and rng <= 40): # Refund
                img_link = img_json["LOOTBOX"]["REFUND"]
                reward = "Refund"
            
            elif(41 <= rng and rng <= 70): # Fortune
                img_link = img_json["LOOTBOX"]["FORTUNE"]
                reward = "Fortune"
            
            elif(71 <= rng and rng <= 100): # Beets
                img_link = img_json["LOOTBOX"]["BEETS"]
                reward = "Beets"


            extra_time = 0
            extra_print = ""
            extra_crate = random.SystemRandom().randint(1, 100)
            if(extra_crate <= 15): 
                img_link = img_link["EXTRA"]
                extra_print = "... and an extra lootbox"
                cycle = True
                extra_time = 3
            else:
                img_link = img_link["NORMAL"]


            await ctx.send(img_link)


            # Suspense
            await asyncio.sleep(6 + extra_time)


            reward_msg = ""
            # Distribute rewards
            if(reward == "Trash"): # Trash
                #NOTHING OMEGALUL
                nothing = True
            

            elif(reward == "Refund"): # Refund
                myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
                if(free):
                    newValues = {'$inc': {'coins': int(lootbox_json["COST"]), 'total_earned': int(lootbox_json["COST"])}}
                else:
                    newValues = {'$inc': {'coins': int(lootbox_json["COST"]), 'total_earned': int(lootbox_json["COST"]), 'earned_bet': int(lootbox_json["COST"])}}
                usersCol.update_one(myQuery, newValues)
                reward_msg = ", earning " + str(lootbox_json["COST"]) + "<:beets:1245409413284499587> back"
            

            elif(reward == "Fortune"): # Fortune
                file = "images/lootbox/lootbox_fortune"
                reward = "Fortune"

                answer_list = []
                with open(fortune_cookie_json["FILE"], 'r') as file:
                    for line in file:
                        phrase = line.strip()
                        if phrase:
                            answer_list.append(phrase)
                
                answer = random.choice(answer_list)

                embed = discord.Embed(title="",
                            description="<@" + str(ctx.author.id) + "> got a fortune cookie reading:\n```" + answer + "```",
                            colour=0x009900,
                            timestamp=datetime.now())


                embed.set_footer(text="Fortune",
                                icon_url="https://images.emojiterra.com/google/noto-emoji/unicode-15.1/color/1024px/1f960.png")

                await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions())
            

            elif(reward == "Beets"): # Beets
                daily_coins = np.random.normal(loc=global_consts["DAILY_MEAN"], scale=global_consts["DAILY_STD"], size = (1))[0]

                myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
                if(free):
                    newValues = {'$inc': {'coins': int(daily_coins), 'total_earned': int(daily_coins)}}
                else:
                    newValues = {'$inc': {'coins': int(daily_coins), 'total_earned': int(daily_coins), 'earned_bet': int(daily_coins)}}
                usersCol.update_one(myQuery, newValues)
                reward_msg = ", earning " + str(int(daily_coins)) + "<:beets:1245409413284499587>"
            
            
            await ctx.send(f"[Lootbox] <@{ctx.author.id}> got " + reward + reward_msg + extra_print + "!")


        


def setup(bot):
    bot.add_cog(Rewards(bot))
