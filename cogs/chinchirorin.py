import os
import discord
from discord.ext import commands

import time, math
from datetime import datetime

import pymongo

import asyncio
import random

import json
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
chinchiroGameCol = myDB["ChinchirorinGame"] #ONLY 1 GAME AT A TIME IN THE GUILD (for now)
chinchiroUserCol = myDB["ChinchirorinUser"]

class Die:
    def __init__(self, sides=6):
        self.sides = sides

    def roll(self):
        self.roll_value = random.randint(1,self.sides)

    def get(self):
        return self.roll_value

class Dice:
    def __init__(self, number=3):
        self.set = []
        for i in range(number):
            self.set.append(Die(sides=6))

    def roll(self):
        for x in self.set:
            x.roll

    def get(self):
        results = []
        for x in self.set:
            results.append = x.get

        results.sort()
        return results

class Player:
    def __init__(self, betAmmount):
        self.betAmmount = betAmmount
        self.dice = Dice(3)

    def set_score(self):
        self.dice.roll
        # FAZER FUNC DE AVALIAR A HAND


    def get(self):
        return 1

class Chinchirorin(commands.Cog):
    """
    Start a game of Chinchirorin
    Default rules: https://en.wikipedia.org/wiki/Cee-lo
    """

    def __init__(self, bot):
        self.bot = bot

    chinchirorin = discord.SlashCommandGroup("chinchirorin", "Chinchirorin related commands.")

    # CHINCHIRORIN START
    @chinchirorin.command(name="play", description="Play a game of Cee-lo.")
    async def start(self, ctx: discord.ApplicationContext):
        chinchiroGameCheck = chinchiroGameCol.find_one({"guild_id": ctx.guild.id, "author_id": ctx.author.id, "running": True, "rolling": False})
        
