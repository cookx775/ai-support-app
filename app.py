from __future__ import annotations

import html
import logging
import os

import streamlit as st

from support_app.db import DatabaseConfigurationError, get_connection_pool
from support_app.domain import (
    Priority,
    Status,
    ValidationError,
    actor_email,
    forwarded_email,
    validate_message,
    validate_ticket,
)
from support_app.repository import RecordNotFound, SupportRepository

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

STATUS_LABELS = {
    Status.OPEN: "Open",
    Status.IN_PROGRESS: "In progress",
    Status.RESOLVED: "Resolved",
}
PRIORITY_LABELS = {
    Priority.LOW: "Low",
    Priority.MEDIUM: "Medium",
    Priority.HIGH: "High",
    Priority.URGENT: "Urgent",
}


st.set_page_config(
    page_title="AI Support Desk",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background: #f6f8fb; }
      [data-testid="stAppViewContainer"] { color: #111827; }
      [data-testid="stAppViewContainer"] h1,
      [data-testid="stAppViewContainer"] h2,
      [data-testid="stAppViewContainer"] h3,
      [data-testid="stAppViewContainer"] p { color: #111827; }
      [data-testid="stSidebar"] { background: #111827; }
      [data-testid="stSidebar"] * { color: #f9fafb; }
      .support-hero {
        padding: 1.4rem 1.6rem;
        border-radius: 18px;
        color: white;
        background: linear-gradient(125deg, #102a43, #1363df 72%, #36c5f0);
        margin-bottom: 1rem;
        box-shadow: 0 12px 30px rgba(16, 42, 67, .18);
      }
      .support-hero h1 { margin: 0; font-size: 2rem; }
      .support-hero h1, .support-hero p { color: white !important; }
      .support-hero p { margin: .35rem 0 0; opacity: .9; }
      .message-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #1363df;
        border-radius: 12px;
        margin: .55rem 0;
        padding: .8rem 1rem;
      }
      .message-meta { color: #64748b; font-size: .8rem; margin-bottom: .35rem; }
      .ticket-meta { color: #64748b; font-size: .9rem; }
      div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: .8rem 1rem;
      }
      div[data-testid="stMetric"] * { color: #111827 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def repository() -> SupportRepository:
    repo = SupportRepository(get_connection_pool())
    repo.initialize()
    return repo


def forwarded_headers() -> dict[str, str]:
    try:
        return dict(st.context.headers)
    except (AttributeError, RuntimeError):
        return {}


def flash_success(message: str) -> None:
    st.session_state["success_message"] = message
    st.rerun()


def show_flash() -> None:
    message = st.session_state.pop("success_message", None)
    if message:
        st.success(message)


def show_validation(error: ValidationError) -> None:
    for message in error.messages:
        st.error(message)


try:
    repo = repository()
except DatabaseConfigurationError as error:
    st.error(str(error))
    st.info("Attach the Lakebase resource and set ENDPOINT_NAME before deploying.")
    st.stop()
except Exception:
    logger.exception("Lakebase initialization failed")
    st.error("Lakebase is temporarily unavailable. Check the Databricks App logs and try again.")
    st.stop()

headers = forwarded_headers()
databricks_email = forwarded_email(headers)
local_identity = os.getenv("LOCAL_USER_EMAIL", "")

st.sidebar.markdown("## Create a ticket")
if not databricks_email:
    local_identity = st.sidebar.text_input(
        "Local development identity",
        value=local_identity,
        placeholder="you@example.com",
        help="Databricks supplies the signed-in email automatically after deployment.",
    )

with st.sidebar.form("create_ticket", clear_on_submit=True):
    new_title = st.text_input("Title", max_chars=200, placeholder="Briefly describe the issue")
    new_priority = st.selectbox(
        "Priority",
        options=list(Priority),
        index=1,
        format_func=lambda value: PRIORITY_LABELS[value],
    )
    create_submitted = st.form_submit_button("Create ticket", use_container_width=True)

if create_submitted:
    try:
        creator = actor_email(headers, local_identity)
        values = validate_ticket(
            title=new_title,
            priority=new_priority.value,
            created_by=creator,
        )
        created = repo.create_ticket(**values)
        flash_success(f"Ticket #{created.ticket_id} created.")
    except ValidationError as error:
        show_validation(error)
    except Exception:
        logger.exception("Ticket creation failed")
        st.sidebar.error("Could not create the ticket. Try again.")

st.markdown(
    """
    <section class="support-hero">
      <h1>AI Support Desk</h1>
      <p>Track requests, collaborate on messages, and keep operational context in Lakebase.</p>
    </section>
    """,
    unsafe_allow_html=True,
)
show_flash()

try:
    stats = repo.ticket_statistics()
except Exception:
    logger.exception("Ticket statistics failed")
    st.error("Could not load ticket statistics.")
    st.stop()

metric_columns = st.columns(4)
for column, label, key in zip(
    metric_columns,
    ("All tickets", "Open", "In progress", "Resolved"),
    ("total", "open", "in_progress", "resolved"),
):
    column.metric(label, stats[key])

st.markdown("### Ticket queue")
filter_label = st.radio(
    "Filter by status",
    options=["All", "Open", "In progress", "Resolved"],
    horizontal=True,
    label_visibility="collapsed",
)
filter_status = {
    "All": None,
    "Open": Status.OPEN,
    "In progress": Status.IN_PROGRESS,
    "Resolved": Status.RESOLVED,
}[filter_label]

try:
    tickets = repo.list_tickets(filter_status)
except Exception:
    logger.exception("Ticket list failed")
    st.error("Could not load the ticket queue.")
    st.stop()

if not tickets:
    st.info("No tickets match this filter.")
    st.stop()

st.dataframe(
    [
        {
            "ID": ticket.ticket_id,
            "Title": ticket.title,
            "Status": STATUS_LABELS[ticket.status],
            "Priority": PRIORITY_LABELS[ticket.priority],
            "Created by": ticket.created_by,
            "Created": ticket.created_at.strftime("%Y-%m-%d %H:%M UTC"),
        }
        for ticket in tickets
    ],
    use_container_width=True,
    hide_index=True,
)

selected_id = st.selectbox(
    "Select a ticket",
    options=[ticket.ticket_id for ticket in tickets],
    format_func=lambda ticket_id: next(
        f"#{ticket.ticket_id} — {ticket.title}"
        for ticket in tickets
        if ticket.ticket_id == ticket_id
    ),
)

try:
    selected = repo.get_ticket(selected_id)
    messages = repo.get_messages(selected_id)
except RecordNotFound as error:
    st.warning(str(error))
    st.stop()
except Exception:
    logger.exception("Ticket detail failed")
    st.error("Could not load this ticket.")
    st.stop()

detail_column, action_column = st.columns([2, 1])
with detail_column:
    st.subheader(f"#{selected.ticket_id} · {selected.title}")
    st.caption(
        f"Created by {selected.created_by} on "
        f"{selected.created_at.strftime('%B %d, %Y at %H:%M UTC')} · "
        f"Priority: {PRIORITY_LABELS[selected.priority]}"
    )

with action_column:
    with st.form("update_status"):
        selected_status = st.selectbox(
            "Status",
            options=list(Status),
            index=list(Status).index(selected.status),
            format_func=lambda value: STATUS_LABELS[value],
        )
        status_submitted = st.form_submit_button("Update status", use_container_width=True)
    if status_submitted:
        try:
            repo.update_status(selected.ticket_id, selected_status)
            flash_success(f"Ticket #{selected.ticket_id} status updated.")
        except Exception:
            logger.exception("Status update failed")
            st.error("Could not update the ticket status.")

st.markdown("### Conversation")
for message in messages:
    safe_author = html.escape(message.author)
    safe_text = html.escape(message.message_text).replace("\n", "<br>")
    st.markdown(
        f"<div class='message-card'><div class='message-meta'>{safe_author} · "
        f"{message.created_at.strftime('%Y-%m-%d %H:%M UTC')}</div>{safe_text}</div>",
        unsafe_allow_html=True,
    )

with st.form("add_message", clear_on_submit=True):
    message_text = st.text_area(
        "Add a message",
        max_chars=5_000,
        placeholder="Share an update or ask a follow-up question…",
    )
    message_submitted = st.form_submit_button("Post message")

if message_submitted:
    try:
        author = actor_email(headers, local_identity)
        values = validate_message(message_text=message_text, author=author)
        repo.add_message(ticket_id=selected.ticket_id, **values)
        flash_success(f"Message added to ticket #{selected.ticket_id}.")
    except ValidationError as error:
        show_validation(error)
    except Exception:
        logger.exception("Message creation failed")
        st.error("Could not add the message. Try again.")
