"""Users, posts and comments (SQLAlchemy 2.0 style)."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime

from flask_login import UserMixin
from sqlalchemy import ForeignKey, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80] or "post"


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    # 2014 stored a plain-text password in a 40-character field. Now: a salted hash.
    password_hash: Mapped[str] = mapped_column(String(256))
    posts: Mapped[list[Post]] = relationship(back_populates="author")

    def set_password(self, password: str) -> None:
        if len(password) < 10:
            raise ValueError("Use at least 10 characters")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    author: Mapped[User] = relationship(back_populates="posts")
    comments: Mapped[list[Comment]] = relationship(
        back_populates="post", cascade="all, delete-orphan", order_by="Comment.created_at"
    )

    @staticmethod
    def unique_slug(title: str, exclude_id: int | None = None) -> str:
        base = slugify(title)
        slug, n = base, 2
        while True:
            existing = db.session.scalar(select(Post).where(Post.slug == slug))
            if existing is None or existing.id == exclude_id:
                return slug
            slug, n = f"{base}-{n}", n + 1

    @property
    def approved_comments(self) -> list[Comment]:
        return [c for c in self.comments if c.status == "approved"]

    @property
    def reading_minutes(self) -> int:
        return max(1, round(len(self.body.split()) / 220))


class Comment(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), index=True)
    post: Mapped[Post] = relationship(back_populates="comments")
    author: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    # approved | pending (held for review) | spam
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)
    spam_score: Mapped[float] = mapped_column(default=0.0)
    spam_reasons: Mapped[str] = mapped_column(String(300), default="")
