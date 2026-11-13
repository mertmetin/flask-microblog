from flask.ext.mongoengine import MongoEngine
from app import db

class User(db.Document):
    username = db.StringField(unique = True, required = True, max_length=40)
    password = db.StringField(max_length=40)

