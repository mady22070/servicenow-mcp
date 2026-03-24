
from typing import Dict, Any, List, Callable
from .audit_simple import log
def execute_plan(step_fn_resolver: Callable[[str, str], Callable[..., Any]], plan: List[Dict[str, Any]],
                 confirm: bool = False, continue_on_error: bool = False) -> Dict[str, Any]:
    results = []; errors = []
    for i, step in enumerate(plan, 1):
        pack = step.get("pack"); func = step.get("func"); args = dict(step.get("args", {}))
        if not confirm and any(k in func for k in ("create","add","set","update","delete")):
            args["dry_run"] = True
        try:
            fn = step_fn_resolver(pack, func); res = fn(**args)
            results.append({"index": i, "pack": pack, "func": func, "ok": True, "result": res})
            log("plan_step", {"index": i, "pack": pack, "func": func, "dry_run": args.get("dry_run", False)})
        except Exception as e:
            err = {"index": i, "pack": pack, "func": func, "ok": False, "error": str(e)}
            errors.append(err); results.append(err)
            if not continue_on_error: break
    return {"ok": len(errors) == 0, "results": results, "errors": errors}
