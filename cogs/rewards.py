import discord
from discord.ext import commands

import pymongo

import asyncio

from datetime import datetime, timedelta
import math

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
rewardsCol = myDB[db["REWARDS_COL"]]

reason = "Jeraptha punishment"

global_json = json.load(open('global.json'))
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

    
    perks = discord.SlashCommandGroup("perks", "Perk info and upgrades.")


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

        await ctx.respond("[Perk] <@" + str(ctx.author.id) + "> upgraded **" + perk + "** to **" + next_tier + "**!")


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



def setup(bot):
    bot.add_cog(Rewards(bot))
