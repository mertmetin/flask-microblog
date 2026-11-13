import os

class Configuration(object):
    MONGODB_SETTINGS = {
        'DB': 'mertmetin',
        'PORT': 27018
    }
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me')
