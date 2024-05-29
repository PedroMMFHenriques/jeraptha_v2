import os
import discord
from discord.ext import commands

import pymongo

from datetime import datetime, timedelta, date

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
rewardsCol = myDB[db["REWARDS_COL"]]

reason = "Jeraptha punishment"
punishments = global_json["PUNISHMENTS"]

perk_list = ["DAILY_BOOST", "DAILY_CRIT"]

class Rewards(commands.Cog): 
    """
    Check and upgrade perks.
    """
        
    def __init__(self, bot): 
        self.bot = bot

    # PERKS_INFO
    @discord.slash_command(name="perks_info", description="Info about the perks and their upgrades.")
    async def perks_info(self, ctx: discord.ApplicationContext):
        userCheck = rewardsCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "daily_boost_tier": 1, "daily_crit_tier": 1})
        if(userCheck is None): 
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        embed = discord.Embed(title="Perks Info",
                            description="Upgrade with '/upgrade <perk_name>'",
                            colour=0x009900)
        
        rewards_list = global_json["TIERED_REWARDS"]

        for reward_name in rewards_list.keys():
            reward_tiers = rewards_list[reward_name]

            if(reward_name == "DAILY_BOOST"):
                user_tier = userCheck["daily_boost_tier"]
                reward_description = "Multiplier of the /daily reward.\n"
                

            elif(reward_name == "DAILY_CRIT"):
                user_tier = userCheck["daily_crit_tier"]
                reward_description = "Increase the % chance of a CRIT /daily, gaining 3x coins.\n"
                
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
                    reward_value = list(tier_info.values())[1]
                    reward_title = reward_name + " (" + user_tier + ": " + list(tier_info.keys())[1] + " = " + str(reward_value) + ")"
                    if(user_tier_num + 1 >= n_tiers):
                        reward_description += "**MAX TIER**"
                else:
                    if(tier_num == user_tier_num + 1): reward_description += "**NEXT**: "
                    reward_description += tier + ": " + list(tier_info.keys())[1] + " = " + str(list(tier_info.values())[1]) + ", costs " + str(list(tier_info.values())[0]) + " coins.\n"


            embed.add_field(name=reward_title,
                            value=reward_description,
                            inline=False)
            
            embed.add_field(name="\n",
                            value="\n",
                            inline=False)

        await ctx.respond(embed=embed, ephemeral=True)


    
    # UPGRADE
    @discord.slash_command(name="upgrade", description="Upgrade your perks.")
    @discord.option("perk", description="Choose what perk to upgrade.", required=True, choices=perk_list)
    async def upgrade(self, ctx: discord.ApplicationContext, name: str):
        rewardsCheck = rewardsCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "daily_boost_tier": 1, "daily_crit_tier": 1})
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(rewardsCheck is None or userCheck is None): 
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        rewards_dict = global_json["TIERED_REWARDS"]
        if(name == "DAILY_BOOST"):
            userTier = rewardsCheck["daily_boost_tier"]
            reward_db = "daily_boost_tier"

        elif(name == "DAILY_CRIT"):
            userTier = rewardsCheck["daily_crit_tier"]
            reward_db = "daily_crit_tier"

        else:
            await ctx.respond("Invalid perk name!", ephemeral=True)
            return

        n_tiers = len(list(rewards_dict[name].keys()))
        user_tier_int = int(userTier.split("_")[1])
        if(user_tier_int + 1 >= n_tiers):
            await ctx.respond("You have reached the max tier!", ephemeral=True)
            return

        next_tier = "TIER_" + str(user_tier_int + 1)
        cost = rewards_dict[name][next_tier]["COST"]

        # Check wallet
        if(userCheck["coins"] < cost): 
            await ctx.respond("You don't have enough coins, scrub!", ephemeral=True)
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

        await ctx.respond("[Perk] <@" + str(ctx.author.id) + "> upgraded **" + name + "** to **" + next_tier + "**!")



    # RENAME
    @discord.command(name="rename", description="Rename an user. Costs " + str(punishments["RENAME_COST"]) + " coins.")
    @discord.option("user", description="@ the target user.", required=True)
    @discord.option("new_nick", description="Choose the new nick for the user.", required=True)
    async def rename(self, ctx: discord.ApplicationContext, user: str, new_nick: str):
        userCheck = usersCol.find_one({"member_id": ctx.author.id, "guild_id": ctx.guild.id},{"_id": 0, "coins": 1})
        if(userCheck is None):
            await ctx.respond("OOPS! This user isn't in the database! Notify bot admin!", ephemeral=True)
            return

        if(userCheck["coins"] < punishments["RENAME_COST"]): 
            await ctx.respond("You don't have enough coins, scrub!", ephemeral=True)
            return
        
        #Check user argument
        try:
            user_change = user.split("@")[1][:-1]
            user_change = ctx.guild.get_member(int(user_change))
        except:
            await ctx.respond("Wrong user argument! Make sure you @ an user.", ephemeral=True)
            return

        if user_change.bot:
            await ctx.respond("You can't change a bot's nickname!", ephemeral=True)
            return

        #Check perms
        try:
            await user_change.edit(nick=new_nick, reason=reason)
        except:
            await ctx.respond("You can't change " + user + "'s nickame!", ephemeral=True)
            return
        
        remove_coins = 0 - punishments["RENAME_COST"]
        myQuery= {"member_id": ctx.author.id, "guild_id": ctx.guild.id}
        newValues = {'$inc': {'coins': int(remove_coins)}}
        usersCol.update_one(myQuery, newValues)

        await ctx.respond("You changed " + user + "'s nickname!", ephemeral=True)



def setup(bot):
    bot.add_cog(Rewards(bot))



