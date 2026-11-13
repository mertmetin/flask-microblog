from __future__ import annotations

from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from sqlalchemy import select

from .extensions import db
from .forms import LoginForm
from .models import User

bp = Blueprint("auth", __name__)


def _safe_next(target: str | None) -> str:
    # Only follow relative paths, so ?next= can't send people to another site.
    if target and not urlsplit(target).netloc and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("blog.index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.username == form.username.data))
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(_safe_next(request.args.get("next")))
        flash("Wrong username or password.", "error")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("blog.index"))
