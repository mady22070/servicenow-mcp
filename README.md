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

## Choosing a transport

The server supports two transports:

| Transport | When to use |
|---|---|
| `stdio` (default) | Claude Desktop — the standard local setup |
| `http` | Cursor, Cline, LangChain, OpenAI Agents SDK, any web client |

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

## HTTP transport (Cursor, Cline, LangChain, OpenAI Agents SDK)

Start the server in HTTP mode:

```bash
MCP_TRANSPORT=http python -m servicenow_mcp
```

The MCP endpoint is at `http://localhost:8000/mcp`.

To require an API key on all requests:

```bash
MCP_TRANSPORT=http MCP_API_KEY=your-secret-key python -m servicenow_mcp
```

Clients must then include `Authorization: Bearer your-secret-key` in every request.

### Cursor / Cline config

```json
{
  "mcpServers": {
    "servicenow": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-secret-key"
      }
    }
  }
}
```

### Docker + HTTP mode

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e MCP_API_KEY=your-secret-key \
  -e SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com \
  -e SERVICENOW_USERNAME=your-username \
  -e SERVICENOW_PASSWORD=your-password \
  servicenow-mcp
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

## Running with Docker

If you don't want to deal with Python environments, you can run the server inside Docker instead.

1. Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

2. Copy `.env.example` to `.env` and fill in your ServiceNow credentials:
   ```bash
   cp .env.example .env
   # then open .env and set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, SERVICENOW_PASSWORD
   ```

3. Build and start the container:
   ```bash
   docker-compose up --build
   ```
   The first run will take a minute to download and build everything. After that it's fast.

4. To stop it:
   ```bash
   docker-compose down
   ```

That's it. Logs are saved to a `logs/` folder in the project directory.

> If you want to use it with Claude Desktop, you still need to run it via `python -m servicenow_mcp` (the Claude Desktop integration talks over stdin/stdout, not HTTP). Docker is more useful if you're running this as a standalone service or testing it independently.

## Running tests

```bash
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
