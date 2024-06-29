from flask import Flask, jsonify
import threading

api = Flask(__name__)

import pymongo

import json
global_json = json.load(open('global.json'))
db = global_json["DB"]
myClient = pymongo.MongoClient(db["CLIENT"])
myDB = myClient[db["DB"]]
usersCol = myDB[db["USERS_COL"]]

@api.route('/test', methods=['GET'])
def get_test():
    return jsonify({"test": "wow"}), 200


@api.route('/check_pp', methods=['GET'])
def get_check_pp():
    checkPP = usersCol.find_one({"guild_id": 565223709699211275, "member_id": 138052322306555906},{"_id": 0, "coins": 1})
    pp_coins = checkPP["coins"]
    return jsonify({"coins": pp_coins}), 200


def run_api_thread():
    threading.Thread(target=lambda: api.run(port=5000)).start()