# flask-microblog

[![CI](https://github.com/mertmetin/flask-microblog/actions/workflows/ci.yml/badge.svg)](https://github.com/mertmetin/flask-microblog/actions/workflows/ci.yml)

**A small, secure Flask blog: Markdown posts, comments with an explainable spam filter, related posts and search.**

I started this in 2014 while learning Flask and never finished it. In 2026 I came back and finished it properly. The original code is preserved in [`legacy/`](legacy/), and the gap between the two is the point of this repo.

## 2014 vs 2026

| | 2014 | 2026 |
|---|---|---|
| Stack | Flask + `flask.ext.*`, MongoEngine, Flask-Script, Python 2 | Flask 3 app factory and blueprints, SQLAlchemy 2 typed models, SQLite, Python 3.12 |
| Passwords | Stored as plain text in a 40-character field | Salted hashes (Werkzeug), 10-character minimum |
| Login | None | Flask-Login, author-only, `flask create-user` (no public sign-up) |
| Forms | No CSRF protection | CSRF token on every form (Flask-WTF) |
| Post bodies | Printed with `\|safe`, so any HTML in a post ran in readers' browsers | Markdown rendered, then sanitised with an allow-list (nh3); raw HTML shows as text |
| Comments | Form not wired up; the model had no comments field | Working comments, a spam filter and a moderation queue |
| Home route | Crashed (`render_template` was never imported) | Paginated posts |
| Design | A copied blog theme still linking to someone else's site | My own, light and dark mode, no inline scripts or styles |
| Headers | Defaults | Strict Content-Security-Policy, no framing, nosniff |
| Secret key | Committed to the repo | From the environment; required in production |
| Tests / CI | None | 20 tests, lint and format checks on every push |

## Features

- **Markdown posts** with clean URLs, edit and delete, reading time, pagination.
- **Comments with an explainable spam filter.** Each comment gets points with reasons: links, spam phrases, shouting, repeated characters, a filled **honeypot** field (hidden from people, irresistible to bots), and a form **submitted in under three seconds**. Three points or more is spam, one or two waits for review, zero is published. The moderation page shows the reasons, so false positives are easy to spot. Held and spam comments get the same "waiting for review" message, so spammers learn nothing.
- **Related posts and search** from a small **TF-IDF** index written from scratch ([`similarity.py`](microblog/similarity.py)): each post becomes a vector of word weights, related posts are the nearest by cosine similarity, and search scores posts against the query the same way. No search server, no ML library.
- **Security by default:** hashed passwords, CSRF, sanitised Markdown with `nofollow` links and only `http`/`https`/`mailto` URLs, safe `?next=` redirects, secure session cookies in production, and a strict CSP.

## Run it

```bash
uv venv && uv pip install -e ".[dev]"
flask --app microblog create-user mert   # prompts for a password
flask --app microblog seed               # optional demo posts and comments
flask --app microblog run --debug        # http://127.0.0.1:5000
pytest
```

With Docker:

```bash
docker build -t microblog .
docker run -p 8000:8000 -e SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))') \
  -v microblog-data:/app/instance microblog
```

## Layout

```
microblog/
  __init__.py     app factory, config, security headers
  models.py       User, Post, Comment (SQLAlchemy 2)
  auth.py         sign in / out
  blog.py         posts, comments, search, moderation
  spam.py         the comment spam score
  similarity.py   TF-IDF related posts and search
  markdown.py     Markdown → sanitised HTML
  cli.py          flask create-user, flask seed
legacy/           the 2014 version, unchanged except for the secret key
tests/            security, posts, comments, spam, related posts, search
```

The 2014 templates were adapted from the s9y "2k11" blog theme; they remain in `legacy/` for history only.

## License

MIT
