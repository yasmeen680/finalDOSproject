from flask import Flask
import flask
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_restful import Api
from flask import request
from flask import Flask,jsonify,json
import json
import requests
from itertools import cycle

app = Flask(__name__)
api = Api(app)



# SERVER_POOL_CATALOG = ['http://catalog-server-2:4002', 'http://catalog-server-1:4001']
# SERVER_POOL_ORDER = ['http://orders-server-1:6001', 'http://orders-server-2:6002']

SERVER_POOL_CATALOG = ["http://127.0.0.1:4001","http://127.0.0.1:4002"]
SERVER_POOL_ORDER = ["http://127.0.0.1:5002","http://127.0.0.1:5001"]

ITER_CATALOG = cycle(SERVER_POOL_CATALOG)
ITER_ORDER = cycle(SERVER_POOL_ORDER)

def round_robin(iter):
    return next(iter)

divider = "\n-----------------------------------------------\n"

@app.route('/info/<id>', methods=['GET'])
def getBookById(id):
    
    book = bookFoundInCache(id)
    if book is not None :
        return formatInfoResponse(book)

    server = round_robin(ITER_CATALOG)
    r = requests.get('{}/books/{}'.format(server, id))
    if r.status_code == 404:
        return "invalid book number" 

    if r.status_code == 200:
        response = r.json()
        addBookToCache(response)
        return formatInfoResponse(response)

    else : return "ERROR try again later"

@app.route('/search/<topic>', methods=['GET'])
def getBooksByTopic(topic):

    topicsList = topicFoundInCache(topic)
    if topicsList is not None :
        return formatTopicResponse(topicsList)

    server = round_robin(ITER_CATALOG)
    r = requests.get('{}/books?topic={}'.format(server, topic))
    if r.status_code == 404:
        return "  no books found with this topic" 
    if r.status_code == 200:
        response = r.json()
        booksList = []
        for book in response:
            addBookToCache(book)
            booksList.append(str(book["id"]))   
        addTopicToCache(topic, booksList) 
        
        return formatTopicResponse(response)

    else : return "ERROR try again later"

@app.route('/purchase/<id>', methods=['POST'])
def updateBookQuantity(id):
    body = request.get_json()
    name = body["name"]

    server = round_robin(ITER_ORDER)

    r = requests.post('{}/orders'.format(server),
                         json={"id":int(id), "name": name})
    if r.status_code == 404:
        return "No Book found, Invalid Id"
    if r.status_code == 400:
        return "Out of stock"
    if r.status_code == 200:
        response = r.json()
        return "Bought Book '" + response["title"]+"'"
    else : return "ERROR try again later"
    
@app.route('/invalidate', methods=['POST'])
def removeBookFromCache():
    book = request.json

    with open("cache.json", "r") as file:
        data = json.load(file)

    data["books"].pop(str(book["id"]), None)
    data["topics"].pop(book["topic"], None)
    
    with open("cache.json", "w") as file:
        json.dump(data, file)

    return flask.Response(status=200) 

def bookFoundInCache(id):
    
    with open("cache.json", "r") as file:
        data = json.load(file) 

    if id in data["books"]:
        return data["books"][id]

    return None        

def topicFoundInCache(topic):
    booksList = []
    
    with open("cache.json", "r") as file:
        data = json.load(file) 
    if topic in data['topics']:
        for book in data['topics'][topic]: 
            booksList.append(data['books'][book])
        return booksList

    return None  
    
def addBookToCache(book):   

    with open("cache.json", "r") as file:
        data = json.load(file)

    if book["id"] in data["books"]:
        return

    data["books"][book["id"]] = book

    with open("cache.json", "w") as file:
        json.dump(data, file)

def addTopicToCache(topic, books):   
    with open("cache.json", "r") as file:
            data = json.load(file)

    data["topics"][topic] = books

    with open("cache.json", "w") as file:
        json.dump(data, file)  

def formatInfoResponse(response):
    res = divider
    res +=  "id      : "+str(response["id"]) + "\n" 
    res +=  "title   : "+response["title"] + "\n" 
    res +=  "price   : "+str(response["price"])+ "\n" 
    res +=  "quantity: "+str(response["quantity"]) 
    res += divider    
    return res

def formatTopicResponse(response):
    res = divider
    for book in response:
        res += "id    : "+str(book["id"]) + "\n" 
        res += "title : "+book["title"] 
        res += divider
    return res

if __name__ == '__main__':
    #app.run(debug=True, host='0.0.0.0', threaded=True)
    app.run(debug=False, port ='3000', threaded=True)
