from flask import Blueprint, render_template, request, redirect, url_for
from models import Post, Comment
from app import db


POST_PER_PAGE = 1

bl = Blueprint('blog', __name__,  template_folder='templates')


@bl.route('/')
def index():
	page = int(request.args.get('page', 1))
	posts = Post.objects.paginate(page = page, per_page = POST_PER_PAGE)
	return render_template('posts/list.html', posts = posts)


@bl.route('/archives/<slug>/')
def detail(slug):
    try:
        post = Post.objects.get_or_404(slug=slug)
    except:
        pass 
    
    return render_template('posts/detail.html', post=post)
