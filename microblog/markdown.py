"""Markdown → safe HTML.

The 2014 templates printed post bodies with `|safe`, so any HTML in a post
ran in readers' browsers. Now Markdown is rendered and then sanitised with
nh3 (an allow-list HTML cleaner): no scripts, no event handlers, no
javascript: links.
"""

from __future__ import annotations

import nh3
from markdown_it import MarkdownIt
from markupsafe import Markup

_md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": True}).enable("table")

_TAGS = {
    "p", "br", "hr", "h2", "h3", "h4", "strong", "em", "del", "code", "pre", "blockquote",
    "ul", "ol", "li", "a", "img", "table", "thead", "tbody", "tr", "th", "td",
}  # fmt: skip
_ATTRS = {"a": {"href", "title"}, "img": {"src", "alt", "title"}}


def render_markdown(text: str) -> Markup:
    html = _md.render(text or "")
    clean = nh3.clean(
        html,
        tags=_TAGS,
        attributes=_ATTRS,
        url_schemes={"http", "https", "mailto"},
        link_rel="nofollow noopener noreferrer",
    )
    return Markup(clean)
