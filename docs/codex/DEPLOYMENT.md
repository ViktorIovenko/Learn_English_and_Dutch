# Deployment

- Server: `204.168.186.69`.
- Project path: `/opt/learn-words`.
- Local remote: `https://github.com/ViktorIovenko/Learn_English_and_Dutch.git`.
- Production branch/commit: unavailable because the deployed directory currently has no `.git` metadata.
- Runtime service: Docker Compose service `learn-words`, container `learn-words-learn-words-1`, image `learn-words-learn-words`.
- Working directory/entrypoint: `/app`, safe command `python run.py`; container port `7001`.
- Environment file path: `/opt/learn-words/.env` (content must never be read/indexed).
- Nginx: container `proxy-nginx`; host config `/opt/proxy/nginx/conf.d/learn.conf`; `learn.iovenko.eu`, `/` → `http://learn-words:7001`.
- MCP: `/mcp` and `/.well-known/oauth-protected-resource/mcp` → `mcp-gateway:8000`; OAuth issuer endpoints remain in `learn-words`.
- MCP runtime: isolated Compose services `mcp-gateway` and `mcp-redis`; proxy network `web_proxy` plus internal application network `learn_mcp_internal`.
- Database: host `/opt/learn-words/data/words.db` → container `/app/words.db`.
- Static code: `/opt/learn-words/app/static`; persistent audio: `/opt/learn-words/data/audio` → `/app/app/static/audio`.
- Bot persistence: `/opt/learn-words/data/bot_persistence.pkl` → `/app/bot_persistence.pkl`.
- Logs: Docker container logs (`docker logs --tail ...`); no application log file was confirmed.
- Update procedure: deployment scripts exist locally, but no automatic update procedure is asserted as production truth. Inspect the requested script and current server state before an authorized deploy.

Production access is read-only by default. No standard verification step includes restart, deploy, database mutation, `.env` access or a second polling process.
