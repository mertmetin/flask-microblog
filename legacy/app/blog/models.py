import datetime
from app import db

from app.user.models import User

class Post(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    author = db.ReferenceField(User)
    title = db.StringField(max_length=255, required=True)
    slug = db.StringField(max_length=255, required=True)
    body = db.StringField(required=True)

    def get_absolute_url(self):
        return url_for('post', kwargs={"slug": self.slug})
        
    def __unicode__(self):
        return self.title
        
    @property
    def post_type(self):
        return self.__class__.__name__
    
    meta = {
        'ordering': ['-created_at']
    }


class Comment(db.EmbeddedDocument):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    body = db.StringField(verbose_name="Comment", required=True)
    author = db.StringField(verbose_name="Name", max_length=255, required=True)
    
    def __unicode__(self):
        return self.author
