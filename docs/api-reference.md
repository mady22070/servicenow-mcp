# API Reference

This document covers every HTTP endpoint the MCP server exposes, how to authenticate, the MCP session handshake, and how to call tools.

---

## Transport modes

| Mode | When to use | How to start |
|------|-------------|--------------|
| **stdio** | Claude Desktop (default) | `python -m servicenow_mcp` |
| **HTTP** | Any LLM — Cursor, Cline, OpenAI, custom agents | `MCP_TRANSPORT=http python -m servicenow_mcp` |

For Claude Desktop use the stdio transport and set the command in `claude_desktop_config.json`. For everything else use HTTP.

---

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICENOW_INSTANCE_URL` | yes | — | e.g. `https://dev12345.service-now.com` |
| `SERVICENOW_USERNAME` | yes | — | ServiceNow username |
| `SERVICENOW_PASSWORD` | yes | — | ServiceNow password |
| `MCP_TRANSPORT` | no | `stdio` | `stdio` or `http` |
| `MCP_HOST` | no | `0.0.0.0` | Bind address for HTTP mode |
| `MCP_PORT` | no | `8000` | Port for HTTP mode |
| `MCP_API_KEY` | no | _(no auth)_ | Bearer token clients must send |
| `MCP_LOG_FILE` | no | `/tmp/servicenow-mcp.log` | Log file path |
| `MCP_LOG_CONSOLE` | no | `false` | Set `true` to also log to stdout |

### Multi-environment ServiceNow credentials

To connect to dev / test / prod separately, set per-environment variables and pass `"env"` in every tool call:

| Variable | env value |
|----------|-----------|
| `SERVICENOW_DEV_INSTANCE_URL` + `_USERNAME` + `_PASSWORD` | `"dev"` |
| `SERVICENOW_TEST_INSTANCE_URL` + `_USERNAME` + `_PASSWORD` | `"test"` |
| `SERVICENOW_PROD_INSTANCE_URL` + `_USERNAME` + `_PASSWORD` | `"prod"` |

---

## Starting the server

```bash
# Minimal — no auth, default port 8000
MCP_TRANSPORT=http \
SERVICENOW_INSTANCE_URL=https://dev12345.service-now.com \
SERVICENOW_USERNAME=admin \
SERVICENOW_PASSWORD=secret \
python -m servicenow_mcp

# With API key on a custom port
MCP_TRANSPORT=http MCP_PORT=9000 MCP_API_KEY=my-secret-key \
SERVICENOW_INSTANCE_URL=https://dev12345.service-now.com \
SERVICENOW_USERNAME=admin SERVICENOW_PASSWORD=secret \
python -m servicenow_mcp
```

Docker:

```bash
docker run --rm -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e MCP_API_KEY=my-secret-key \
  -e SERVICENOW_INSTANCE_URL=https://dev12345.service-now.com \
  -e SERVICENOW_USERNAME=admin \
  -e SERVICENOW_PASSWORD=secret \
  servicenow-mcp
```

---

## Authentication

When `MCP_API_KEY` is set every request must include:

```
Authorization: Bearer <your-api-key>
```

Requests missing or with a wrong token receive `HTTP 401 Unauthorized`.

The `/dashboard` page and the SSE stream (`/activity/stream`) also accept the key as a query parameter so browsers can open them directly:

```
http://localhost:8000/dashboard?key=my-secret-key
http://localhost:8000/activity/stream?key=my-secret-key
```

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/mcp` | Bearer | MCP JSON-RPC — all protocol messages go here |
| `GET` | `/dashboard` | key param | Real-time activity dashboard (open in browser) |
| `GET` | `/activity/stream` | Bearer or key param | SSE stream of live tool calls |
| `GET` | `/activity` | Bearer | JSON list of recent tool calls |
| `GET` | `/sessions` | Bearer | JSON list of active/known sessions |

---

## MCP session lifecycle

Every MCP client must perform a 3-step handshake before calling tools. All three requests go to `POST /mcp`.

### Step 1 — initialize

Send this once to open a session. The response contains the server's capabilities and a `mcp-session-id` response header you must include in all subsequent requests.

```bash
curl -si -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "my-agent", "version": "1.0"}
    }
  }'
```

Extract the session ID from the response header:

```
mcp-session-id: a1b2c3d4e5f6...
```

Response body (SSE `data:` line):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
    "serverInfo": {"name": "servicenow-mcp", "version": "1.12.4"}
  }
}
```

### Step 2 — notifications/initialized

Acknowledge the session. Returns `HTTP 202` with no body.

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'
```

### Step 3 — tools/list or tools/call

After step 2 you can call any MCP method. Include `mcp-session-id` in every request.

---

## How to list available tools

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'
```

