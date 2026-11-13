import pytest

from microblog import create_app
from microblog.extensions import db
from microblog.models import Post, User


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"}
    )
    with app.app_context():
        author = User(username="mert")
        author.set_password("correct horse battery")
        db.session.add(author)
        db.session.add_all(
            [
                Post(
                    title="Hybrid search with BM25",
                    slug="bm25",
                    body="Keyword search and BM25 ranking for products.",
                    author=author,
                ),
                Post(
                    title="Semantic search with embeddings",
                    slug="embeddings",
                    body="Embeddings make search understand meaning; hybrid search mixes BM25 and embeddings.",
                    author=author,
                ),
                Post(title="Baking sourdough", slug="bread", body="Flour, water, salt and patience.", author=author),
            ]
        )
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in(client):
    client.post("/login", data={"username": "mert", "password": "correct horse battery"})
    return client
