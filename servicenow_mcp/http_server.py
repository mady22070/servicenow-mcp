import uvicorn


class _ApiKeyMiddleware:
    """Pure ASGI middleware — checks Bearer token before passing the request through.
    Uses the raw ASGI interface rather than Starlette's BaseHTTPMiddleware so that
    streaming / SSE responses aren't buffered."""

    def __init__(self, app, api_key):
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = {k: v for k, v in scope.get("headers", [])}
            auth = headers.get(b"authorization", b"").decode()
            if not auth.startswith("Bearer ") or auth[7:] != self.api_key:
                await send({
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"content-type", b"text/plain")],
                })
                await send({"type": "http.response.body", "body": b"Unauthorized"})
                return
        await self.app(scope, receive, send)


def start(mcp_server, host, port, api_key=None):
    app = mcp_server.streamable_http_app()
    if api_key:
        app = _ApiKeyMiddleware(app, api_key)
    uvicorn.run(app, host=host, port=port, log_level="info")
