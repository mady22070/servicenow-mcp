import atexit
import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicenow_mcp.mcp_adapter import mcp, logger, cleanup

if __name__ == "__main__":
    atexit.register(cleanup)

    def _on_signal(signum, frame):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    try:
        if transport == "http":
            from servicenow_mcp.http_server import start
            host = os.getenv("MCP_HOST", "0.0.0.0")
            port = int(os.getenv("MCP_PORT", "8000"))
            api_key = os.getenv("MCP_API_KEY") or None
            logger.info(f"Starting HTTP transport on {host}:{port}")
            start(mcp, host, port, api_key)
        else:
            mcp.run()
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        cleanup()
