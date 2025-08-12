
from typing import Any, Dict, List, Optional
import requests

class ServiceNowClient:
    def __init__(self, instance_url: str, username: str, password: str, timeout: int = 30):
        self.base = instance_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.timeout = timeout

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base}{path}"

    def _headers(self) -> Dict[str, str]:
        return {"Accept": "application/json", "Content-Type": "application/json"}

    def _json(self, r: requests.Response) -> Dict[str, Any]:
        try:
            return r.json()
        except Exception:
            return {"error": "non_json_response", "status": r.status_code, "url": r.url, "text_snippet": (r.text or "")[:400]}

    # Generic request helpers
    def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r = self.session.request(method.upper(), self._url(path), headers=self._headers(), params=params, json=json, timeout=self.timeout)
        return self._json(r)

    def get_any(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("GET", path, params=params)

    def post_any(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("POST", path, json=payload)

    # Table APIs (Now Table)
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        r = self.session.post(self._url(f"/api/now/table/{table}"), headers=self._headers(), json=data, timeout=self.timeout)
        js = self._json(r)
        return js.get("result", js)

    def get_record(self, table: str, sys_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        params = {}
        if fields: params["sysparm_fields"] = ",".join(fields)
        r = self.session.get(self._url(f"/api/now/table/{table}/{sys_id}"), headers=self._headers(), params=params, timeout=self.timeout)
        js = self._json(r)
        return js.get("result", js)

    def update_record(self, table: str, sys_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        r = self.session.patch(self._url(f"/api/now/table/{table}/{sys_id}"), headers=self._headers(), json=data, timeout=self.timeout)
        js = self._json(r)
        return js.get("result", js)

    def delete_record(self, table: str, sys_id: str) -> Dict[str, Any]:
        r = self.session.delete(self._url(f"/api/now/table/{table}/{sys_id}"), headers=self._headers(), timeout=self.timeout)
        if r.status_code >= 400:
            return self._json(r)
        return {"deleted": True, "sys_id": sys_id}

    def query_table(self, table: str, query: str = "", fields: Optional[List[str]] = None, limit: int = 100, display: bool = False) -> Dict[str, Any]:
        params = {"sysparm_limit": str(limit)}
        if query: params["sysparm_query"] = query
        if fields: params["sysparm_fields"] = ",".join(fields)
        if display: params["sysparm_display_value"] = "all"
        r = self.session.get(self._url(f"/api/now/table/{table}"), headers=self._headers(), params=params, timeout=self.timeout)
        js = self._json(r)
        return js.get("result", js)

    # Attachments
    def upload_attachment(self, table: str, sys_id: str, file_path: str, file_name: str = "") -> Dict[str, Any]:
        import mimetypes
        file_name = file_name or (file_path.split('/')[-1])
        url = self._url("/api/now/attachment/file")
        params = {"table_name": table, "table_sys_id": sys_id, "file_name": file_name}
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, mimetypes.guess_type(file_name)[0] or "application/octet-stream")}
            r = self.session.post(url, params=params, files=files, timeout=self.timeout)
        return self._json(r)

    def list_attachments(self, table: str, sys_id: str, limit: int = 50) -> Dict[str, Any]:
        q = f"table_name={table}^table_sys_id={sys_id}"
        return self.query_table("sys_attachment", query=q, fields=["sys_id","file_name","size_bytes","content_type","sys_created_on"], limit=limit)

    def download_attachment(self, attachment_sys_id: str, out_path: str) -> Dict[str, Any]:
        url = self._url(f"/api/now/attachment/{attachment_sys_id}/file")
        r = self.session.get(url, timeout=self.timeout, stream=True)
        if r.status_code >= 400:
            return self._json(r)
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
        return {"saved": True, "path": out_path, "attachment_sys_id": attachment_sys_id}

    # Higher-level helpers used by packs
    def create_table(self, table_label: str, table_name: str, extends: Optional[str] = None, scope: Optional[str] = None) -> Dict[str, Any]:
        rec = {"name": table_name, "label": table_label}
        if extends: rec["super_class"] = extends
        return self.create_record("sys_db_object", rec)

    def add_field(self, table_name: str, name: str, ftype: str, label: str, mandatory: bool = False,
                  default: Optional[str] = None, choices: Optional[List[str]] = None, scope: Optional[str] = None) -> Dict[str, Any]:
        rec = {
            "name": table_name,
            "element": name,
            "internal_type": ftype,
            "column_label": label,
            "mandatory": "true" if mandatory else "false",
        }
        if default is not None:
            rec["default_value"] = default
        d = self.create_record("sys_dictionary", rec)
        if choices:
            for c in choices:
                self.create_record("sys_choice", {"name": table_name, "element": name, "label": c, "value": c})
        return d

    def add_choice(self, table_name: str, element: str, choices: List[str]) -> Dict[str, Any]:
        out = []
        for c in choices:
            out.append(self.create_record("sys_choice", {"name": table_name, "element": element, "label": c, "value": c}))
        return {"results": out}

    def add_catalog_variable(self, item_sys_id: str, vtype: str, name: str, question: str, choices: Optional[List[str]] = None) -> Dict[str, Any]:
        rec = {"cat_item": item_sys_id, "name": name, "question_text": question, "type": vtype}
        v = self.create_record("item_option_new", rec)
        if choices:
            for c in choices:
                self.create_record("question_choice", {"item_option_new": v.get("sys_id"), "text": c, "value": c})
        return v

    def add_catalog_client_script(self, item_sys_id: str, ui_type: str, script: str) -> Dict[str, Any]:
        return self.create_record("sc_cat_item_client_script", {"cat_item": item_sys_id, "ui_type": ui_type, "script": script})

    # Operate helpers
    def get_syslog_transactions(self, since_minutes: int = 60, limit: int = 100) -> List[Dict[str, Any]]:
        q = f"sys_created_onRELATIVEGT@minute@ago@{since_minutes}"
        fields = ["sys_created_on","response_time","url","user"]
        return self.query_table("syslog_transaction", query=q, fields=fields, limit=limit)

    def get_execution_trackers(self, limit: int = 100) -> List[Dict[str, Any]]:
        fields = ["sys_id","name","state","progress","started","duration"]
        return self.query_table("sys_execution_tracker", fields=fields, limit=limit)

    def get_ecc_queue(self, states: Optional[List[str]] = None, since_minutes: int = 120, limit: int = 100) -> List[Dict[str, Any]]:
        q = f"sys_created_onRELATIVEGT@minute@ago@{since_minutes}"
        if states:
            q += "^" + "^".join([f"state={s}" for s in states])
        fields = ["sys_id","agent","topic","state","queue","created"]
        return self.query_table("ecc_queue", query=q, fields=fields, limit=limit)

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        fields = ["sys_id","source","node","resource","severity","time_of_event","state"]
        return self.query_table("em_event", fields=fields, limit=limit)

    def get_relationships(self, ci_sys_id: str, direction: str = "both", limit: int = 200) -> List[Dict[str, Any]]:
        parts = []
        if direction in ("both","up"):
            parts.append(f"child={ci_sys_id}")
        if direction in ("both","down"):
            parts.append(f"parent={ci_sys_id}")
        q = "^OR".join(parts) if parts else ""
        fields = ["sys_id","parent","child","type"]
        return self.query_table("cmdb_rel_ci", query=q, fields=fields, limit=limit)

    # Stats/Aggregates
    def stats(self, table: str, query: str = "", group_by: Optional[List[str]] = None, count: bool = True,
              sum: Optional[List[str]] = None, avg: Optional[List[str]] = None, minv: Optional[List[str]] = None, maxv: Optional[List[str]] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if query: params["sysparm_query"] = query
        if group_by: params["sysparm_group_by"] = ",".join(group_by)
        if count: params["sysparm_count"] = "true"
        if sum: params["sysparm_sum_fields"] = ",".join(sum)
        if avg: params["sysparm_avg_fields"] = ",".join(avg)
        if minv: params["sysparm_min_fields"] = ",".join(minv)
        if maxv: params["sysparm_max_fields"] = ",".join(maxv)
        r = self.session.get(self._url(f"/api/now/stats/{table}"), headers=self._headers(), params=params, timeout=self.timeout)
        return self._json(r)
