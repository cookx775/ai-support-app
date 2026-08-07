from __future__ import annotations

import base64
import os
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


class DatabaseConfigurationError(RuntimeError):
    """Raised when the Lakebase connection secret is unavailable."""


@lru_cache(maxsize=1)
def _workspace_client():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def _lakebase_url() -> str:
    configured_url = os.environ.get("LAKEBASE_URL")
    if configured_url:
        return configured_url

    scope = os.environ.get("LAKEBASE_SECRET_SCOPE", "database")
    key = os.environ.get("LAKEBASE_SECRET_KEY", "lakebase-url")
    try:
        secret = _workspace_client().secrets.get_secret(scope=scope, key=key)
        encoded_value = secret.value
        if not encoded_value:
            raise DatabaseConfigurationError(f"Secret {scope}/{key} is empty")
        return base64.b64decode(encoded_value).decode("utf-8")
    except DatabaseConfigurationError:
        raise
    except Exception as exc:
        raise DatabaseConfigurationError(
            f"Unable to read Lakebase connection secret {scope}/{key}"
        ) from exc


@contextmanager
def get_connection() -> Iterator[connection]:
    conn = psycopg2.connect(_lakebase_url(), cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()
