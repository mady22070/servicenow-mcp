
from typing import Any, Dict, List, Optional
import requests
import time
from datetime import datetime

from .logging_config import get_logger, LogContext
from .error_handler import ServiceNowError, TimeoutError, AuthenticationError
from .constants import (
    ServiceNowAPI, HTTPStatus, ServiceNowTables, DefaultValues, 
    Headers, ValidationMessages
)

class ServiceNowClient:
    def __init__(self, instance_url: str, username: str, password: str, timeout: int = 30):
        self.base = instance_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.timeout = timeout
        self.logger = get_logger()
        
        # Set default headers
        self.session.headers.update({
            Headers.ACCEPT: Headers.APPLICATION_JSON,
            Headers.CONTENT_TYPE: Headers.APPLICATION_JSON,
            Headers.USER_AGENT: Headers.MCP_USER_AGENT
        })

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base}{path}"



    def _json(self, r: requests.Response) -> Dict[str, Any]:
        """Parse JSON response with error handling"""
        try:
            return r.json()
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return {
                "error": "non_json_response", 
                "status": r.status_code, 
                "url": str(r.url), 
                "text_snippet": (r.text or "")[:400]
            }
    
    def _handle_response(self, r: requests.Response, operation: str = "request") -> Dict[str, Any]:
        """Handle HTTP response with comprehensive error checking"""
        duration_ms = getattr(r, '_duration_ms', 0)
        
        with LogContext(self.logger, 
                       operation=operation,
                       status_code=r.status_code,
                       duration_ms=duration_ms,
                       url=str(r.url)):
            
            # Check for authentication errors
            if r.status_code == HTTPStatus.UNAUTHORIZED:
                self.logger.error("Authentication failed")
                raise AuthenticationError("Invalid credentials or session expired")
            
            # Check for other client/server errors
            if r.status_code >= HTTPStatus.BAD_REQUEST:
                error_text = r.text[:400] if r.text else "No error details"
                self.logger.error(f"HTTP {r.status_code}: {error_text}")
                raise ServiceNowError(
                    f"HTTP {r.status_code}: {error_text}",
                    status_code=r.status_code,
                    response_data=self._json(r) if r.text else None
                )
            
            # Success - parse and return JSON
            result = self._json(r)
            self.logger.debug(f"Request successful: {operation}")
            return result

    # Generic request helpers
    def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request with timing and error handling"""
        start_time = time.time()
        
        try:
            r = self.session.request(
                method.upper(), 
                self._url(path), 
                params=params, 
                json=json, 
                timeout=self.timeout
            )
            
            # Add timing information
            r._duration_ms = (time.time() - start_time) * 1000
            
            return self._handle_response(r, f"{method.upper()} {path}")
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.ConnectionError as e:
            raise ServiceNowError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Request error: {str(e)}")

    def get_any(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("GET", path, params=params)

    def post_any(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("POST", path, json=payload)

    # Table APIs (Now Table)
    def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a record in ServiceNow table"""
        if not table or not table.strip():
            raise ValueError(ValidationMessages.EMPTY_TABLE_NAME)
        if not data:
            raise ValueError(ValidationMessages.EMPTY_DATA)
        if not isinstance(data, dict):
            raise TypeError(ValidationMessages.INVALID_DATA_TYPE)
        
        start_time = time.time()
        
        try:
            r = self.session.post(
                self._url(f"{ServiceNowAPI.TABLE_API}/{table}"), 
                json=data, 
                timeout=self.timeout
            )
            r._duration_ms = (time.time() - start_time) * 1000
            
            result = self._handle_response(r, f"CREATE {table}")
            return result.get("result", result)
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Create record timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Create record error: {str(e)}")

    def get_record(self, table: str, sys_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a record from ServiceNow table"""
        if not table or not table.strip():
            raise ValueError(ValidationMessages.EMPTY_TABLE_NAME)
        if not sys_id or not sys_id.strip():
            raise ValueError(ValidationMessages.EMPTY_SYS_ID)
        
        start_time = time.time()
        params = {}
        if fields: 
            params["sysparm_fields"] = ",".join(fields)
        
        try:
            r = self.session.get(
                self._url(f"/api/now/table/{table}/{sys_id}"), 
                params=params, 
                timeout=self.timeout
            )
            r._duration_ms = (time.time() - start_time) * 1000
            
            result = self._handle_response(r, f"GET {table}/{sys_id}")
            return result.get("result", result)
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Get record timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Get record error: {str(e)}")

    def update_record(self, table: str, sys_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record in ServiceNow table"""
        if not table or not table.strip():
            raise ValueError("Table name cannot be empty")
        if not sys_id or not sys_id.strip():
            raise ValueError("sys_id cannot be empty")
        if not data:
            raise ValueError("Data cannot be empty")
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary")
        
        start_time = time.time()
        
        try:
            r = self.session.patch(
                self._url(f"/api/now/table/{table}/{sys_id}"), 
                json=data, 
                timeout=self.timeout
            )
            r._duration_ms = (time.time() - start_time) * 1000
            
            result = self._handle_response(r, f"UPDATE {table}/{sys_id}")
            return result.get("result", result)
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Update record timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Update record error: {str(e)}")

    def delete_record(self, table: str, sys_id: str) -> Dict[str, Any]:
        """Delete a record from ServiceNow table"""
        start_time = time.time()
        
        try:
            r = self.session.delete(
                self._url(f"/api/now/table/{table}/{sys_id}"), 
                timeout=self.timeout
            )
            r._duration_ms = (time.time() - start_time) * 1000
            
            # For delete operations, success is indicated by 204 No Content
            if r.status_code == 204:
                return {"deleted": True, "sys_id": sys_id}
            
            # Handle other responses through standard error handling
            result = self._handle_response(r, f"DELETE {table}/{sys_id}")
            return result
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Delete record timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Delete record error: {str(e)}")

    def query_table(self, table: str, query: str = "", fields: Optional[List[str]] = None, limit: int = 100, display: bool = False) -> Dict[str, Any]:
        """Query records from ServiceNow table"""
        if not table or not table.strip():
            raise ValueError("Table name cannot be empty")
        if limit <= 0:
            raise ValueError(ValidationMessages.INVALID_LIMIT)
        if limit > DefaultValues.MAX_QUERY_LIMIT:
            raise ValueError(ValidationMessages.LIMIT_EXCEEDED)
        
        start_time = time.time()
        params = {"sysparm_limit": str(limit)}
        if query: 
            params["sysparm_query"] = query
        if fields: 
            params["sysparm_fields"] = ",".join(fields)
        if display: 
            params["sysparm_display_value"] = "all"
        
        try:
            r = self.session.get(
                self._url(f"/api/now/table/{table}"), 
                params=params, 
                timeout=self.timeout
            )
            r._duration_ms = (time.time() - start_time) * 1000
            
            result = self._handle_response(r, f"QUERY {table}")
            return result.get("result", result)
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Query table timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Query table error: {str(e)}")

    # Attachments
    def upload_attachment(self, table: str, sys_id: str, file_path: str, file_name: str = "") -> Dict[str, Any]:
        """Upload file attachment to ServiceNow record"""
        import mimetypes
        start_time = time.time()
        
        if not table or not table.strip():
            raise ValueError("Table name cannot be empty")
        if not sys_id or not sys_id.strip():
            raise ValueError("sys_id cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")
        
        file_name = file_name or (file_path.split('/')[-1])
        url = self._url("/api/now/attachment/file")
        params = {"table_name": table, "table_sys_id": sys_id, "file_name": file_name}
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, mimetypes.guess_type(file_name)[0] or "application/octet-stream")}
                r = self.session.post(url, params=params, files=files, timeout=self.timeout)
                
            r._duration_ms = (time.time() - start_time) * 1000
            return self._handle_response(r, f"UPLOAD_ATTACHMENT {table}/{sys_id}")
            
        except FileNotFoundError:
            raise ServiceNowError(f"File not found: {file_path}")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Upload timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Upload error: {str(e)}")

    def list_attachments(self, table: str, sys_id: str, limit: int = 50) -> Dict[str, Any]:
        q = f"table_name={table}^table_sys_id={sys_id}"
        return self.query_table("sys_attachment", query=q, fields=["sys_id","file_name","size_bytes","content_type","sys_created_on"], limit=limit)

    def download_attachment(self, attachment_sys_id: str, out_path: str) -> Dict[str, Any]:
        """Download attachment from ServiceNow"""
        start_time = time.time()
        
        if not attachment_sys_id or not attachment_sys_id.strip():
            raise ValueError("attachment_sys_id cannot be empty")
        if not out_path or not out_path.strip():
            raise ValueError("out_path cannot be empty")
        
        url = self._url(f"/api/now/attachment/{attachment_sys_id}/file")
        
        try:
            r = self.session.get(url, timeout=self.timeout, stream=True)
            r._duration_ms = (time.time() - start_time) * 1000
            
            # Check for errors before processing stream
            if r.status_code >= 400:
                return self._handle_response(r, f"DOWNLOAD_ATTACHMENT {attachment_sys_id}")
            
            # Success - write file
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: 
                        f.write(chunk)
            
            self.logger.info(f"Downloaded attachment {attachment_sys_id} to {out_path}")
            return {"saved": True, "path": out_path, "attachment_sys_id": attachment_sys_id}
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Download timeout after {self.timeout}s", self.timeout)
        except IOError as e:
            raise ServiceNowError(f"File write error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Download error: {str(e)}")

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
        """Get statistics and aggregations from ServiceNow table"""
        start_time = time.time()
        params: Dict[str, Any] = {}
        if query: 
            params["sysparm_query"] = query
        if group_by: 
            params["sysparm_group_by"] = ",".join(group_by)
        if count: 
            params["sysparm_count"] = "true"
        if sum: 
            params["sysparm_sum_fields"] = ",".join(sum)
        if avg: 
            params["sysparm_avg_fields"] = ",".join(avg)
        if minv: 
            params["sysparm_min_fields"] = ",".join(minv)
        if maxv: 
            params["sysparm_max_fields"] = ",".join(maxv)
        
        try:
            r = self.session.get(
                self._url(f"/api/now/stats/{table}"), 
                params=params, 
                timeout=self.timeout
            )
            r._duration_ms = (time.time() - start_time) * 1000
            
            return self._handle_response(r, f"STATS {table}")
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Stats query timeout after {self.timeout}s", self.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceNowError(f"Stats query error: {str(e)}")
