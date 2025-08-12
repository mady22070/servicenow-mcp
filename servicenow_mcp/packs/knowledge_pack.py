
from typing import Dict, Any
from ..servicenow_client import ServiceNowClient
def create_knowledge_article(client: ServiceNowClient, fields: Dict[str, Any], table: str = "kb_knowledge", dry_run: bool = False) -> Dict[str, Any]:
    if dry_run: return {"dry_run": True, "table": table, "record": fields}
    return client.create_record(table, fields)
def publish_knowledge_article(client: ServiceNowClient, sys_id: str, table: str = "kb_knowledge", dry_run: bool = False) -> Dict[str, Any]:
    payload = {"workflow_state": "published", "valid_to": ""}
    if dry_run: return {"dry_run": True, "table": table, "sys_id": sys_id, "fields": payload}
    return client.update_record(table, sys_id, payload)
def search_knowledge(client: ServiceNowClient, query: str, limit: int = 20, table: str = "kb_knowledge") -> Dict[str, Any]:
    q = f"short_descriptionLIKE{query}^ORtextLIKE{query}^active=true"
    return {"items": client.query_table(table, query=q, fields=["sys_id","short_description","number","kb_knowledge_base"], limit=limit)}
def get_article_feedback(client: ServiceNowClient, article_sys_id: str, table: str = "kb_feedback", limit: int = 50) -> Dict[str, Any]:
    return {"items": client.query_table(table, query=f"article={article_sys_id}", fields=["sys_id","rating","comments","sys_created_on"], limit=limit)}
