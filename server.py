from math import erf
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import jwt
import datetime

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
        return jsonify({'errorMessage':'please provide valid username'})

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
        print(query)
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

## db.users.aggregate([{$lookup:{from:'user_game_status',localField:'email',foreignField:'user_id',as:'game_progress'}},{$unwind:'$game_progress'}])
@app.route('/userGameStatus',methods=['POST'])
def getUserGameStatus():
    reqdata={}
    responseData =[];
    if request.is_json:
        reqdata = request.json
    try:
        email = reqdata['_id']
        pipeline= [{
                        '$lookup': { 
                            'from':'user_game_status',
                            'localField':'email',
                            'foreignField':'user_id',
                            'as':'game_progress'}
                    },
                    {
                        '$unwind':'$game_progress'
                    }]
        result = users.aggregate(pipeline);
        for doc in result:
            responseData.append(doc)
        return jsonify(responseData)
    
    except Exception as e:
        return jsonify({'errormessage':'something went wrong'})
    return jsonify({})

@app.route('/tokenize',methods=['POST'])
def tokenizeLogin():
    reqdata ={}
    if request.is_json:
        reqdata = request.json
        
    return jsonify({'sid':''})


def processUserGameStatus(respJson):
    finalList=[]
    for game in respJson:
        game['name']  = game['game'][0]['name']
        game['category'] = game['game'][0]['category']
        game.pop('game')
        print(game)
    return {}

@app.route('/usersummary',methods=['POST'])
def getUserSummary():
    reqdata={}
    response = {}

    game_status_data =[];
    if request.is_json:
        reqdata = request.json
    try:
        email = reqdata['email']

        totalGames = games.count_documents({});
        response['totalGames'] = totalGames

        
        # game status by email id
        pipeline= [
            {
                '$match' : { 'email':email } 
            },
            {
                '$lookup': {
                    'from':'user_game_status',
                    'let':{'email':'$email'},
                    'pipeline':[
                          { '$match':{ '$expr': { '$eq': ['$email','$$email'] } } },
                          { '$project':{ '_id':0, 'email':0}},
                          {
                              '$lookup':{
                                    'from':'games',
                                    'let':{'game_id':'$game_id'},
                                    'pipeline':[
                                        { '$match':{ '$expr': { '$eq': ['$_id','$$game_id'] } } },
                                        { '$project':{ '_id':0, 'name':1, 'category':1} }
                                        ],
                                    'as':'game'
                              }
                          }
                          ],
                    'as':'game_status' 
                    } 
            },
            {
                '$project':{
                    '_id':0,
                    'password':0,
                    'phonenumber': 0,
                    'username': 0
                }
            }]
        print('pipeline',pipeline)
        result = users.aggregate(pipeline)
        for doc in result:
            game_status_data.append(doc)

        gamesFinished = len(game_status_data[0]['game_status'])        

        progress_percent = (gamesFinished/totalGames)*100

        response['gamesCompleted'] = gamesFinished
        response['progressPercentage'] = progress_percent
        processUserGameStatus(game_status_data[0]['game_status'])
        response['game_status'] = game_status_data[0]['game_status']

    except Exception as e:
        print(e)
        return jsonify({'errormessage':'something went wrong'})

    return jsonify(response)

@app.route('/updateusergamestatus',methods=['POST'])
def upsertUserGameStatus():
    data={}
    response = {}
    if request.is_json:
        data = request.json
        userEmail = data['email']
        gameId = data['game_id']
        status = data['status']

        query = {'email':userEmail,'game_id':gameId}
        updatet = {'$set':{ 'status':status, 'email' : userEmail, 'game_id':gameId}}
        try:
            result = user_game_status.update_one(query,updatet,True)
            response['acknowledged'] = True
        except Exception as e:
            print(e)
            return jsonify({'errormessage':'failed to add user'})

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)