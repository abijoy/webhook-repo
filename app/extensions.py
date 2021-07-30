from flask_pymongo import PyMongo
from flask import Flask

app = Flask(__name__)

print(app)

mongo = PyMongo(app, uri="mongodb://localhost:27017/webhooktest")
db = mongo.db 
# mongo = PyMongo(webhook)
