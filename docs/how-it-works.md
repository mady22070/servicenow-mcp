# How this MCP server works

## What is MCP?

MCP (Model Context Protocol) is an open standard that lets AI assistants like Claude talk to external systems. Instead of Claude just knowing things from its training data, MCP lets it actually *do* things — query a database, create a record, run a script — by calling tools that your server exposes.

Think of it like giving Claude a set of functions it can call whenever it needs to interact with ServiceNow. You run this server locally, Claude Desktop connects to it, and from that point Claude can do things like "create an incident", "query the CMDB", or "run a background script" directly.

---

## How the pieces fit together

```
Claude Desktop
     |
     | (stdin/stdout — MCP protocol)
     |
servicenow_mcp (this server)
     |
     | (HTTPS REST API — basic auth)
     |
Your ServiceNow instance
```

When you ask Claude something like "show me all P1 incidents from today", Claude:
1. Picks the right tool (`query_table`)
2. Sends a tool call to this server over stdin/stdout
3. This server makes a REST API call to your ServiceNow instance
4. Gets the result back and returns it to Claude
5. Claude reads the result and responds to you

---

## Entry point

When Claude Desktop starts this server, it runs `python -m servicenow_mcp`, which hits [servicenow_mcp/__main__.py](../servicenow_mcp/__main__.py). That imports the FastMCP server from [servicenow_mcp/mcp_adapter.py](../servicenow_mcp/mcp_adapter.py) and calls `mcp.run()`.

All 182+ tools are registered in `mcp_adapter.py` using FastMCP's decorator pattern:

```python
@mcp.tool()
def query_table(table: str, query: str = "", limit: int = 100, env: str = "dev"):
    """Query a ServiceNow table with filters"""
    ...
```

FastMCP automatically handles the MCP protocol handshake, tool discovery, and message routing.

---

## Pack system

Rather than dumping all tools in one file, tools are grouped into **domain packs** — one file per functional area. `mcp_adapter.py` imports from each pack and wraps the pack functions as MCP tools.

```
servicenow_mcp/packs/
├── scripts_pack.py        # Business rules, client scripts, script includes
├── flow_pack.py           # Flow Designer
├── cmdb_pack.py           # CMDB and CI management
├── csm_pack.py            # Customer Service Management
├── itom_pack.py           # IT Operations Management
├── sam_ham_pack.py        # Software and Hardware Asset Management
├── rag_knowledge_pack.py  # Semantic knowledge search
└── ... (53 packs total)
```

Each pack function takes a `ServiceNowClient` instance as its first argument and returns a plain dict. The client handles the actual HTTP calls to ServiceNow.

---

## Multi-environment support

The server supports connecting to multiple ServiceNow instances at once — dev, test, and production. Most tools accept an `env` parameter that defaults to `"dev"`. Set the relevant environment variables and Claude can target any of them:

```bash
SERVICENOW_DEV_INSTANCE_URL=...
SERVICENOW_TEST_INSTANCE_URL=...
SERVICENOW_PROD_INSTANCE_URL=...
```

---

## RAG knowledge search

The server includes an optional vector database (ChromaDB) for semantic search across ServiceNow documentation and knowledge articles. When enabled, tools like `semantic_knowledge_search` can answer questions like "how do I configure a business rule for incident SLA" by searching embeddings rather than exact keywords.

Requires either `sentence-transformers` for local embeddings or an OpenAI API key for cloud embeddings.

---

## What tools are available

182 tools across 11 domains:

| Domain | Example tools |
|---|---|
| Core dev | `create_business_rule`, `add_client_script`, `execute_background_script` |
| Tables / data | `query_table`, `create_record`, `update_record`, `bulk_import` |
| ITSM | `create_incident`, `create_change_request`, `manage_approval` |
| CMDB | `query_cmdb`, `discover_csdm_topology`, `validate_ci_relationships` |
| Workflows | `create_flow`, `add_flow_action`, `activate_flow` |
| Integrations | `create_scripted_rest_api`, `test_rest_endpoint` |
| Service catalog | `create_catalog_item`, `manage_variables` |
| Scoped apps | `create_scoped_application`, `validate_naming_conventions` |
| Testing | `create_atf_test`, `run_atf_suite` |
| Knowledge | `search_knowledge_base`, `semantic_knowledge_search` |
| Security | `manage_acl`, `impersonate_user` |

---

## MCP best practices audit

Here's how this server holds up against the current MCP spec (2025-11-25):

| Area | Status | Detail |
|---|---|---|
| Transport | OK | Uses stdio — correct for Claude Desktop integration |
| Tool registration | OK | Consistent `@mcp.tool()` decorator pattern throughout |
| Tool naming | OK | snake_case, descriptive, action-based names |
| Console logging | OK | Disabled by default so it doesn't corrupt the stdio stream |
| Tool descriptions | Inconsistent | Some tools have full docstrings with Args/Returns/Examples; others have one-liners. Claude relies on these to know when and how to call a tool. |
| Output schemas | Missing | MCP supports `outputSchema` to tell Claude what shape the response will be. None defined here. |
| Resources | Not used | MCP has a "Resources" primitive for exposing read-only data (docs, templates, schemas). Not implemented. |
| Prompts | Not used | MCP supports reusable prompt templates. Not implemented — not critical but useful for guided workflows. |
| Error format | Partial | Some tools use a `@handle_errors` decorator; others catch exceptions inconsistently. Should be uniform. |
| Authentication | None at MCP level | The MCP server itself has no authentication — anyone who can run it gets all tools. This is fine for local Claude Desktop use (only you run it), but worth noting if you ever expose it remotely. |
| FastMCP version | `mcp>=0.1.0` | Very loose version pin. Worth tightening to avoid surprises on install. |

**The two things most worth fixing:**
1. Standardise docstrings on all tools — Claude uses them to decide which tool to pick and how to call it
2. Pin the `mcp` version in `requirements.txt`

---

## How this compares to other ServiceNow MCP servers

Five other ServiceNow MCP servers exist publicly:

| Server | Tools | Notable |
|---|---|---|
| [aartiq/servicenow-mcp](https://github.com/aartiq/servicenow-mcp) | 400+ | Most tools, 5-tier permission model, autonomous script deployment |
| [echelon-ai-labs/servicenow-mcp](https://github.com/echelon-ai-labs/servicenow-mcp) | 80+ | SSE streaming, multiple auth methods |
| [shunyaai/snow-mcp](https://github.com/shunyaai/snow-mcp) | 60+ | Good retry logic, production validation |
| [Happy-Technologies-LLC/mcp-servicenow-nodejs](https://github.com/Happy-Technologies-LLC/mcp-servicenow-nodejs) | 44 | Auto-discovers table schemas, Node.js, HTTP transport |
| [michaelbuckner/servicenow-mcp](https://github.com/michaelbuckner/servicenow-mcp) | 10 | Minimal starter template |

**Where this server stands:**

Strengths over the field:
- Only server with CSDM 5.0 topology support
- Only server with RAG / vector search
- Best pack organisation — 53 focused domain modules vs flat lists
- Second highest tool count (182), but better organised than aartiq's 400+
- Multi-environment (dev/test/prod) out of the box

Gaps vs the field:
- aartiq has more raw tools and supports autonomous ATF execution and script deployment
- Happy Tech auto-discovers table schemas — this server requires manual pack definitions
- No HTTP transport option (stdio only)
- No granular permission model (aartiq has a 5-tier system)

**Bottom line:** top tier for depth and organisation. The main gap is aartiq's broader automation surface — if you need to autonomously deploy scripts or run ATF without human confirmation, aartiq covers more of that.
