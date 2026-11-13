from flask import abort
from flask.ext.admin import (Admin,AdminIndexView as _AdminIndexView, expose)
from flask.ext.security import current_user
from flask.ext.admin.contrib.mongoengine import ModelView

from app import app, db
from blog.models import Post, Comment
from user.models import User


class AdminIndexView(_AdminIndexView):
    @expose('/')
    def index(self):
        return self.render(self._template)



admin = Admin(name='Index', index_view=AdminIndexView())
admin.add_view(ModelView(Post))
admin.add_view(ModelView(Comment))
admin.add_view(ModelView(User))

                         
admin.init_app(app)
