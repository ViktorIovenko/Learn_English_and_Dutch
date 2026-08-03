import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "project_kb.py"
SPEC = importlib.util.spec_from_file_location("project_kb", MODULE_PATH)
kb = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(kb)


class ProjectKnowledgeBaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "kb.sqlite"
        self.con = kb.connect(self.db)

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def fixture(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_database_creation_and_noop_reindex(self):
        path = self.fixture("sample.py", "def alpha(value):\n    return value\n")
        self.assertTrue(kb.index_file(self.con, path))
        self.assertFalse(kb.index_file(self.con, path))
        self.assertTrue(self.db.exists())

    def test_single_file_update_and_delete_cleanup(self):
        path = self.fixture("changed.py", "def before():\n    pass\n")
        kb.index_file(self.con, path)
        path.write_text("def after():\n    pass\n", encoding="utf-8")
        self.assertTrue(kb.index_file(self.con, path))
        rel = path.as_posix()
        self.assertIsNotNone(self.con.execute("SELECT 1 FROM symbols WHERE name='after'").fetchone())
        path.unlink()
        self.con.execute("DELETE FROM files WHERE path=?", (rel,))
        self.con.execute("DELETE FROM symbols WHERE file_path=?", (rel,))
        self.assertIsNone(self.con.execute("SELECT 1 FROM files WHERE path=?", (rel,)).fetchone())

    def test_python_symbol_flask_route_and_table(self):
        path = self.fixture("routes.py", '''
from flask import Blueprint
web = Blueprint("web", __name__)
@web.post("/api/progress/sync")
def sync_progress():
    """Store queued progress."""
    sql = "INSERT INTO progress_events(user_id) VALUES (?)"
    return {"ok": True}
SCHEMA = "CREATE TABLE progress_events (id INTEGER PRIMARY KEY, user_id TEXT)"
''')
        kb.index_file(self.con, path)
        self.assertIsNotNone(self.con.execute("SELECT 1 FROM symbols WHERE name='sync_progress'").fetchone())
        self.assertIsNotNone(self.con.execute("SELECT 1 FROM routes WHERE route_or_command='/api/progress/sync'").fetchone())
        self.assertIsNotNone(self.con.execute("SELECT 1 FROM database_tables WHERE table_name='progress_events'").fetchone())

    def test_telegram_handler(self):
        path = self.fixture("bot.py", 'application.add_handler(CommandHandler("start", start_cmd))\n')
        kb.telegram_routes(self.con, path.as_posix(), path.read_text(), "local")
        row = self.con.execute("SELECT route_or_command,handler FROM routes").fetchone()
        self.assertEqual((row[0], row[1]), ("/start", "start_cmd"))

    def test_android_contract_matching(self):
        android = self.fixture("ApiService.kt", '''
@POST("api/progress/sync")
suspend fun syncProgress(@Body request: SyncProgressRequest): Response<SyncProgressResponse>
''')
        backend = self.fixture("backend.py", '''
@web.post("/api/progress/sync")
def sync_progress():
    return {}
''')
        kb.index_file(self.con, android)
        kb.index_file(self.con, backend)
        kb.link_android(self.con)
        row = self.con.execute("SELECT status,backend_handler FROM android_contracts").fetchone()
        self.assertEqual((row[0], row[1]), ("confirmed", "sync_progress"))

    def test_secrets_env_and_user_data_are_not_indexed(self):
        self.assertFalse(kb.should_index(Path(".env")))
        self.assertFalse(kb.should_index(Path("data/words.db")))
        secret = "super-private-token-value"
        path = self.fixture("config.py", f'API_TOKEN = "{secret}"\n')
        kb.index_file(self.con, path)
        dump = "\n".join(self.con.iterdump())
        self.assertNotIn(secret, dump)
        self.assertNotIn("Alice Example", dump)

    def test_without_fts5(self):
        other = sqlite3.connect(self.root / "nofts.sqlite")
        other.executescript(kb.SCHEMA)
        self.assertFalse(kb.ensure_fts(other, force_disable=True))
        self.assertEqual(other.execute("SELECT enabled FROM kb_capabilities WHERE name='fts5'").fetchone()[0], 0)
        other.close()

    def test_systemd_command_redaction(self):
        value = kb.redact_command("python run.py --token abc PASSWORD=xyz --port 7001")
        self.assertNotIn("abc", value)
        self.assertNotIn("xyz", value)
        self.assertIn("<redacted>", value)

    def test_production_snapshot_parser_and_commit_compare_fields(self):
        payload = "\n".join([
            "META|project_path|/opt/learn-words", "META|git_branch|master",
            "META|git_commit|abc123", "META|git_dirty|0",
            "SERVICE|learn-words|docker|/app|python run.py|root|root|/opt/learn-words/.env|7001",
            "ROUTE|learn.iovenko.eu|/|http://learn-words:7001|/opt/proxy/nginx/conf.d/learn.conf|ok",
            "HASH|deadbeef|run.py",
        ])
        parsed = kb.parse_production_payload(payload)
        self.assertEqual(parsed["meta"]["git_commit"], "abc123")
        self.assertEqual(parsed["services"][0][0], "learn-words")
        self.assertEqual(parsed["hashes"]["run.py"], "deadbeef")

    def test_server_scan_mock_has_no_ssh(self):
        mock = self.fixture("scan.txt", "\n".join([
            "META|project_path|/opt/learn-words", "META|git_branch|unavailable",
            "META|git_commit|unavailable", "META|git_dirty|unknown",
            "SERVICE|learn-words|docker|/app|python run.py --token abc|root|root|/opt/learn-words/.env|7001",
            "SCHEMA|table|words|words|CREATE TABLE words (id INTEGER PRIMARY KEY, nl TEXT)",
        ]))
        self.con.close()
        parsed = kb.server_scan("unused", "unused", str(mock), self.db)
        con = sqlite3.connect(self.db)
        command = con.execute("SELECT exec_start_redacted FROM services").fetchone()[0]
        snap = con.execute("SELECT git_commit FROM environment_snapshots WHERE environment='production'").fetchone()[0]
        con.close()
        self.con = kb.connect(self.db)
        self.assertEqual(parsed["meta"]["project_path"], "/opt/learn-words")
        self.assertNotIn("abc", command)
        self.assertEqual(snap, "unavailable")


if __name__ == "__main__":
    unittest.main()
