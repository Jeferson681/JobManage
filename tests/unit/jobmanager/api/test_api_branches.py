import importlib
import sqlite3

import pytest
from fastapi import HTTPException


def test_get_conn_falls_back_when_importlib_fails(monkeypatch):
    api_app = importlib.import_module("jobmanager.api.app")

    def _bad(name):
        raise ImportError("nope")

    monkeypatch.setattr("importlib.import_module", _bad)
    conn = api_app.get_conn()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


@pytest.mark.asyncio
async def test_lifespan_initializes_db():
    api_app = importlib.import_module("jobmanager.api.app")
    # use the async context manager to exercise lifespan startup
    async with api_app.lifespan(api_app.app):
        # ensure a connection can be created while lifespan is active
        conn = api_app.get_conn()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()


def test_ready_raises_when_db_unavailable(monkeypatch):
    api_app = importlib.import_module("jobmanager.api.app")

    def _bad_conn():
        raise sqlite3.Error("cant connect")

    monkeypatch.setattr(api_app, "get_conn", _bad_conn)
    with pytest.raises(HTTPException):
        api_app.ready()


def test_get_job_handler_404():
    api_app = importlib.import_module("jobmanager.api.app")
    with pytest.raises(HTTPException):
        api_app.get_job_handler("no-such")


def test_cancel_job_404():
    api_app = importlib.import_module("jobmanager.api.app")
    with pytest.raises(HTTPException):
        api_app.cancel_job("no-such")
