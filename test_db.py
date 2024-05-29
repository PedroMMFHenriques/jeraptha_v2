# Tutorial: https://www.w3schools.com/python/python_mongodb_getstarted.asp
# Install: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/
# WSL fix: https://learn.microsoft.com/en-us/windows/wsl/systemd#how-to-enable-systemd

# sudo systemctl enable mongod # start on boot
# sudo service mongod start
# sudo service mongod stop
# sudo service mongod status

import os
from dotenv import load_dotenv

import pymongo

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

usersCol.update({},
                {"$set" : {"coins_bet": 0}},
                upsert = False,
                multi = True
              )

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
