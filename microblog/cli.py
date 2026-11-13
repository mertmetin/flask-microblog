"""flask create-user / flask seed"""

from __future__ import annotations

import click
from flask import Flask
from sqlalchemy import select

from .extensions import db
from .models import Comment, Post, User


def register(app: Flask) -> None:
    @app.cli.command("create-user")
    @click.argument("username")
    @click.password_option()
    def create_user(username: str, password: str) -> None:
        """Create the author account (there's no public sign-up)."""
        if db.session.scalar(select(User).where(User.username == username)):
            raise click.ClickException(f"{username} already exists")
        user = User(username=username)
        try:
            user.set_password(password)
        except ValueError as e:
            raise click.ClickException(str(e)) from e
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created {username}")

    @app.cli.command("seed")
    def seed() -> None:
        """Add demo posts and comments (for local development)."""
        # No built-in demo account: a password in public code would be a known login.
        author = db.session.scalar(select(User))
        if author is None:
            raise click.ClickException("Create an author first: flask --app microblog create-user <name>")
        for title, body in DEMO_POSTS:
            if not db.session.scalar(select(Post).where(Post.title == title)):
                db.session.add(Post(title=title, body=body, slug=Post.unique_slug(title), author=author))
                db.session.flush()
        first = db.session.scalar(select(Post).order_by(Post.id))
        if first and not first.comments:
            first.comments.append(Comment(author="Ada", body="Great write-up, thanks!", status="approved"))
            first.comments.append(
                Comment(
                    author="CheapPills",
                    body="BUY NOW http://spam.example click here",
                    status="spam",
                    spam_score=5,
                    spam_reasons="contains a link; spam phrases: buy now, click here",
                )
            )
        db.session.commit()
        click.echo(f"Seeded {len(DEMO_POSTS)} posts")


DEMO_POSTS = [
    (
        "Rebuilding a blog I wrote in 2014",
        "In 2014 this was a Flask app on MongoDB that I never finished: no login, comments that didn't save, "
        "and post bodies printed straight into the page.\n\n"
        "## What changed\n\n"
        "- **Passwords** are salted hashes instead of plain text.\n"
        "- **Every form** carries a CSRF token.\n"
        "- **Markdown** is rendered and then sanitised, so a post can't run scripts.\n"
        "- **Comments** go through a small, explainable spam filter.\n",
    ),
    (
        "Why I sanitise Markdown even on my own blog",
        "Rendering Markdown is easy; rendering it *safely* takes one more step. Markdown allows raw HTML, so a "
        "`<script>` tag or an `onerror` attribute can ride along. An allow-list cleaner keeps only the tags and "
        "attributes you expect, and only `http`, `https` and `mailto` links.\n\n"
        "Even if you're the only author, comments and pasted snippets are not.",
    ),
    (
        "A spam filter you can explain",
        "Instead of a black box, every comment gets points with reasons: links, spam phrases, a filled honeypot "
        "field, a form submitted in under three seconds. Three points and it's spam; one or two and it waits for "
        "review. The moderation page shows the reasons, so false positives are easy to spot.",
    ),
    (
        "Related posts with TF-IDF in fifty lines",
        "Each post becomes a vector of word weights: words common in that post but rare across the blog weigh the "
        "most. Cosine similarity between vectors finds related posts, and the same index answers search queries. "
        "No search server, no ML library, and fast enough for a few hundred posts.",
    ),
    (
        "Flask, then and now",
        "Flask in 2014 meant `flask.ext.*` imports, Flask-Script and Python 2. Today it's application factories, "
        "blueprints, SQLAlchemy 2 typed models and `flask` CLI commands. The ideas held up; the plumbing got much "
        "better.",
    ),
]
