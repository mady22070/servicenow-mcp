# Claude Desktop Setup Guide

Complete step-by-step guide to set up and use ServiceNow MCP with Claude Desktop.

## 📋 Prerequisites

Before starting, ensure you have:
- **Claude Desktop** installed on your computer
- **Python 3.8+** installed
- **ServiceNow instance** access (dev, test, or prod)
- **ServiceNow user account** with appropriate permissions
- **Git** installed (for cloning the repository)

## 🚀 Step 1: Install ServiceNow MCP Server

### Option A: Install from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/mady22070/servicenow-mcp.git
cd servicenow-mcp

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option B: Install via pip (when available)

```bash
pip install servicenow-mcp
```

## 🔧 Step 2: Configure ServiceNow Connection

### Create Environment Configuration

1. **Copy the example environment file:**
```bash
cp .env.example .env
```

2. **Edit the `.env` file with your ServiceNow details:**
```bash
# Open in your preferred editor
nano .env
# or
code .env
```

3. **Add your ServiceNow instance details:**
```bash
# Development Environment (Required)
SERVICENOW_DEV_INSTANCE_URL=https://devXXX.service-now.com
SERVICENOW_DEV_USERNAME=your_username
SERVICENOW_DEV_PASSWORD=your_password

# Optional: Production Environment
SERVICENOW_PROD_INSTANCE_URL=https://yourinstance.service-now.com
SERVICENOW_PROD_USERNAME=prod_username
SERVICENOW_PROD_PASSWORD=prod_password

# Optional: Security Configuration
MCP_ALLOW_TABLES=incident,problem,change_request,sys_script
```

### Test Your Connection

```bash
# Test the connection
python doctor.py

# Expected output:
# ✅ ServiceNow connection successful
# ✅ User permissions verified
# ✅ MCP server ready
```

## 🖥️ Step 3: Configure Claude Desktop

### Locate Claude Desktop Configuration

Find your Claude Desktop configuration file:

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

### Add ServiceNow MCP Configuration

1. **Open the configuration file** (create if it doesn't exist):
```bash
# macOS
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows
notepad %APPDATA%\Claude\claude_desktop_config.json

# Linux
code ~/.config/Claude/claude_desktop_config.json
```

2. **Add the ServiceNow MCP server configuration:**

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "python",
      "args": ["/full/path/to/servicenow-mcp/mcp_adapter.py"],
      "env": {
        "SERVICENOW_DEV_INSTANCE_URL": "https://devXXX.service-now.com",
        "SERVICENOW_DEV_USERNAME": "your_username",
        "SERVICENOW_DEV_PASSWORD": "your_password"
      }
    }
  }
}
```

**Important:** Replace `/full/path/to/servicenow-mcp/` with the actual path where you cloned the repository.

### Find Your Full Path

To get the full path:
```bash
# Navigate to your servicenow-mcp directory
cd servicenow-mcp

# Get the full path
pwd

# Example output: /Users/yourname/projects/servicenow-mcp
```

Then use this path in your configuration:
```json
"args": ["/Users/yourname/projects/servicenow-mcp/mcp_adapter.py"]
```

## 🔄 Step 4: Restart Claude Desktop

1. **Quit Claude Desktop completely**
2. **Restart Claude Desktop**
3. **Wait for the MCP server to initialize** (may take 10-30 seconds)

## ✅ Step 5: Verify the Setup

### Test Basic Functionality

Open Claude Desktop and try these commands:

1. **Test connection:**
```
Can you check the health of my ServiceNow connection?
```

2. **Query incidents:**
```
Show me the latest 5 incidents from ServiceNow
```

3. **Get ServiceNow statistics:**
```
Give me statistics on incidents by state
```

### Expected Response

Claude should respond with ServiceNow data, indicating the MCP server is working correctly.

## 🎯 Step 6: Start Using ServiceNow MCP

### Basic Operations

#### Create an Incident
```
Create a new incident with:
- Short description: "Server outage in production"
- Description: "Web servers are not responding"
- Urgency: High
- Impact: High
```

#### Query Records
```
Find all high-priority incidents that are still open
```

#### Update Records
```
Update incident INC0000123 to set the state to "In Progress" and add a work note
```

### Advanced Features

#### Story-Driven Development
```
I have a user story: "As a service desk agent, I want to automatically assign incidents based on category so that tickets are routed to the right team faster"

Can you analyze this story and create an implementation plan?
```

#### CMDB Analysis
```
Analyze my CMDB for duplicate servers and provide recommendations for cleanup
```

#### Root Cause Analysis
```
Users are reporting slow form loading times. Can you perform a root cause analysis for the last 24 hours?
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. "MCP server not found" Error

