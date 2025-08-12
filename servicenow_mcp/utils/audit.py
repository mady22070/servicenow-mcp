
import json, time, os
from pathlib import Path
AUDIT_PATH = Path(os.getenv("MCP_AUDIT_FILE", "audit.log")).expanduser()
def log(action: str, details: dict):
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "action": action, "details": details}) + "\n")
    except Exception:
        pass
