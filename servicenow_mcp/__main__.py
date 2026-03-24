"""
ServiceNow MCP Server - Module entry point for Claude Desktop
"""

import sys
import os

# Ensure we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicenow_mcp.mcp_adapter import mcp, logger, cleanup

if __name__ == "__main__":
    import atexit
    import signal
    
    # Register cleanup handlers
    atexit.register(cleanup)
    
    def signal_handler(signum, frame):
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the MCP server
        mcp.run()
    except Exception as e:
        logger.error(f"MCP server error: {str(e)}")
        sys.exit(1)
    finally:
        cleanup()