**Problem:** Claude can't find the MCP server
**Solution:**
- Verify the full path in your configuration
- Ensure Python is in your PATH
- Check that the virtual environment is activated

#### 2. "ServiceNow connection failed" Error

**Problem:** Can't connect to ServiceNow
**Solution:**
- Verify your ServiceNow URL, username, and password
- Check if your ServiceNow instance is accessible
- Ensure your user has the required permissions

#### 3. "Permission denied" Error

**Problem:** Insufficient ServiceNow permissions
**Solution:**
- Contact your ServiceNow administrator
- Ensure your user has these minimum roles:
  - `rest_service`
  - `web_service_admin`
  - `itil` (for ITSM operations)

#### 4. MCP Server Won't Start

**Problem:** Server fails to initialize
**Solution:**
```bash
# Check for errors
python mcp_adapter.py

# Check dependencies
pip install -r requirements.txt

# Verify configuration
python -c "from servicenow_mcp.config import Config; print(Config.for_env('dev'))"
```

### Debug Mode

Enable debug logging for troubleshooting:

1. **Add to your `.env` file:**
```bash
MCP_LOG_LEVEL=DEBUG
```

2. **Check logs:**
```bash
# View real-time logs
tail -f logs/servicenow-mcp.log
```

## 🔒 Security Best Practices

### Environment Variables
- Never commit `.env` files to version control
- Use strong passwords and rotate them regularly
- Consider using ServiceNow OAuth for production

### Table Access Control
```bash
# Restrict table access during testing
MCP_ALLOW_TABLES=incident,problem,change_request,sys_script,sys_script_include

# Block sensitive tables
MCP_BLOCKED_TABLES=sys_user_password,oauth_entity
```

### Network Security
- Use HTTPS for all ServiceNow connections
- Consider VPN for production access
- Implement IP whitelisting where possible

## 📚 Usage Examples

### Example Conversation Flow

**You:** "Show me all critical incidents from the last week"

**Claude:** "I'll query your ServiceNow instance for critical incidents from the last week."

*[Claude uses the query_table tool to fetch incidents]*

**Claude:** "Here are the critical incidents from the last 7 days:
1. INC0000123 - Database server outage (Created: 2024-01-10)
2. INC0000124 - Network connectivity issues (Created: 2024-01-12)
..."

**You:** "Create a change request to address the database server issue"

**Claude:** "I'll create a change request for the database server outage. Let me gather the necessary information and create the change record."

*[Claude uses create_change_request tool]*

### Advanced Workflow Example

**You:** "I need to implement automatic incident assignment based on category. Can you help me build this?"

**Claude:** "I'll help you implement automatic incident assignment. Let me analyze this as a user story and create a complete implementation plan."

*[Claude uses story_to_implementation tool]*

**Claude:** "I've analyzed your requirement and created a comprehensive implementation plan:

**Story Analysis:**
- User: Service Desk Agent
- Goal: Automatic incident assignment based on category
- Benefit: Faster ticket routing

**Implementation Plan:**
1. Create business rule on incident table
2. Add assignment logic based on category mapping
3. Create assignment group mapping table
4. Test the automation

Would you like me to proceed with implementing these components?"

## 🎓 Learning Resources

### ServiceNow MCP Documentation
- [API Reference](api-reference.md) - Complete tool documentation
- [Configuration Guide](configuration.md) - Advanced setup options
- [Examples](../examples/) - Real-world usage scenarios

### ServiceNow Resources
- [ServiceNow Developer Portal](https://developer.servicenow.com/)
- [ServiceNow REST API Documentation](https://docs.servicenow.com/bundle/vancouver-application-development/page/integrate/inbound-rest/concept/c_RESTAPI.html)
- [ServiceNow Community](https://community.servicenow.com/)

## 🆘 Getting Help

### Community Support
- **GitHub Issues**: [Report bugs or request features](https://github.com/mady22070/servicenow-mcp/issues)
- **GitHub Discussions**: [Community support and questions](https://github.com/mady22070/servicenow-mcp/discussions)
- **ServiceNow Community**: General ServiceNow questions

### Professional Support
- ServiceNow support for platform issues
- Consult ServiceNow partners for implementation help
- Consider ServiceNow training and certification

---

## 🎉 You're Ready!

Your ServiceNow MCP server is now configured and ready to use with Claude Desktop. You can now:

- ✅ Query ServiceNow data through natural language
- ✅ Create and update records conversationally
- ✅ Perform advanced analysis and troubleshooting
- ✅ Implement story-driven development workflows
- ✅ Automate complex ServiceNow operations

Start with simple queries and gradually explore the advanced features. The AI will guide you through complex operations and help you discover new capabilities!

**Happy automating!** 🚀