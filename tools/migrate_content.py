"""Explicit, additive catalog migration with an SQLite-consistent backup.

Usage: python tools/migrate_content.py --db path/to/words.db
No user records, IDs, progress or lesson assignments are deleted/renumbered.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.content_db import transaction
from app.content_service import ensure_schema
from app.audio_gen import _ensure_audio_schema


def migrate(path):
    path = Path(path).resolve(strict=True)
    backup = path.with_name(path.name + ".before-content-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".bak")
    with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(backup)) as target:
        source.backup(target)
    with transaction(path) as conn:
        before = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        ensure_schema(conn)
        _ensure_audio_schema(conn)
        after = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        if before != after:
            raise RuntimeError("migration changed the number of user records")
    return backup


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    print("Additive migration applied. Backup:", migrate(args.db))
