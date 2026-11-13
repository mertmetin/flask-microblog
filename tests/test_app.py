import re
import time

import pytest

from microblog import create_app
from microblog.extensions import db
from microblog.markdown import render_markdown
from microblog.models import Comment, Post, User
from microblog.similarity import Index
from microblog.spam import score_comment

# --------------------------------------------------------------------------- security


def test_passwords_are_hashed_not_stored(app):
    with app.app_context():
        user = db.session.query(User).filter_by(username="mert").one()
        assert "correct horse" not in user.password_hash
        assert user.check_password("correct horse battery")
        assert not user.check_password("wrong")
        with pytest.raises(ValueError):
            user.set_password("short")


@pytest.mark.parametrize(
    "markdown",
    [
        "<script>alert(1)</script>",
        '<img src=x onerror="alert(1)">',
        "[click](javascript:alert(1))",
        '<a href="https://x" onclick="steal()">x</a>',
        "![x](javascript:alert(1))",
    ],
)
def test_markdown_is_sanitised(markdown):
    # 2014 printed post bodies with |safe. Now raw HTML is shown as text, and
    # no real tag, event handler or javascript: URL reaches the page.
    html = str(render_markdown(markdown))
    assert "<script" not in html and "<img" not in html
    assert not re.search(r"<[a-z][^>]*\son\w+\s*=", html, re.I)
    assert not re.search(r"(href|src)=\"\s*javascript:", html, re.I)


def test_markdown_keeps_formatting_and_marks_links_nofollow():
    html = render_markdown("**bold** and [a link](https://example.com)\n\n```\ncode\n```")
    assert "<strong>bold</strong>" in html and "<pre><code>" in html
    assert 'rel="nofollow noopener noreferrer"' in html


def test_writing_requires_login(client):
    assert client.get("/write").status_code == 302
    assert client.post("/write", data={"title": "x", "body": "y"}).status_code == 302
    assert client.get("/moderate").status_code == 302


def test_wrong_password_is_rejected(client):
    r = client.post("/login", data={"username": "mert", "password": "nope"}, follow_redirects=True)
    assert b"Wrong username or password" in r.data
    assert client.get("/write").status_code == 302


def test_login_does_not_redirect_offsite(client):
    r = client.post("/login?next=https://evil.example", data={"username": "mert", "password": "correct horse battery"})
    assert r.headers["Location"] == "/"


def test_csrf_is_enforced_when_enabled(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'c.db'}"})
    assert app.test_client().post("/login", data={"username": "a", "password": "b"}).status_code == 400


def test_security_headers(client):
    r = client.get("/")
    assert "script-src 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Frame-Options"] == "DENY"


# --------------------------------------------------------------------------- posts


def test_author_can_publish_edit_and_delete(logged_in, app):
    r = logged_in.post("/write", data={"title": "Hello, World!", "body": "First *post*"})
    assert r.headers["Location"] == "/posts/hello-world"
    assert b"<em>post</em>" in logged_in.get("/posts/hello-world").data

    logged_in.post("/posts/hello-world/edit", data={"title": "Hello again", "body": "Edited"})
    assert logged_in.get("/posts/hello-again").status_code == 200

    logged_in.post("/posts/hello-again/delete")
    assert logged_in.get("/posts/hello-again").status_code == 404


def test_duplicate_titles_get_unique_slugs(logged_in):
    first = logged_in.post("/write", data={"title": "Same title", "body": "a"}).headers["Location"]
    second = logged_in.post("/write", data={"title": "Same title", "body": "b"}).headers["Location"]
    assert first == "/posts/same-title" and second == "/posts/same-title-2"


# --------------------------------------------------------------------------- comments and spam


def comment(client, body, author="Ada", **extra):
    data = {"author": author, "body": body, "rendered_at": str(time.time() - 30), **extra}
    return client.post("/posts/bm25", data=data, follow_redirects=True)


def test_clean_comment_is_published(client, app):
    r = comment(client, "Really clear explanation, thanks!")
    assert b"Your comment is up" in r.data and b"Really clear explanation" in r.data


def test_spam_is_held_and_hidden(client, app):
    r = comment(client, "BUY NOW cheap viagra http://a.example http://b.example http://c.example click here")
    assert b"waiting for review" in r.data
    assert b"viagra" not in r.data
    with app.app_context():
        c = db.session.query(Comment).one()
        assert c.status == "spam" and "links" in c.spam_reasons


def test_honeypot_and_instant_submit_are_caught():
    assert score_comment("hello there", honeypot="http://x").status == "spam"
    assert score_comment("hello there", seconds_to_submit=0.4).status == "pending"
    assert score_comment("hello there", seconds_to_submit=20).status == "approved"


def test_author_can_approve_held_comment(logged_in, app):
    comment(logged_in, "see https://my-site.example")  # one link: held for review
    with app.app_context():
        held = db.session.query(Comment).one()
        assert held.status == "pending"
        comment_id = held.id
    logged_in.post(f"/comments/{comment_id}/approve")
    with app.app_context():
        assert db.session.get(Comment, comment_id).status == "approved"


# --------------------------------------------------------------------------- related posts and search


def test_related_posts_share_topics(app):
    with app.app_context():
        index = Index((p.id, p.title, p.body) for p in db.session.query(Post))
        bm25 = db.session.query(Post).filter_by(slug="bm25").one()
        related = [db.session.get(Post, i).slug for i, _ in index.related(bm25.id)]
    assert related[0] == "embeddings"
    assert "bread" not in related


def test_search_ranks_by_relevance(client):
    r = client.get("/search?q=embeddings")
    page = r.data.decode()
    assert page.index("Semantic search with embeddings") < (page.find("Hybrid search with BM25") % (len(page) + 1))
    assert "Baking sourdough" not in page
