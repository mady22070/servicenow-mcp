
from typing import Dict, Any
import datetime, json
def _now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
def generate_docs(project_name: str, scope: str, audience: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    title = f"{project_name} — {audience.replace('_',' ').title()} Guide"
    body = [f"# {title}", "", f"_Generated {_now()}_", ""]
    if audience == "admin":
        body += ["## Promotion & Governance","- Environments: dev / test / prod","- Change gates: ATF pass required before promotion","","## Support Runbooks","- Clear cache (cache.do)","- Toggle properties and reschedule jobs"]
    elif audience == "developer":
        body += ["## Coding Standards","- Server: Script Includes namespaced; BRs before/after; GlideRecordSecure","- Client: avoid alert(); use g_form.addInfoMessage/warn","- Naming: tables x_<scope>_<name>, fields u_*","","## SDLC","- Small atomic update sets","- ATF for each acceptance criterion"]
    elif audience == "end_user":
        body += ["## What you can do","- Submit requests in the Catalog","- Track incidents and approvals","","## How to","1. Open the Service Catalog","2. Fill required fields (*)","3. Submit and monitor via Requests"]
    else:
        body += ["## Architecture Overview",f"- Scope: `{scope}`","- Integrations: REST Messages, Scripted REST","- Event/Discovery: rules and quick jobs","","## Objects Created",f"```json\n{json.dumps(inputs, indent=2)}\n```"]
    return {"title": title, "markdown": "\n".join(body)}
