
import json, os
from pathlib import Path
from typing import Dict, Any
PATH = Path(os.getenv("MCP_WORKSPACES_FILE", "workspaces.json")).expanduser()
def _load() -> Dict[str, Any]:
    if PATH.exists():
        try: return json.loads(PATH.read_text(encoding="utf-8"))
        except Exception: return {}
    return {}
def _save(data: Dict[str, Any]):
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
def list_workspaces():
    return list(_load().keys())
def get_workspace(name: str = "default") -> Dict[str, Any]:
    return _load().get(name, {"env": "dev", "scope": "x_cloudorch_aiops", "confirm": False})
def set_workspace(name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    data = _load(); ws = data.get(name, {"env": "dev", "scope": "x_cloudorch_aiops", "confirm": False})
    ws.update({k:v for k,v in updates.items() if v is not None}); data[name] = ws; _save(data); return ws
