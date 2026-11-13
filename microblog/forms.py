from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=40)])
    password = PasswordField("Password", validators=[DataRequired()])


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("Body (Markdown)", validators=[DataRequired()])


class CommentForm(FlaskForm):
    author = StringField("Name", validators=[DataRequired(), Length(max=80)])
    body = TextAreaField("Comment", validators=[DataRequired(), Length(max=4000)])
    # Honeypot: hidden from people by CSS, irresistible to bots.
    website = StringField("Website")
    # When the form was rendered, so instant submissions look suspicious.
    rendered_at = HiddenField()
