from flask import Flask, jsonify
import threading

api = Flask(__name__)

@api.route('/test', methods=['GET'])
def get_test():
    return jsonify({"test": "wow"}), 200

def run_api_thread():
    threading.Thread(target=lambda: api.run(port=5000)).start()