from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .domain import Priority, Status


@dataclass(frozen=True)
class Ticket:
    ticket_id: int
    title: str
    status: Status
    priority: Priority
    created_by: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Ticket:
        return cls(
            ticket_id=row["ticket_id"],
            title=row["title"],
            status=Status(row["status"]),
            priority=Priority(row["priority"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
        )


@dataclass(frozen=True)
class TicketMessage:
    message_id: int
    ticket_id: int
    message_text: str
    author: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> TicketMessage:
        return cls(
            message_id=row["message_id"],
            ticket_id=row["ticket_id"],
            message_text=row["message_text"],
            author=row["author"],
            created_at=row["created_at"],
        )
