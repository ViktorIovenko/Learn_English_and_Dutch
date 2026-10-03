"""Shared SQLite transactions for content writes and MCP retry receipts."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import sqlite3

_active = ContextVar("content_transaction", default=None)


class BorrowedConnection:
    def __init__(self, connection):
        self.connection = connection

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def __setattr__(self, name, value):
        if name == "connection":
            object.__setattr__(self, name, value)
        else:
            setattr(self.connection, name, value)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def commit(self):
        pass  # Only the owning transaction may commit.

    def close(self):
        pass

    def rollback(self):
        raise RuntimeError("rollback must be performed by the owning transaction")

    def executescript(self, script):
        # sqlite3.executescript implicitly commits; execute complete statements
        # separately so legacy schema helpers cannot break an atomic MCP write.
        statement = ""
        for char in script:
            statement += char
            if char == ";" and sqlite3.complete_statement(statement):
                self.connection.execute(statement)
                statement = ""
        if statement.strip():
            self.connection.execute(statement)


def connect(db_path):
    active = _active.get()
    path = str(Path(db_path).resolve())
    if active and active[0] == path:
        return BorrowedConnection(active[1])
    connection = sqlite3.connect(db_path, timeout=60)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def transaction(db_path):
    active = _active.get()
    path = str(Path(db_path).resolve())
    if active and active[0] == path:
        yield BorrowedConnection(active[1])
        return
    connection = connect(db_path)
    connection.execute("BEGIN IMMEDIATE")
    token = _active.set((path, connection))
    try:
        yield BorrowedConnection(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        _active.reset(token)
        connection.close()
