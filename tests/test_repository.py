from contextlib import contextmanager
from datetime import datetime, timezone

from support_app.domain import Priority, Status
from support_app.repository import SupportRepository

NOW = datetime(2026, 8, 4, 18, 0, tzinfo=timezone.utc)


class FakeCursor:
    def __init__(self, results):
        self.results = list(results)
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.executions.append((str(query), params))

    def fetchall(self):
        return self.results.pop(0)

    def fetchone(self):
        return self.results.pop(0)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class FakePool:
    def __init__(self, cursor):
        self.cursor = cursor

    @contextmanager
    def connection(self):
        yield FakeConnection(self.cursor)


def ticket_row(ticket_id=7, status="open"):
    return {
        "ticket_id": ticket_id,
        "title": "Dashboard access",
        "status": status,
        "priority": "high",
        "created_by": "analyst@example.com",
        "created_at": NOW,
    }


def test_list_tickets_filters_by_status_and_returns_domain_records():
    cursor = FakeCursor([[ticket_row()]])
    repository = SupportRepository(FakePool(cursor))

    tickets = repository.list_tickets(Status.OPEN)

    assert tickets[0].ticket_id == 7
    assert tickets[0].priority is Priority.HIGH
    assert "WHERE status = %s" in cursor.executions[0][0]
    assert cursor.executions[0][1] == ("open",)


def test_list_tickets_can_return_all_statuses():
    cursor = FakeCursor([[ticket_row()]])
    repository = SupportRepository(FakePool(cursor))

    repository.list_tickets()

    assert "WHERE status" not in cursor.executions[0][0]
    assert cursor.executions[0][1] is None


def test_create_ticket_uses_parameterized_values_and_returns_created_ticket():
    cursor = FakeCursor([ticket_row(ticket_id=11)])
    repository = SupportRepository(FakePool(cursor))

    created = repository.create_ticket(
        title="Dashboard access",
        priority=Priority.HIGH,
        created_by="analyst@example.com",
    )

    assert created.ticket_id == 11
    assert cursor.executions[0][1] == (
        "Dashboard access",
        "high",
        "analyst@example.com",
    )


def test_add_message_links_message_to_ticket():
    row = {
        "message_id": 25,
        "ticket_id": 7,
        "message_text": "I still cannot sign in.",
        "author": "analyst@example.com",
        "created_at": NOW,
    }
    cursor = FakeCursor([row])
    repository = SupportRepository(FakePool(cursor))

    message = repository.add_message(
        ticket_id=7,
        message_text="I still cannot sign in.",
        author="analyst@example.com",
    )

    assert message.ticket_id == 7
    assert cursor.executions[0][1] == (
        7,
        "I still cannot sign in.",
        "analyst@example.com",
    )


def test_update_ticket_status_returns_updated_ticket():
    cursor = FakeCursor([ticket_row(status="resolved")])
    repository = SupportRepository(FakePool(cursor))

    updated = repository.update_status(7, Status.RESOLVED)

    assert updated.status is Status.RESOLVED
    assert cursor.executions[0][1] == ("resolved", 7)


def test_get_messages_returns_conversation_in_repository_order():
    rows = [
        {
            "message_id": 1,
            "ticket_id": 7,
            "message_text": "First update",
            "author": "analyst@example.com",
            "created_at": NOW,
        },
        {
            "message_id": 2,
            "ticket_id": 7,
            "message_text": "Second update",
            "author": "support@example.com",
            "created_at": NOW,
        },
    ]
    cursor = FakeCursor([rows])
    repository = SupportRepository(FakePool(cursor))

    messages = repository.get_messages(7)

    assert [message.message_text for message in messages] == ["First update", "Second update"]
    assert cursor.executions[0][1] == (7,)


def test_initialize_creates_foreign_key_and_seeds_three_tickets_with_six_messages():
    cursor = FakeCursor(
        [
            {"count": 0},
            {"ticket_id": 1},
            {"ticket_id": 2},
            {"ticket_id": 3},
        ]
    )
    repository = SupportRepository(FakePool(cursor))

    repository.initialize()

    sql = "\n".join(query for query, _params in cursor.executions)
    ticket_inserts = [
        query for query, _params in cursor.executions if "INSERT INTO support.tickets" in query
    ]
    message_inserts = [
        query
        for query, _params in cursor.executions
        if "INSERT INTO support.ticket_messages" in query
    ]
    assert "REFERENCES support.tickets(ticket_id)" in sql
    assert len(ticket_inserts) == 3
    assert len(message_inserts) == 6


def test_ticket_statistics_include_all_statuses_and_total():
    cursor = FakeCursor([[{"status": "open", "count": 2}, {"status": "resolved", "count": 1}]])
    repository = SupportRepository(FakePool(cursor))

    stats = repository.ticket_statistics()

    assert stats == {"total": 3, "open": 2, "in_progress": 0, "resolved": 1}
