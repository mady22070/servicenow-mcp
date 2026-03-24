# servicenow-mcp

An MCP (Model Context Protocol) server that lets Claude interact with a ServiceNow instance. Exposes ServiceNow functionality as tools Claude can call directly from Claude Desktop or any MCP-compatible client.

## Requirements

- Python 3.10+
- A ServiceNow instance (developer instance works fine)
- Claude Desktop or another MCP client

## Installation

```bash
pip install -r requirements.txt
```

For RAG-based knowledge search (optional):

```bash
pip install chromadb sentence-transformers
```

## Configuration

Set the following environment variables (or copy `.env.example` to `.env`):

```bash
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password

# Optional — enables semantic knowledge search
OPENAI_API_KEY=your-openai-key
```

## Claude Desktop setup

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["-m", "servicenow_mcp"],
      "env": {
        "SERVICENOW_INSTANCE_URL": "https://your-instance.service-now.com",
        "SERVICENOW_USERNAME": "your-username",
        "SERVICENOW_PASSWORD": "your-password"
      }
    }
  }
}
```

## What's included

Tools are grouped into packs by domain:

| Category | Packs |
|---|---|
| Core development | scripts, dev, background scripts, senior dev |
| Data / config | tables, data import/export, update sets, attachments |
| ITSM | incidents, changes, problems, requests, approvals |
| CMDB / discovery | CMDB, CSDM, discovery, ITAM, ITOM, SAM/HAM |
| Workflow | Flow Designer, pipelines, planner |
| Integrations | Scripted REST APIs, integration hub |
| UI | UI Builder, service catalog, UX |
| App development | scoped apps, best practices, naming conventions |
| Testing | ATF, troubleshooting |
| Knowledge | docs search, knowledge base, RAG search |
| Security | governance, impersonation, events |

## Running tests

```bash
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
