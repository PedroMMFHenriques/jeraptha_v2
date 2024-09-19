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
