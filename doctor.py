
#!/usr/bin/env python3
import importlib
print("Importing MCP adapter...")
m = importlib.import_module("servicenow_mcp.mcp_adapter")
print("Adapter OK")
import servicenow_mcp.packs as pk
print("Loaded packs:", getattr(pk, "__all__", []))
