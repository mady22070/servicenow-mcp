
from typing import Any, Dict, List, Optional
from ..servicenow_client import ServiceNowClient
def query_table(client: ServiceNowClient, table: str, query: str = "", fields: Optional[List[str]] = None, limit: int = 100, display: bool = False) -> Dict[str, Any]:
    return {"items": client.query_table(table, query, fields, limit, display)}
def stats(client: ServiceNowClient, table: str, query: str = "", group_by: Optional[List[str]] = None, count: bool = True,
          sum: Optional[List[str]] = None, avg: Optional[List[str]] = None, minv: Optional[List[str]] = None, maxv: Optional[List[str]] = None) -> Dict[str, Any]:
    return client.stats(table, query, group_by, count, sum, avg, minv, maxv)
def ci_graph(client: ServiceNowClient, root_sys_id: str, direction: str = "both", depth: int = 2, limit: int = 200) -> Dict[str, Any]:
    visited = set([root_sys_id]); frontier = [root_sys_id]; edges = []
    for _ in range(max(depth, 0)):
        new_frontier = []
        for ci in frontier:
            rels = client.get_relationships(ci, direction=direction, limit=limit)
            if isinstance(rels, list):
                for r in rels:
                    parent = r.get("parent"); child = r.get("child")
                    if parent and child:
                        edges.append({"parent": parent, "child": child, "type": r.get("type")})
                        for nxt in (parent, child):
                            if nxt not in visited:
                                visited.add(nxt); new_frontier.append(nxt)
        frontier = new_frontier
    return {"root": root_sys_id, "nodes": list(visited), "edges": edges[:limit]}
