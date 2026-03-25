"""
HTTP transport for the MCP server.

Exposes:
  POST /mcp                 - MCP JSON-RPC protocol endpoint
  GET  /dashboard           - Real-time activity dashboard (browser UI)
  GET  /activity/stream     - SSE feed of live tool calls
  GET  /activity            - JSON list of recent tool calls (?n=50)
  GET  /sessions            - JSON list of known sessions

All endpoints except /dashboard accept the Bearer token in the
Authorization header.  /activity/stream also accepts ?key=<token> as a
query param because browser EventSource cannot set custom headers.
"""

import json
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Mount, Route

from .activity_tracker import tracker


# ---------------------------------------------------------------------------
# Dashboard HTML (self-contained, no external dependencies)
# ---------------------------------------------------------------------------

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ServiceNow MCP &mdash; Dashboard</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", monospace;
       background: #0f1117; color: #e2e8f0; min-height: 100vh; }
header { background: #1a1d2e; border-bottom: 1px solid #2d3148;
         padding: 14px 24px; display: flex; align-items: center; gap: 12px; }
header h1 { font-size: 16px; font-weight: 600; color: #fff; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
       animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.ok      { background: #14532d; color: #4ade80; }
.error   { background: #450a0a; color: #f87171; }
.running { background: #1e3a5f; color: #60a5fa; }
.layout { display: grid; grid-template-columns: 300px 1fr; gap: 0;
          height: calc(100vh - 53px); }
.panel { overflow-y: auto; border-right: 1px solid #2d3148; }
.panel-title { font-size: 11px; font-weight: 700; letter-spacing: .08em;
               text-transform: uppercase; color: #64748b;
               padding: 12px 16px; border-bottom: 1px solid #2d3148; }
.session-card { padding: 10px 16px; border-bottom: 1px solid #1e2235; font-size: 12px; }
.sid { font-family: monospace; color: #94a3b8; font-size: 11px; }
.calls { color: #60a5fa; font-size: 11px; margin-top: 2px; }
.active-badge { color: #facc15; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
thead th { padding: 8px 12px; text-align: left; font-size: 11px; font-weight: 600;
           letter-spacing: .06em; text-transform: uppercase; color: #475569;
           border-bottom: 1px solid #2d3148; position: sticky; top: 0;
           background: #0f1117; }
tbody tr { border-bottom: 1px solid #1a1d2e; }
tbody tr:hover { background: #1a1d2e; }
tbody td { padding: 7px 12px; }
.tool { color: #e2e8f0; font-weight: 500; }
.ts   { color: #64748b; font-variant-numeric: tabular-nums; }
.dur  { color: #94a3b8; font-variant-numeric: tabular-nums; }
.err  { color: #f87171; font-size: 11px; max-width: 220px;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#feed { overflow-y: auto; }
.empty { color: #475569; font-size: 13px; padding: 24px 16px; }
.stats-bar { display: flex; gap: 28px; padding: 12px 16px;
             border-bottom: 1px solid #2d3148; }
.stat { display: flex; flex-direction: column; }
.stat-val { font-size: 20px; font-weight: 700; color: #fff; }
.stat-lbl { color: #64748b; font-size: 10px; margin-top: 1px; }
</style>
</head>
<body>
<header>
  <div class="dot" id="dot"></div>
  <h1>ServiceNow MCP &mdash; Activity Dashboard</h1>
</header>
<div class="layout">
  <div class="panel">
    <div class="panel-title">Sessions</div>
    <div id="sessions"><div class="empty">No sessions yet.</div></div>
  </div>
  <div id="feed">
    <div class="stats-bar">
      <div class="stat"><span class="stat-val" id="s-total">0</span><span class="stat-lbl">Total Calls</span></div>
      <div class="stat"><span class="stat-val" id="s-ok">0</span><span class="stat-lbl">OK</span></div>
      <div class="stat"><span class="stat-val" id="s-err">0</span><span class="stat-lbl">Errors</span></div>
      <div class="stat"><span class="stat-val" id="s-run">0</span><span class="stat-lbl">Running</span></div>
    </div>
    <table>
      <thead><tr>
        <th>Time</th><th>Session</th><th>Tool</th>
        <th>Duration</th><th>Status</th><th>Error</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</div>
<script>
const API_KEY = new URLSearchParams(location.search).get("key") || "";
const hdrs = API_KEY ? {"Authorization": "Bearer " + API_KEY} : {};
const MAX = 100;
let st = {total:0, ok:0, err:0, run:0};
let running = new Set();

function row(ev) {
  const dur = ev.duration_ms > 0 ? ev.duration_ms + "ms" : "&mdash;";
  const badge = `<span class="badge ${ev.status}">${ev.status}</span>`;
  const errCell = ev.error ? `<span class="err" title="${ev.error}">${ev.error}</span>` : "";
  return `<tr data-id="${ev.id}">
    <td class="ts">${ev.started_iso}</td>
    <td class="ts">${(ev.session_short||ev.session_id||"").slice(0,8)}</td>
    <td class="tool">${ev.tool_name}</td>
    <td class="dur">${dur}</td>
    <td>${badge}</td>
    <td>${errCell}</td>
  </tr>`;
}

function updateStats() {
  document.getElementById("s-total").textContent = st.total;
  document.getElementById("s-ok").textContent = st.ok;
  document.getElementById("s-err").textContent = st.err;
  document.getElementById("s-run").textContent = st.run;
}

function handleEv(ev) {
  const tbody = document.getElementById("tbody");
  if (ev.status === "running") {
    st.total++; st.run++; running.add(ev.id);
    tbody.insertAdjacentHTML("afterbegin", row(ev));
  } else {
    const existing = tbody.querySelector(`tr[data-id="${ev.id}"]`);
    const html = row(ev);
    if (existing) {
      existing.outerHTML = html;
    } else {
      tbody.insertAdjacentHTML("afterbegin", html);
    }
    if (running.has(ev.id)) { running.delete(ev.id); st.run = Math.max(0, st.run-1); }
    if (ev.status === "ok") st.ok++; else if (ev.status === "error") st.err++;
  }
  while (tbody.rows.length > MAX) tbody.deleteRow(-1);
  updateStats();
}

function refreshSessions() {
  fetch("/sessions", {headers: hdrs}).then(r => r.json()).then(sessions => {
    const el = document.getElementById("sessions");
    if (!sessions.length) { el.innerHTML = '<div class="empty">No sessions yet.</div>'; return; }
    el.innerHTML = sessions.map(s => `
      <div class="session-card">
        <div>${(s.session_short||s.session_id||"").slice(0,8)}&hellip;</div>
        <div class="sid">${s.session_id}</div>
        <div class="calls">${s.call_count} calls
          ${s.active_calls>0 ? `<span class="active-badge">&bull; ${s.active_calls} running</span>` : ""}
        </div>
      </div>`).join("");
  }).catch(()=>{});
}

const sseUrl = "/activity/stream" + (API_KEY ? "?key="+encodeURIComponent(API_KEY) : "");
const src = new EventSource(sseUrl);
src.onopen  = () => document.getElementById("dot").style.background = "#22c55e";
src.onerror = () => document.getElementById("dot").style.background = "#ef4444";
src.onmessage = e => { try { handleEv(JSON.parse(e.data)); } catch(_) {} };

fetch("/activity?n=50", {headers: hdrs}).then(r => r.json()).then(events => {
  [...events].reverse().forEach(handleEv);
}).catch(()=>{});

refreshSessions();
setInterval(refreshSessions, 3000);
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _auth_ok(request: Request) -> bool:
    api_key = request.app.state.api_key
    if not api_key:
        return True
    auth = request.headers.get("authorization", "")
    return auth == f"Bearer {api_key}"


async def dashboard(request: Request):
    return HTMLResponse(_DASHBOARD_HTML)


async def activity_stream(request: Request):
    api_key = request.app.state.api_key
    if api_key:
        key_via_query = request.query_params.get("key", "")
        auth_header = request.headers.get("authorization", "")
        if auth_header != f"Bearer {api_key}" and key_via_query != api_key:
            return Response("Unauthorized", status_code=401)

    async def gen():
        async for chunk in tracker.subscribe():
            yield chunk.encode()

    return Response(
        content=gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def activity_json(request: Request):
    if not _auth_ok(request):
        return Response("Unauthorized", status_code=401)
    n = int(request.query_params.get("n", 50))
    return JSONResponse(tracker.get_recent(n))


async def sessions_json(request: Request):
    if not _auth_ok(request):
        return Response("Unauthorized", status_code=401)
    return JSONResponse(tracker.get_sessions())


# ---------------------------------------------------------------------------
# Auth middleware (pure ASGI — no buffering, SSE-safe)
# ---------------------------------------------------------------------------

class _ApiKeyMiddleware:
    def __init__(self, app, api_key: str):
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and self.api_key:
            path = scope.get("path", "")
            # /dashboard and /activity/stream handle auth themselves
            if path not in ("/dashboard", "/activity/stream"):
                headers = {k: v for k, v in scope.get("headers", [])}
                auth = headers.get(b"authorization", b"").decode()
                if not auth.startswith("Bearer ") or auth[7:] != self.api_key:
                    await send({"type": "http.response.start", "status": 401,
                                "headers": [(b"content-type", b"text/plain")]})
                    await send({"type": "http.response.body", "body": b"Unauthorized"})
                    return
        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def start(mcp_server, host: str, port: int, api_key: str = None):
    from contextlib import asynccontextmanager

    mcp_asgi = mcp_server.streamable_http_app()

    # Starlette does NOT propagate lifespan to mounted sub-apps.
    # We delegate to the inner MCP app's lifespan so its session manager
    # task group is initialised before requests arrive.
    @asynccontextmanager
    async def lifespan(app):
        async with mcp_asgi.router.lifespan_context(mcp_asgi):
            yield

    app = Starlette(
        routes=[
            Route("/dashboard",       dashboard),
            Route("/activity/stream", activity_stream),
            Route("/activity",        activity_json),
            Route("/sessions",        sessions_json),
            Mount("/",                app=mcp_asgi),
        ],
        lifespan=lifespan,
    )
    app.state.api_key = api_key or ""

    if api_key:
        app = _ApiKeyMiddleware(app, api_key)

    uvicorn.run(app, host=host, port=port, log_level="info")
