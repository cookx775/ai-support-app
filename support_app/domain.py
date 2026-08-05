from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Optional


class Status(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ValidationError(ValueError):
    def __init__(self, messages: list[str]):
        super().__init__(" ".join(messages))
        self.messages = messages


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValidationError([f"{label} is required."])
    return normalized


def _limited(value: str, label: str, maximum: int) -> str:
    normalized = _required(value, label)
    if len(normalized) > maximum:
        formatted_maximum = f"{maximum:,}"
        raise ValidationError([f"{label} must be {formatted_maximum} characters or fewer."])
    return normalized


def validate_ticket(*, title: str, priority: str, created_by: str) -> dict[str, object]:
    try:
        selected_priority = Priority(priority)
    except ValueError as error:
        raise ValidationError(["Choose a valid priority."]) from error
    return {
        "title": _limited(title, "Title", 200),
        "priority": selected_priority,
        "created_by": _limited(created_by, "Created by", 320),
    }


def validate_message(*, message_text: str, author: str) -> dict[str, str]:
    return {
        "message_text": _limited(message_text, "Message", 5_000),
        "author": _limited(author, "Author", 320),
    }


def actor_email(headers: Mapping[str, str], fallback: Optional[str] = None) -> str:
    forwarded = next(
        (value for key, value in headers.items() if key.lower() == "x-forwarded-email"),
        None,
    )
    candidate = forwarded or fallback or ""
    return _required(candidate, "Author")
