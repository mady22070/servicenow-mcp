"""
Real-time activity tracking for the MCP server.

Tracks every tool call with session ID, tool name, duration, and status.
Exposes a singleton used by both mcp_adapter (to record events) and
http_server (to serve the dashboard and SSE feed).
"""

import asyncio
import json
import time
import uuid
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ActivityEvent:
    id: str
    session_id: str        # full session ID
    session_short: str     # first 8 chars for display
    tool_name: str
    status: str            # "running" | "ok" | "error"
    started_at: float      # time.time()
    started_iso: str       # ISO 8601 string for UI
    duration_ms: float     # 0 until complete
    error: Optional[str]

    def to_dict(self):
        return asdict(self)


class ActivityTracker:
    def __init__(self, maxlen: int = 500):
        self._events: deque = deque(maxlen=maxlen)
        self._active: Dict[str, ActivityEvent] = {}
        self._sessions: Dict[str, dict] = {}
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Called from mcp_adapter (sync-safe — uses run_coroutine_threadsafe
    # if called from a sync context, otherwise direct await)
    # ------------------------------------------------------------------

    def record_start(self, session_id: str, tool_name: str) -> str:
        event_id = uuid.uuid4().hex[:12]
        now = time.time()
        event = ActivityEvent(
            id=event_id,
            session_id=session_id,
            session_short=session_id[:8] if len(session_id) >= 8 else session_id,
            tool_name=tool_name,
            status="running",
            started_at=now,
            started_iso=datetime.fromtimestamp(now, tz=timezone.utc).strftime("%H:%M:%S"),
            duration_ms=0.0,
            error=None,
        )
        self._active[event_id] = event

        # Track session
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "session_short": event.session_short,
                "first_seen": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
                "last_seen": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
                "call_count": 0,
                "active_calls": 0,
            }
        self._sessions[session_id]["last_seen"] = datetime.fromtimestamp(now, tz=timezone.utc).isoformat()
        self._sessions[session_id]["call_count"] += 1
        self._sessions[session_id]["active_calls"] += 1

        # Fan out "running" event to SSE subscribers (fire-and-forget)
        self._fanout(event)
        return event_id

    def record_end(self, event_id: str, error: Optional[str] = None):
        event = self._active.pop(event_id, None)
        if event is None:
            return
        now = time.time()
        event.duration_ms = round((now - event.started_at) * 1000, 1)
        event.status = "error" if error else "ok"
        event.error = error

        self._events.append(event)

        # Update session active count
        sid = event.session_id
        if sid in self._sessions:
            self._sessions[sid]["active_calls"] = max(
                0, self._sessions[sid]["active_calls"] - 1
            )
            self._sessions[sid]["last_seen"] = datetime.fromtimestamp(
                now, tz=timezone.utc
            ).isoformat()

        self._fanout(event)

    def _fanout(self, event: ActivityEvent):
        """Push event to all SSE subscriber queues (non-blocking)."""
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    # ------------------------------------------------------------------
    # Called from http_server routes
    # ------------------------------------------------------------------

    def get_recent(self, n: int = 50) -> List[dict]:
        events = list(self._events)[-n:]
        events.reverse()
        return [e.to_dict() for e in events]

    def get_sessions(self) -> List[dict]:
        return list(self._sessions.values())

    def get_active_calls(self) -> List[dict]:
        return [e.to_dict() for e in self._active.values()]

    async def subscribe(self):
        """Async generator that yields SSE-formatted strings."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers.append(q)
        try:
            while True:
                event: ActivityEvent = await q.get()
                yield f"data: {json.dumps(event.to_dict())}\n\n"
        finally:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass


# Global singleton
tracker = ActivityTracker()
