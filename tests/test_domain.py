from support_app.domain import (
    Priority,
    Status,
    ValidationError,
    actor_email,
    forwarded_email,
    validate_message,
    validate_ticket,
)


def test_validate_ticket_normalizes_valid_input():
    result = validate_ticket(
        title="  Cannot access dashboard  ",
        priority="high",
        created_by=" analyst@example.com ",
    )

    assert result == {
        "title": "Cannot access dashboard",
        "priority": Priority.HIGH,
        "created_by": "analyst@example.com",
    }


def test_validate_ticket_rejects_blank_title():
    try:
        validate_ticket(title="   ", priority="medium", created_by="a@example.com")
    except ValidationError as error:
        assert error.messages == ["Title is required."]
    else:
        raise AssertionError("Expected blank title to be rejected")


def test_validate_ticket_rejects_title_longer_than_database_column():
    try:
        validate_ticket(title="x" * 201, priority="medium", created_by="a@example.com")
    except ValidationError as error:
        assert error.messages == ["Title must be 200 characters or fewer."]
    else:
        raise AssertionError("Expected an oversized title to be rejected")


def test_validate_ticket_reports_invalid_priority_helpfully():
    try:
        validate_ticket(title="A ticket", priority="critical", created_by="a@example.com")
    except ValidationError as error:
        assert error.messages == ["Choose a valid priority."]
    else:
        raise AssertionError("Expected invalid priority to be rejected")


def test_validate_message_rejects_blank_message():
    try:
        validate_message(message_text="\n", author="a@example.com")
    except ValidationError as error:
        assert error.messages == ["Message is required."]
    else:
        raise AssertionError("Expected blank message to be rejected")


def test_validate_message_rejects_oversized_message():
    try:
        validate_message(message_text="x" * 5001, author="a@example.com")
    except ValidationError as error:
        assert error.messages == ["Message must be 5,000 characters or fewer."]
    else:
        raise AssertionError("Expected an oversized message to be rejected")


def test_actor_email_prefers_forwarded_databricks_identity():
    assert (
        actor_email(
            {"X-Forwarded-Email": "signed.in@example.com"},
            fallback="local@example.com",
        )
        == "signed.in@example.com"
    )


def test_actor_email_uses_local_fallback_when_header_missing():
    assert actor_email({}, fallback="local@example.com") == "local@example.com"


def test_forwarded_email_header_lookup_is_case_insensitive():
    assert forwarded_email({"x-FoRwArDeD-eMaIl": "user@example.com"}) == "user@example.com"


def test_status_and_priority_values_match_database_contract():
    assert [status.value for status in Status] == ["open", "in_progress", "resolved"]
    assert [priority.value for priority in Priority] == ["low", "medium", "high", "urgent"]
