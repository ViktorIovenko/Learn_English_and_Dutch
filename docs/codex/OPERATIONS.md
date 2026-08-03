# Safe operations

```bash
# Local state and focused checks
git status --short
python -m compileall tools
python -m unittest tests.test_project_kb
python tools/project_kb.py status

# Read-only production runtime
ssh -i "$HOME/Desktop/id_ed25519" root@204.168.186.69 "docker ps --filter name=learn-words --format '{{.Names}} {{.Status}} {{.Ports}}'"
ssh -i "$HOME/Desktop/id_ed25519" root@204.168.186.69 "docker logs --tail 50 learn-words-learn-words-1"
ssh -i "$HOME/Desktop/id_ed25519" root@204.168.186.69 "ss -ltnp | grep ':7001' || true"
ssh -i "$HOME/Desktop/id_ed25519" root@204.168.186.69 "curl -fsS -o /dev/null -w '%{http_code}\n' https://learn.iovenko.eu/"
ssh -i "$HOME/Desktop/id_ed25519" root@204.168.186.69 "docker exec proxy-nginx nginx -t"
ssh -i "$HOME/Desktop/id_ed25519" root@204.168.186.69 "cd /opt/learn-words && if test -d .git; then git status --short; git branch --show-current; git rev-parse HEAD; else echo NO_GIT_METADATA; fi"

# Schema metadata only; never SELECT user rows
ssh -i "$HOME/Desktop/id_ed25519" root@204.168.186.69 "docker exec learn-words-learn-words-1 sqlite3 /app/words.db '.schema'"
```

If `sqlite3` is absent in the image, use `python tools/project_kb.py server-scan`; it reads only `sqlite_master`. A restart is not a diagnostic command and is intentionally omitted.
