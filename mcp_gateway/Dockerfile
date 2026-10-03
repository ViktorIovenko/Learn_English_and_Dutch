FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/mcp

COPY mcp_gateway/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && addgroup --system mcp \
    && adduser --system --ingroup mcp --home /nonexistent --no-create-home mcp

COPY mcp_gateway /srv/mcp/mcp_gateway
USER mcp
EXPOSE 8000
CMD ["uvicorn", "mcp_gateway.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
