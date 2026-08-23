"""Conservative helpers for gender display and work-record merge review."""
from __future__ import annotations

import re

_VOLUME_RE = re.compile(r"[﹕:：]?\s*[一二三四五六七八九十百千\d]+\s*卷")


def classify_gender(cbdb_female: str | int | None) -> str:
    """Return a three-state display class; never infer sex from a person's name."""
    if str(cbdb_female).strip() == "1":
        return "female"
    if str(cbdb_female).strip() == "0":
        return "male"
    return "unknown"


def normalize_title_without_volumes(title: str) -> str:
    """Remove explicit volume counts while preserving title, author, and other wording."""
    normalized = _VOLUME_RE.sub("", (title or "").strip())
    normalized = re.sub(r"[﹕:：]\s*(?=[﹐，,；;附(])", "", normalized)
    return re.sub(r"\s+", "", normalized)


def merge_decision(left: dict[str, str], right: dict[str, str]) -> str:
    """Only nominate records identical outside volume count for human review."""
    comparable = ("title_key", "worktype", "publisher", "place", "pub_statement")
    if all((left.get(field) or "").strip() == (right.get(field) or "").strip() for field in comparable):
        return "candidate_merge_review" if (left.get("volume") or "") != (right.get("volume") or "") else "possible_duplicate_review"
    return "keep_separate"
