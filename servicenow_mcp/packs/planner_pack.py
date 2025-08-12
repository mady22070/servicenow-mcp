
from typing import Dict, Any, List
def plan_from_story(story: str, acceptance: str) -> Dict[str, Any]:
    text = f"{story}\n{acceptance}".lower()
    steps: List[Dict[str, Any]] = []
    def has(*words): return any(w in text for w in words)
    if has("table","field"): steps.append({"pack":"build","func":"app_scaffold","args":{"spec":{"tables":[]}, "dry_run":True}})
    if has("catalog item"): steps.append({"pack":"build","func":"create_catalog_item","args":{"name":"","category":"","description":"","dry_run":True}})
    if has("client script"): steps.append({"pack":"scripts","func":"add_client_script","args":{"table":"","name":"","ui_type":"onLoad","script":"","dry_run":True}})
    if has("jdbc","sql connection","data source"): steps.append({"pack":"data","func":"create_data_source_jdbc","args":{"name":"","connection_url":"","username":"","password":"","dry_run":True}})
    if has("event management","event rule","alert"): steps.append({"pack":"event","func":"create_event_rule","args":{"name":"","filter_query":"","dry_run":True}})
    if has("correlation"): steps.append({"pack":"event","func":"create_alert_correlation_rule","args":{"name":"","group_by":[],"dry_run":True}})
    if has("risk","assessment"): steps.append({"pack":"irm","func":"schedule_assessment","args":{"template":"","assignment_group":"","due_in_days":7,"population_query":"","dry_run":True}})
    if has("quick discovery","discover","ip address"): steps.append({"pack":"discovery","func":"quick_discovery","args":{"name":"Quick job","ips":[],"dry_run":True}})
    if not steps: steps.append({"pack":"query","func":"query_table","args":{"table":"incident","query":"","limit":5}})
    return {"plan": steps, "notes": "Fill args, run with dry_run=false to apply."}
