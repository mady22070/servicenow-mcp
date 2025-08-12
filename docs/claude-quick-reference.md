# Claude Desktop Quick Reference

Quick reference for using ServiceNow MCP with Claude Desktop.

## 🚀 Getting Started Commands

### Test Your Setup
```
Check the health of my ServiceNow connection
```

### Basic Information
```
What ServiceNow tools are available?
Show me my active environments
List all available workspaces
```

## 📊 Querying Data

### Incidents
```
Show me the latest 10 incidents
Find all critical incidents that are still open
Get incident INC0000123 details
Show incidents created in the last 24 hours
```

### Problems
```
List all open problems
Show problem PRB0000456 with related incidents
Find problems created this week
```

### Change Requests
```
Show all pending change requests
Find emergency changes from last month
Get change CHG0000789 approval status
```

### Users and Groups
```
Find user by email: john.doe@company.com
Show all members of the "IT Support" group
List users with admin roles
```

## 🔧 Creating Records

### Create Incident
```
Create a new incident:
- Short description: "Email server down"
- Description: "Users cannot send or receive emails"
- Urgency: High
- Impact: High
- Category: Software
```

### Create Problem
```
Create a problem record for recurring database timeouts with:
- Short description: "Database performance issues"
- Impact: Medium
- Urgency: Medium
```

### Create Change Request
```
Create a change request for:
- Short description: "Upgrade database server"
- Type: Standard
- Risk: Medium
- Start date: 2024-01-20 02:00:00
- End date: 2024-01-20 06:00:00
```

## ✏️ Updating Records

### Update Incident
```
Update incident INC0000123:
- Set state to "In Progress"
- Add work note: "Investigating root cause"
- Assign to: john.doe
```

### Bulk Updates
```
Update all incidents with category "Hardware" to set priority to "High"
```

## 📈 Analytics and Reporting

### Statistics
```
Give me incident statistics by state
Show problem statistics by category
Analyze change request success rates
```

### Trends
```
Show incident trends for the last 30 days
Analyze problem resolution times by category
Compare this month's incidents to last month
```

## 🏗️ Development Operations

### Story-Driven Development
```
Analyze this user story: "As a service desk agent, I want to automatically escalate incidents after 4 hours so that critical issues don't get missed"

Create an implementation plan for automatic incident escalation
```

### Script Development
```
Create a business rule that automatically assigns incidents based on category
Generate a script include for calculating SLA breach times
Create a UI policy to hide fields based on incident category
```

### Application Building
```
Create a new custom table for tracking software licenses
Add fields to the incident table for tracking resolution codes
Build a catalog item for requesting new user accounts
```

## 🔍 Advanced Analysis

### CMDB Analysis
```
Analyze my CMDB for duplicate servers
Find configuration items without relationships
Check data quality for the cmdb_ci_server table
```

### Root Cause Analysis
```
Perform root cause analysis for "slow system performance" over the last 24 hours
Investigate why incidents are taking longer to resolve this month
Analyze the correlation between changes and incidents
```

### Performance Monitoring
```
Show me the top 10 slowest transactions from the last hour
Check for any scheduled jobs that are running long
Find any ECC queue backlogs
```

## 🔒 Security and Compliance

### Access Control
```
Check ACL permissions for the incident table
Show form visibility rules for the problem form
Test record access for user john.doe on incident INC0000123
```

### Audit and Compliance
```
Show audit trail for incident INC0000123
Find all changes made by user admin in the last week
Generate compliance report for change management
```

## 🛠️ Troubleshooting

### System Health
```
Check ServiceNow system health
Show any active alerts or events
Find recent error logs containing "timeout"
```

### User Issues
```
Troubleshoot why user jane.doe cannot see incident forms
Check why business rule "Auto Assignment" is not firing
Investigate slow form loading for the change request table
```

## 🔄 Workflow and Automation

### Flow Designer
```
Create a flow to automatically notify managers of critical incidents
Build a workflow for change request approvals
Design an automation for problem escalation
```

### Integration
```
Create a REST message for external system integration
Set up a data source for importing CI data
Configure event rules for alert correlation
```

## 📋 Workspace Management

### Workspace Operations
```
List all available workspaces
Switch to the "development" workspace
Set workspace environment to "test"
Configure workspace for dry-run mode
```

### Plan Execution
```
Execute this plan:
1. Create incident for server outage
2. Create problem record for investigation
3. Link incident to problem
4. Notify IT management
```

## 💡 Pro Tips

### Natural Language Queries
- Be specific about what you want
- Include relevant details like time ranges, categories, states
- Ask for explanations if you don't understand the results

### Batch Operations
```
Create 5 test incidents for training purposes
Update all incidents assigned to john.doe to set priority to "High"
Delete all test records created today
```

### Complex Workflows
```
I need to implement a complete incident management workflow:
1. Auto-assignment based on category
2. Escalation after 4 hours
3. Manager notification for critical incidents
4. Automatic problem creation for recurring incidents

Can you help me design and implement this?
```

### Data Analysis
```
Analyze our incident data to identify:
- Most common incident categories
- Average resolution times by priority
- Peak incident creation times
- Teams with highest workload
```

## 🎯 Best Practices

### Query Efficiently
- Use specific filters to limit results
- Ask for summaries of large datasets
- Request only the fields you need

### Safety First
- Use dry-run mode for testing: "Create this incident in dry-run mode"
- Test in development environment first
- Always verify before bulk operations

### Documentation
- Ask Claude to explain complex operations
- Request step-by-step guides for processes
- Get recommendations for best practices

---

## 🆘 Quick Help

### If Something Goes Wrong
```
Check the health of my ServiceNow connection
Show me any recent errors in the MCP server
Test my ServiceNow permissions
```

### Getting Information
```
What can you help me with in ServiceNow?
Show me examples of incident management operations
Explain how to use the story-driven development features
```

### Learning More
```
Teach me about ServiceNow business rules
Explain the difference between problems and incidents
Show me how to create effective user stories
```

Remember: Claude understands natural language, so feel free to ask questions in your own words. The AI will interpret your intent and use the appropriate ServiceNow MCP tools to help you accomplish your goals!