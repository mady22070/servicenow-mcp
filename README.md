# ServiceNow MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

A comprehensive Model Context Protocol (MCP) server that provides AI assistants with powerful ServiceNow integration capabilities. This server enables automated operations, advanced troubleshooting, and sophisticated development workflows within ServiceNow instances.

## 🚀 Features

### Core Capabilities
- **Multi-environment support** (dev/test/prod)
- **Comprehensive ServiceNow operations** through modular "packs"
- **Built-in security guards** and workspace management
- **Advanced caching and connection pooling**
- **Comprehensive error handling and logging**

### Senior Developer Features
- **Story-to-Implementation Pipeline**: Convert user stories into executable ServiceNow plans
- **Advanced CMDB Troubleshooting**: Sophisticated duplicate detection and data quality analysis
- **Root Cause Analysis**: Systematic problem investigation with correlation analysis
- **Development Planning**: Automated task decomposition and dependency management

### Supported ServiceNow Areas
- **ITSM**: Incidents, Problems, Changes, Requests
- **CMDB**: Configuration items, relationships, discovery
- **Development**: Scripts, business rules, UI policies, flows
- **Platform**: Tables, fields, users, groups, notifications
- **Automation**: Workflows, scheduled jobs, integrations
- **Quality**: ATF testing, data validation, performance monitoring

## 📋 Prerequisites

- Python 3.8 or higher
- ServiceNow instance (any version)
- ServiceNow user account with appropriate permissions
- MCP-compatible AI assistant (Claude Desktop, etc.)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/mady22070/servicenow-mcp.git
cd servicenow-mcp
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create environment variables for your ServiceNow instance:

```bash
# Development environment
export SERVICENOW_DEV_INSTANCE_URL=https://devXXX.service-now.com
export SERVICENOW_DEV_USERNAME=your_username
export SERVICENOW_DEV_PASSWORD=your_password

# Optional: Production environment
export SERVICENOW_PROD_INSTANCE_URL=https://yourinstance.service-now.com
export SERVICENOW_PROD_USERNAME=prod_username
export SERVICENOW_PROD_PASSWORD=prod_password

# Optional: Restrict table access during testing
export MCP_ALLOW_TABLES=sys_script,sys_script_include,ui_policy,ui_policy_action
```

## 🚀 Quick Start

### 1. Start the MCP Server
```bash
python mcp_adapter.py
```

### 2. Configure Your MCP Client
Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["/path/to/servicenow-mcp/mcp_adapter.py"],
      "env": {
        "SERVICENOW_DEV_INSTANCE_URL": "https://devXXX.service-now.com",
        "SERVICENOW_DEV_USERNAME": "your_username",
        "SERVICENOW_DEV_PASSWORD": "your_password"
      }
    }
  }
}
```

### 3. Test the Connection
```bash
# Run health check
python doctor.py
```

## 📖 Usage Examples

### Basic Operations
```python
# Create an incident
create_incident(
    short_description="Server outage in production",
    description="Web servers are not responding",
    additional_fields={"urgency": "1", "impact": "1"}
)

# Query records
query_table(
    table="incident",
    query="state=1^urgency=1",
    fields=["number", "short_description", "state"],
    limit=10
)
```

### Story-Driven Development
```python
# Convert user story to implementation plan
story_to_implementation(
    story="As a service desk agent, I want to automatically assign incidents based on category so that tickets are routed to the right team faster"
)
```

### Advanced CMDB Analysis
```python
# Detect and analyze CMDB duplicates
troubleshoot_cmdb_duplicates(
    ci_class="cmdb_ci_server",
    analysis_fields=["name", "ip_address", "serial_number"],
    limit=100
)
```

### Root Cause Analysis
```python
# Investigate system issues
root_cause_analysis(
    issue_description="Users reporting slow form loading times",
    related_table="incident",
    time_range_hours=24
)
```

## 🏗️ Architecture

The ServiceNow MCP server is built with a modular architecture:

```
servicenow_mcp/
├── mcp_adapter.py          # Main MCP server entry point
├── client_manager.py       # Connection pooling and lifecycle
├── tool_registry.py        # Centralized tool registration
├── config.py              # Environment configuration
├── decorators.py           # Cross-cutting concerns
├── packs/                 # Functional modules
│   ├── query_pack.py      # Data querying and statistics
│   ├── build_pack.py      # Application development
│   ├── senior_dev_pack.py # Advanced development features
│   ├── story_driven_pack.py # Story-to-implementation
│   └── ...               # 20+ specialized packs
├── utils/                 # Utility functions
│   ├── guard.py          # Security controls
│   ├── plan.py           # Multi-step execution
│   └── workspace.py      # Workspace management
└── tools/                # Tool definitions by area
    └── ...
```

## 🔒 Security

- **Table Guards**: Configurable access controls for sensitive tables
- **Environment Isolation**: Separate configurations for dev/test/prod
- **Dry Run Mode**: Test operations without making changes
- **Audit Logging**: Comprehensive operation tracking
- **Credential Management**: Secure environment variable handling

## 🧪 Testing

```bash
# Run basic health checks
python doctor.py

# Test specific functionality
python -c "from servicenow_mcp.client_manager import client_manager; print(client_manager.health_check())"

# Validate configuration
python -c "from servicenow_mcp.config import Config; print(Config.for_env('dev'))"
```

## 📚 Documentation

- [API Reference](docs/api-reference.md) - Complete tool documentation
- [Configuration Guide](docs/configuration.md) - Setup and environment management
- [Development Guide](docs/development.md) - Contributing and extending
- [Examples](examples/) - Real-world usage scenarios
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone and setup
git clone https://github.com/mady22070/servicenow-mcp.git
cd servicenow-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black servicenow_mcp/
isort servicenow_mcp/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the foundational framework
- [ServiceNow](https://www.servicenow.com/) for the platform APIs
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server implementation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/mady22070/servicenow-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mady22070/servicenow-mcp/discussions)
- **Documentation**: [Wiki](https://github.com/mady22070/servicenow-mcp/wiki)

## 🗺️ Roadmap

- [ ] GraphQL API support
- [ ] Advanced workflow automation
- [ ] Machine learning integration
- [ ] Performance optimization tools
- [ ] Extended ITOM capabilities
- [ ] Custom app scaffolding templates

---

**Made with ❤️ for the ServiceNow community**