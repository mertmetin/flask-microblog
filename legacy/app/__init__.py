from flask import Flask
from flask.ext.mongoengine import MongoEngine



app = Flask(__name__)
app.config.from_object('config.Configuration')

#Database
db = MongoEngine()
db.init_app(app)


#Admin
import admin

import blog.views as blog
app.register_blueprint(blog.bl)


# Endpoints
@app.route('/')
def index():
    return render_template('posts/list.html')



