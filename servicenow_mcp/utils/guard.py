import os

ALLOW = set([s.strip() for s in os.getenv("MCP_ALLOW_TABLES", "").split(",") if s.strip()])
DENY = set([s.strip() for s in os.getenv("MCP_DENY_TABLES", "").split(",") if s.strip()])

# Global kill switch: set MCP_GUARD_MODE=off to allow everything
MODE = (os.getenv("MCP_GUARD_MODE", "on") or "on").lower()

DANGEROUS_DEFAULTS = {
    "sys_user_password_reset", "sys_user", "sys_security_acl", "sys_encryption",
    "sys_properties", "sys_user_role", "sys_scope", "sys_script_include",
    "sys_script", "ua_workflow", "sys_choice", "cmn_location", "core_company"
}

def is_allowed(table: str, op: str = "read", override: bool = False) -> (bool, str):
    t = (table or "").strip()

    if override or MODE in ("off", "disable", "disabled", "all"):
        return True, "guard:off"

    if DENY and t in DENY:
        return False, f"Table {t} is denied by MCP_DENY_TABLES"

    if ALLOW and t not in ALLOW:
        return False, f"Table {t} not in MCP_ALLOW_TABLES"

    if not ALLOW and t in DANGEROUS_DEFAULTS and op != "read":
        return False, f"Write to {t} blocked by default guard. Pass override=true if intentional."

    return True, "ok"
