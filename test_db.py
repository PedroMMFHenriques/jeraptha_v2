# Tutorial: https://www.w3schools.com/python/python_mongodb_getstarted.asp
# Install: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/
# WSL fix: https://learn.microsoft.com/en-us/windows/wsl/systemd#how-to-enable-systemd

# sudo systemctl enable mongod # start on boot
# sudo service mongod start
# sudo service mongod stop
# sudo service mongod status

# stored data: /var/lib/mongodb

# Backup: mongodump --archive=/home/cawilho/jeraptha_v2_backup/JerapthaV2_01_06_2024
# Restore: mongorestore --drop --archive=/home/cawilho/jeraptha_v2_backup/JerapthaV2_01_06_2024

# Autobackup and deletion files older than 30 days: 
# crontab -e
# 0 6 * * * mongodump --archive=/home/cawilho/jeraptha_v2_backup/JerapthaV2_$(date +\%Y-\%m-\%d_\%H:\%M:\%S) && find /home/cawilho/jeraptha_v2_backup/ -type f -mtime +30 -exec rm {} \;

import os
from dotenv import load_dotenv

import pymongo

from datetime import datetime

load_dotenv() # Load vars

import json

# Load vars
global_json = json.load(open('global.json'))

# Setup database
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]
wagersCol = myDB["Wagers"]
wagersSubCol = myDB["WagersSub"]
rewardsCol = myDB["Rewards"]
beetdleCol = myDB["Beetdle"]

myQuery= {"member_id": 226800940668289025, "guild_id": 565223709699211275}
newValues = {'$set': {'wagers_won': 4}}
usersCol.update_one(myQuery, newValues)

myQuery= {"member_id": 119870049996636161, "guild_id": 565223709699211275}
newValues = {'$set': {'wagers_won': 2}}
usersCol.update_one(myQuery, newValues)

myQuery= {"member_id": 191675966332993536, "guild_id": 565223709699211275}
newValues = {'$set': {'wagers_won': 2}}
usersCol.update_one(myQuery, newValues)

myQuery= {"member_id": 220963716718395393, "guild_id": 565223709699211275}
newValues = {'$set': {'wagers_won': 1}}
usersCol.update_one(myQuery, newValues)

myQuery= {"member_id": 127469742163230721, "guild_id": 565223709699211275}
newValues = {'$set': {'wagers_won': 1}}
usersCol.update_one(myQuery, newValues)

"""usersCol.drop()
beetdleCol.drop()
wagersCol.drop()
wagersSubCol.drop()
rewardsCol.drop()
beetdleCol.drop()"""


"""wagersCol.update_many({"member_id": x, "guild_id": x},
                {"$inc" : {"earned_bet": 751}},
                upsert = False
              )"""

"""wagersCol.update_many({"_id": 0}, {"$set": {"wager_id": 0, "guild_id": x}})
wagersCol.update_many({"_id": 1}, {"$set": {"wager_id": 1, "guild_id": x}})
wagersCol.update_many({"_id": 2}, {"$set": {"wager_id": 2, "guild_id": x}})
wagersCol.update_many({"_id": 3}, {"$set": {"wager_id": 3, "guild_id": x}})
wagersSubCol.update_many({"wager_id": 0}, {"$set": {"guild_id": x}})
wagersSubCol.update_many({"wager_id": 1}, {"$set": {"guild_id": x}})
wagersSubCol.update_many({"wager_id": 2}, {"$set": {"guild_id": x}})
wagersSubCol.update_many({"wager_id": 3}, {"$set": {"guild_id": x}})


wagersCol.delete_many({"_id": 4})
wagersCol.delete_many({"_id": 5})
wagersCol.delete_many({"_id": 6})
wagersSubCol.delete_many({"wager_id": 4})
wagersSubCol.delete_many({"wager_id": 5})
wagersSubCol.delete_many({"wager_id": 6})"""

"""for x in wagersCol.find({},{}):
  print(x)"""

"""usersCol.drop()
wagersCol.drop()
wagersSubCol.drop()"""

"""rouletteGameCol = myDB["RouletteGame"] #ONLY 1 GAME AT A TIME IN THE GUILD
rouletteUserCol = myDB["RouletteUser"]
rouletteGameCol.drop()
rouletteUserCol.drop()"""

"""rewardsCol = myDB[db["REWARDS_COL"]]
rewardsCol.drop()"""

#insert
"""mydict = { "name": "John", "address": "Highway 37" }
mycol.insert_one(mydict)"""

#query
"""myquery = { "address": { "$gt": "S" } } #greater than
myquery = { "address": { "$regex": "^S" } } #start with
mydoc = mycol.find(myquery)

for x in mycol.find({},{ "_id": 0, "name": 1, "address": 1 }):
  print(x)
"""

#sort
"""mydoc = mycol.find().sort("name")
mydoc = mycol.find().sort("name", -1) #descending
for x in mydoc:
  print(x)"""

#delete
"""mycol.delete_one(myquery)"""

#update
"""myquery = { "address": { "$regex": "^S" } } #Update all documents where the address starts with the letter "S"
newvalues = { "$set": { "name": "Minnie" } } # {'$inc': {'item': X}} to increment by X

x = mycol.update_many(myquery, newvalues)"""

"""myclient.drop_database("mydatabase")
print(myclient.list_database_names())"""


