"""Shared helpers for Celery task logging."""

from __future__ import annotations

import logging

logger = logging.getLogger("jobs.tasks")


def task_display_name(task_or_sender) -> str:
    name = getattr(task_or_sender, "name", None) or str(task_or_sender or "unknown")
    return name.rsplit(".", maxsplit=1)[-1]


def truncate_for_log(value, max_len: int = 200) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}…"
