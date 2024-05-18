from math import erf
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import json

app = Flask(__name__)
CORS(app)

uri = "mongodb://localhost:27017"
client = MongoClient(uri)

database = client.get_database("al-chronicles")
users = database.get_collection("users")
games = database.get_collection("games")
user_game_status = database.get_collection('user_game_status')
mongodelParam = {'_id':0}

@app.route('/healthcheck', methods=['GET'])
def healthCheck():
    return jsonify({'message' : 'BE is up and running!!!'})

@app.route('/users', methods=['GET'])
def getUser():
    query = {}
    usersList = users.find_one(query,mongodelParam)
    return jsonify(usersList)

@app.route('/finduser',methods=['POST'])
def findUserWithId():
    data={}
    if request.is_json:
        data = request.json
    try:
        email = data['_id']
        query = {'_id':email}
        usersList = users.find_one(query)
        return jsonify(usersList or {'errorMessage':'user not found'})
    except KeyError as e:
        return jsonify(usersList or {'errorMessage':'please provide valid username'})

@app.route('/adduser',methods=['POST'])
def addUser():
    data={}
    if request.is_json:
        data = request.json
    email = data['email']
    username = data['username']
    age = data['age']
    password = data['password']
    phonenumber = data['phonenumber']

    query = {
        'email':email,'username':username,'age':age,'password':password,'phonenumber':phonenumber,'_id':email
    }

    try:
        
        result = users.insert_one(query)
        id = str(result.inserted_id)
        if id == None:
            return jsonify({'errorMessage':'insertion failed!!!'})
        else:
            return jsonify({'insertion_id':id})
    
    except Exception as e:
        return jsonify({'errormessage':'failed to add user'})

@app.route('/listgames',methods=['GET'])
def getGamesList():
    query={}
    gameslist = []
    gameslistCursor = games.find(query);

    for game in gameslistCursor:
        gameslist.append(game);
    
    return jsonify({'data':gameslist});

if __name__ == '__main__':
    app.run(debug=True)