The response is an SSE stream. Each `data:` line is a JSON object. The tool list is in:

```
result.tools[]  — array of {name, description, inputSchema}
```

Parse the tool count in one command:

```bash
... | grep "^data:" | head -1 | sed 's/^data: //' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['result']['tools']), 'tools')"
```

---

## How to call a tool

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: <SESSION_ID>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "create_incident",
      "arguments": {
        "short_description": "VPN not working",
        "description": "Cannot connect to VPN from home office.",
        "env": "dev"
      }
    }
  }'
```

Result is in `result.content[0].text` (a JSON string):

```json
{
  "number": "INC0010003",
  "sys_id": "...",
  "state": "1",
  "short_description": "VPN not working"
}
```

---

## Tool categories

| Category | Tools (examples) |
|----------|-----------------|
| Core server | `get_server_info`, `health_check`, `get_pack_registry_info` |
| Table / data | `query_table`, `create_record`, `update_record`, `delete_record` |
| Incidents | `create_incident`, `get_incident`, `update_incident`, `resolve_incident` |
| Change management | `create_change_request`, `approve_change`, `implement_change` |
| CMDB | `query_cmdb`, `ci_graph`, `troubleshoot_cmdb_duplicates`, `cmdb_health_snapshot` |
| Discovery / ITOM | `run_discovery`, `manage_alerts`, `correlate_events` |
| Flows & automation | `create_flow`, `trigger_flow`, `manage_workflow` |
| Scripts | `create_business_rule`, `create_script_include`, `run_background_script` |
| Service catalog | `create_catalog_item`, `submit_request`, `manage_catalog` |
| Scoped apps | `create_application`, `manage_update_sets`, `publish_app` |
| Knowledge / docs | `search_servicenow_docs`, `query_knowledge_base` |

Run `tools/list` to get the full list with input schemas.

---

## Activity dashboard

Open in a browser while the server is running:

```
http://localhost:8000/dashboard?key=my-secret-key
```

The dashboard shows:

- **Sessions panel** (left) — every MCP session that has connected, with call count and active call indicator. Refreshes every 3 seconds.
- **Activity feed** (right) — live table of every tool call: timestamp, session ID (first 8 chars), tool name, duration, status badge (green OK / blue running / red error), and error message if any.

### Activity API

Recent calls (JSON):

```bash
curl http://localhost:8000/activity?n=50 \
  -H "Authorization: Bearer my-secret-key"
```

Active sessions (JSON):

```bash
curl http://localhost:8000/sessions \
  -H "Authorization: Bearer my-secret-key"
```

SSE stream (one JSON event per tool call, live):

```bash
curl -N http://localhost:8000/activity/stream \
  -H "Authorization: Bearer my-secret-key"
```

Each SSE event looks like:

```json
{
  "id": "a1b2c3d4e5f6",
  "session_id": "1753fddfcb1641b8b330c205ade58aec",
  "session_short": "1753fddf",
  "tool_name": "query_table",
  "status": "ok",
  "started_iso": "11:23:45",
  "duration_ms": 312.4,
  "error": null
}
```

`status` is one of `"running"` (emitted when the call starts), `"ok"`, or `"error"`.

---

## Connecting from LLM clients

### Cursor / Cline (MCP settings JSON)

```json
{
  "mcpServers": {
    "servicenow": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer my-secret-key"
      }
    }
  }
}
```

### Claude Desktop (stdio)

```json
{
  "mcpServers": {
    "servicenow-mcp": {
      "command": "python",
      "args": ["-m", "servicenow_mcp"],
      "env": {
        "SERVICENOW_INSTANCE_URL": "https://dev12345.service-now.com",
        "SERVICENOW_USERNAME": "admin",
        "SERVICENOW_PASSWORD": "secret"
      }
    }
  }
}
```

### Python (raw HTTP)

```python
import httpx, json

BASE = "http://localhost:8000/mcp"
KEY  = "my-secret-key"
HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

def mcp_call(session_id, method, params, id=1):
    r = httpx.post(BASE, headers={**HEADERS, "mcp-session-id": session_id},
                   json={"jsonrpc": "2.0", "id": id, "method": method, "params": params})
    for line in r.text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())

# Handshake
r = httpx.post(BASE, headers=HEADERS, json={
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
               "clientInfo": {"name": "test", "version": "1.0"}}
})
session_id = r.headers["mcp-session-id"]
httpx.post(BASE, headers={**HEADERS, "mcp-session-id": session_id},
           json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

# Call a tool
result = mcp_call(session_id, "tools/call",
                  {"name": "health_check", "arguments": {"env": "dev"}})
print(result["result"]["content"][0]["text"])
```
