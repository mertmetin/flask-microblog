from __future__ import annotations

import time

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from .extensions import db
from .forms import CommentForm, PostForm
from .models import Comment, Post
from .similarity import Index
from .spam import score_comment

bp = Blueprint("blog", __name__)


def _index() -> Index:
    rows = db.session.execute(select(Post.id, Post.title, Post.body)).all()
    return Index(rows)


@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    posts = db.paginate(
        select(Post).order_by(Post.created_at.desc()), page=page, per_page=current_app.config["POSTS_PER_PAGE"]
    )
    return render_template("blog/index.html", posts=posts)


@bp.route("/posts/<slug>", methods=["GET", "POST"])
def post(slug: str):
    post = db.session.scalar(select(Post).where(Post.slug == slug)) or abort(404)
    form = CommentForm()

    if form.validate_on_submit():
        try:
            elapsed = time.time() - float(form.rendered_at.data or 0)
        except ValueError:
            elapsed = None
        result = score_comment(
            form.body.data, form.author.data, honeypot=form.website.data or "", seconds_to_submit=elapsed
        )
        db.session.add(
            Comment(
                post=post,
                author=form.author.data.strip(),
                body=form.body.data.strip(),
                status=result.status,
                spam_score=result.score,
                spam_reasons="; ".join(result.reasons),
            )
        )
        db.session.commit()
        if result.status == "approved":
            flash("Thanks! Your comment is up.", "ok")
        else:
            # Same message for "held" and "spam", so spammers learn nothing.
            flash("Thanks! Your comment is waiting for review.", "ok")
        return redirect(url_for("blog.post", slug=post.slug) + "#comments")

    form.rendered_at.data = str(time.time())
    related_ids = [i for i, _ in _index().related(post.id)]
    related = [db.session.get(Post, i) for i in related_ids]
    return render_template("blog/post.html", post=post, form=form, related=related)


@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()[:200]
    results = []
    if q:
        results = [(db.session.get(Post, i), score) for i, score in _index().search(q)]
    return render_template("blog/search.html", q=q, results=results)


@bp.route("/write", methods=["GET", "POST"])
@login_required
def create():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data.strip(),
            body=form.body.data,
            slug=Post.unique_slug(form.title.data),
            author=current_user,
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("blog.post", slug=post.slug))
    return render_template("blog/edit.html", form=form, post=None)


@bp.route("/posts/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit(slug: str):
    post = db.session.scalar(select(Post).where(Post.slug == slug)) or abort(404)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data.strip()
        post.body = form.body.data
        post.slug = Post.unique_slug(post.title, exclude_id=post.id)
        db.session.commit()
        return redirect(url_for("blog.post", slug=post.slug))
    return render_template("blog/edit.html", form=form, post=post)


@bp.post("/posts/<slug>/delete")
@login_required
def delete(slug: str):
    post = db.session.scalar(select(Post).where(Post.slug == slug)) or abort(404)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "ok")
    return redirect(url_for("blog.index"))


@bp.route("/moderate")
@login_required
def moderate():
    held = db.session.scalars(
        select(Comment).where(Comment.status != "approved").order_by(Comment.created_at.desc())
    ).all()
    counts = dict(db.session.execute(select(Comment.status, func.count()).group_by(Comment.status)).all())
    return render_template("blog/moderate.html", comments=held, counts=counts)


@bp.post("/comments/<int:comment_id>/<action>")
@login_required
def moderate_comment(comment_id: int, action: str):
    comment = db.session.get(Comment, comment_id) or abort(404)
    if action == "approve":
        comment.status = "approved"
    elif action == "delete":
        db.session.delete(comment)
    else:
        abort(400)
    db.session.commit()
    return redirect(request.referrer or url_for("blog.moderate"))
