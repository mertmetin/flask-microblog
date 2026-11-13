"""Comment spam scoring.

A small, explainable score instead of a black box: each signal adds points
and a reason. Comments scoring 3 or more are marked spam; 1–2 are held for
review; 0 is published. The reasons are stored so the moderation screen can
show *why* something was held.

Signals are the ones that catch most real blog spam: links, money/pill
keywords, shouting, repeated characters, a filled honeypot field (a hidden
input people never see but bots fill in), and a form submitted faster than a
person could type.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SPAM_AT = 3.0
REVIEW_AT = 1.0

_KEYWORDS = re.compile(
    r"\b(viagra|cialis|casino|crypto ?(?:giveaway|airdrop)|bitcoin doubler|loan offer|payday|"
    r"free money|work from home|earn \$?\d+|click here|buy now|seo services|backlinks?)\b",
    re.I,
)
_LINK = re.compile(r"https?://|www\.", re.I)


@dataclass
class SpamResult:
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    def add(self, points: float, reason: str) -> None:
        self.score += points
        self.reasons.append(reason)

    @property
    def status(self) -> str:
        if self.score >= SPAM_AT:
            return "spam"
        if self.score >= REVIEW_AT:
            return "pending"
        return "approved"


def score_comment(
    body: str, author: str = "", *, honeypot: str = "", seconds_to_submit: float | None = None
) -> SpamResult:
    result = SpamResult()
    text = f"{author} {body}"

    if honeypot.strip():
        result.add(5, "filled the hidden field")
    if seconds_to_submit is not None and seconds_to_submit < 3:
        result.add(2, f"submitted in {seconds_to_submit:.1f}s")

    links = len(_LINK.findall(text))
    if links >= 3:
        result.add(3, f"{links} links")
    elif links:
        result.add(1, "contains a link")

    keywords = {m.group(0).lower() for m in _KEYWORDS.finditer(text)}
    if keywords:
        result.add(2 * len(keywords), "spam phrases: " + ", ".join(sorted(keywords)))

    letters = [c for c in body if c.isalpha()]
    if len(letters) >= 20 and sum(c.isupper() for c in letters) / len(letters) > 0.6:
        result.add(1, "mostly capitals")
    if re.search(r"(.)\1{7,}", body):
        result.add(1, "repeated characters")
    if len(body.strip()) < 2:
        result.add(1, "empty")
    return result
