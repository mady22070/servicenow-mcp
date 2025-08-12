# Claude Desktop Examples

Real-world examples of using ServiceNow MCP with Claude Desktop.

## 🎯 Basic Operations

### Example 1: Incident Management

**You:** "Show me all critical incidents that are currently open"

**Claude:** "I'll query your ServiceNow instance for open critical incidents."

*[Uses query_table tool]*

**Claude Response:**
```
Here are the open critical incidents:

1. **INC0000123** - Database server outage
   - State: In Progress
   - Assigned to: John Smith
   - Created: 2024-01-15 09:30:00
   - Priority: 1 - Critical

2. **INC0000124** - Network connectivity issues
   - State: New
   - Assigned to: Unassigned
   - Created: 2024-01-15 14:20:00
   - Priority: 1 - Critical

Would you like me to help you with any of these incidents?
```

**You:** "Assign the network incident to Jane Doe and add a work note saying we're investigating"

**Claude:** "I'll assign INC0000124 to Jane Doe and add the work note."

*[Uses update_record tool]*

**Claude Response:**
```
✅ Successfully updated INC0000124:
- Assigned to: Jane Doe
- Added work note: "Investigating network connectivity issues"
- State remains: New

The incident is now assigned and Jane will be notified of the assignment.
```

### Example 2: Creating Records

**You:** "Create a new incident for email server issues. Users can't send emails since 2 PM today. This is affecting the entire sales team."

**Claude:** "I'll create a high-priority incident for the email server issues affecting the sales team."

*[Uses create_incident tool]*

**Claude Response:**
```
✅ Created new incident: **INC0000125**

Details:
- Short Description: Email server issues - users cannot send emails
- Description: Users unable to send emails since 2 PM today, affecting entire sales team
- Priority: 2 - High (High Impact, Medium Urgency)
- Category: Software
- Subcategory: Email
- State: New
- Created: 2024-01-15 16:45:00

The incident has been created and is ready for assignment. Would you like me to:
1. Assign it to a specific team or person?
2. Create a related problem record for investigation?
3. Notify management about this business-impacting issue?
```

## 🏗️ Advanced Development Workflows

### Example 3: Story-Driven Development

**You:** "I have a user story: 'As a service desk manager, I want to automatically escalate incidents that haven't been touched in 4 hours so that nothing falls through the cracks.' Can you help me implement this?"

**Claude:** "I'll analyze your user story and create a complete implementation plan for automatic incident escalation."

*[Uses story_to_implementation tool]*

**Claude Response:**
```
## Story Analysis ✅

**Parsed Story:**
- **User:** Service desk manager
- **Goal:** Automatically escalate incidents that haven't been touched in 4 hours
- **Benefit:** Prevent incidents from falling through the cracks

**Validation:** ✅ Complete story with clear user, goal, and benefit

## Technical Requirements

**Identified Requirements:**
1. **Business Rule:** Scheduled script execution to check incident activity
2. **SLA Definition:** 4-hour response time tracking
3. **Escalation Logic:** Automatic assignment to manager or senior team
4. **Notification System:** Alert relevant stakeholders
5. **Audit Trail:** Log all escalation actions

## Implementation Plan

### Phase 1: Core Infrastructure (2-3 hours)
1. **Create SLA Definition**
   - Response time: 4 hours
   - Escalation conditions: No updates or assignments

2. **Create Business Rule: "Auto Escalation Check"**
   - Table: Incident
   - When: Scheduled (every 30 minutes)
   - Condition: State not in [Resolved, Closed, Cancelled]

### Phase 2: Escalation Logic (2-3 hours)
3. **Create Script Include: "IncidentEscalationUtils"**
   - Function: checkForEscalation()
   - Function: escalateIncident()
   - Function: notifyStakeholders()

4. **Create Assignment Rules**
   - Escalate to assignment group manager
   - If no manager, escalate to IT director

### Phase 3: Notifications (1-2 hours)
5. **Create Email Templates**
   - Manager escalation notification
   - Original assignee notification

6. **Create Event Rules**
   - Trigger notifications on escalation
   - Log escalation events

Would you like me to proceed with implementing these components? I can:
1. Start with Phase 1 (SLA and Business Rule)
2. Show you the exact code for each component
3. Create everything in dry-run mode first for testing
```

**You:** "Yes, let's start with Phase 1. Create the SLA definition and business rule."

**Claude:** "I'll create the SLA definition and business rule for incident escalation."

*[Uses multiple tools: create_sla_definition, create_business_rule]*

### Example 4: CMDB Analysis

**You:** "Our CMDB seems messy. Can you analyze it for duplicates and data quality issues?"

**Claude:** "I'll perform a comprehensive CMDB analysis to identify duplicates and data quality issues."

*[Uses troubleshoot_cmdb_duplicates and investigate_data_quality tools]*

**Claude Response:**
```
## CMDB Analysis Results 📊

### Duplicate Analysis
**Found 23 potential duplicates with high confidence:**

**High Confidence Duplicates (15):**
1. **server01.company.com** vs **server01**
   - Same IP: 192.168.1.10
   - Same Serial: SN123456
   - Confidence: 95%

2. **LAPTOP-ABC123** vs **laptop-abc123**
   - Same Serial: LP789012
   - Same User: john.doe
   - Confidence: 92%

**Medium Confidence Duplicates (8):**
- Similar names with different cases
- Matching serial numbers but different models

### Data Quality Issues

**Missing Critical Data:**
- 45% of servers missing IP addresses
- 32% of workstations missing assigned users
- 28% of network devices missing location

**Inconsistent Data:**
- 12 different naming conventions for servers
- Mixed case usage across all CI types
- Inconsistent location formats

### Recommendations

**Immediate Actions:**
1. **Merge High-Confidence Duplicates** (Est. 2-3 hours)
   - Review and merge the 15 high-confidence duplicates
   - Preserve relationships and history

2. **Data Cleanup** (Est. 4-6 hours)
   - Standardize naming conventions
   - Fill missing IP addresses from discovery
   - Update assigned users from AD sync

3. **Process Improvements** (Est. 1-2 days)
   - Implement duplicate prevention rules
   - Create data validation business rules
   - Set up automated data quality monitoring

Would you like me to:
1. Start merging the high-confidence duplicates?
2. Create business rules to prevent future duplicates?
3. Generate a detailed cleanup plan with scripts?
```

## 🔍 Troubleshooting Scenarios

### Example 5: Root Cause Analysis

**You:** "Users are complaining about slow performance today. Can you help me investigate what might be causing this?"

**Claude:** "I'll perform a root cause analysis to investigate the performance issues."

*[Uses root_cause_analysis tool]*

**Claude Response:**
```
## Root Cause Analysis: Slow Performance 🔍

### Investigation Summary
**Time Range:** Last 24 hours
**Issue:** System performance degradation

### Findings

**1. System Metrics**
- **Database Response Time:** 3.2s average (normal: 0.8s)
- **Active Sessions:** 245 (normal: 120-150)
- **Memory Usage:** 89% (normal: 65-75%)

**2. Recent Changes**
Found 3 changes deployed in the last 24 hours:
- **CHG0001234:** Database index rebuild (Completed 2024-01-15 02:00)
- **CHG0001235:** New business rule deployment (Completed 2024-01-15 08:30)
- **CHG0001236:** Scheduled job modification (Completed 2024-01-15 10:15)

**3. Error Patterns**
- 47 timeout errors since 08:30 AM
- 23 "slow query" warnings
- 15 memory allocation failures

**4. Correlation Analysis**
⚠️ **Strong correlation found:**
- Performance issues started at 08:35 AM
- CHG0001235 (business rule) deployed at 08:30 AM
- Business rule affects incident table (high-volume table)

### Root Cause Assessment

**Primary Suspect:** CHG0001235 - New business rule
- **Evidence:** Timing correlation with performance degradation
- **Impact:** Rule executes on every incident update (high frequency)
- **Risk:** Inefficient database queries in rule logic

**Secondary Factors:**
- High user activity during business hours
- Database index rebuild may have affected query plans

### Recommended Actions

**Immediate (Next 30 minutes):**
1. **Disable the new business rule** temporarily
2. **Monitor system performance** for improvement
3. **Review business rule code** for optimization opportunities

**Short-term (Next 2-4 hours):**
1. **Optimize business rule queries** (add proper indexing)
2. **Test in development environment**
3. **Implement performance monitoring** for the rule

**Long-term (Next week):**
1. **Implement change impact analysis** process
2. **Add performance testing** to deployment pipeline
3. **Create performance baselines** for critical components

Would you like me to:
1. Disable the business rule temporarily?
2. Show you the business rule code for review?
3. Create a performance monitoring plan?
```

## 🎓 Learning and Discovery

### Example 6: Exploring Capabilities

**You:** "I'm new to ServiceNow automation. What can you help me with?"

**Claude Response:**
```
# Welcome to ServiceNow MCP! 🚀

I can help you with a wide range of ServiceNow operations and automation. Here's what I can do:

## 📋 Basic Operations
- **Query and search** records across all tables
- **Create, update, and delete** records
- **Manage incidents, problems, and changes**
- **Handle user and group management**
- **Work with attachments and knowledge articles**

## 🏗️ Development & Automation
- **Story-driven development** - Turn user stories into working code
- **Create business rules, script includes, and UI policies**
- **Build applications and custom tables**
- **Design workflows and flows**
- **Set up integrations and REST APIs**

## 🔍 Analysis & Troubleshooting
- **CMDB analysis** - Find duplicates, analyze relationships
- **Root cause analysis** - Investigate system issues
- **Performance monitoring** - Check system health
- **Data quality assessment** - Identify and fix data issues

## 🎯 Advanced Features
- **Multi-environment support** (dev/test/prod)
- **Bulk operations** with safety controls
- **Plan execution** for complex multi-step tasks
- **Security analysis** - ACL and permission checking

## 💡 Getting Started Tips

**Try these commands:**
- "Show me the latest 5 incidents"
- "Create a test incident for learning"
- "Explain how ServiceNow business rules work"
- "Help me analyze this user story: [your story]"

**Best Practices:**
- Start with simple queries to get familiar
- Use dry-run mode for testing: "Create this in dry-run mode"
- Ask for explanations: "Explain what this business rule does"
- Request step-by-step guides: "Show me how to create a workflow"

What would you like to explore first?
```

### Example 7: Learning ServiceNow Concepts

**You:** "Can you explain the difference between incidents and problems in ServiceNow?"

**Claude Response:**
```
# Incidents vs Problems in ServiceNow 📚

## 🚨 Incidents
**Definition:** An unplanned interruption or reduction in quality of an IT service.

**Characteristics:**
- **Reactive** - Response to something that's already broken
- **Immediate focus** - Restore service as quickly as possible
- **User-reported** - Usually reported by end users
- **Symptom-focused** - Addresses what users are experiencing

**Examples:**
- "I can't log into my email"
- "The website is loading slowly"
- "My computer won't start"

**Lifecycle:**
New → In Progress → Resolved → Closed

## 🔍 Problems
**Definition:** The underlying cause of one or more incidents.

**Characteristics:**
- **Proactive** - Investigation to prevent future incidents
- **Root cause focus** - Find and fix the underlying issue
- **IT-initiated** - Usually created by IT teams
- **Cause-focused** - Addresses why incidents are happening

**Examples:**
- "Faulty network switch causing connectivity issues"
- "Memory leak in application causing crashes"
- "Outdated driver causing printer failures"

**Lifecycle:**
New → In Progress → Root Cause Analysis → Resolved → Closed

## 🔗 Relationship

**One Problem → Multiple Incidents**
```
Problem: Database server hardware failure
├── Incident 1: Users can't access CRM system
├── Incident 2: Reports are not generating
├── Incident 3: Email integration is down
└── Incident 4: Mobile app won't sync
```

## 📊 Practical Example

Let me show you how this works in practice:

**Scenario:** Multiple users report they can't access the company intranet.

**Step 1: Create Incidents**
- INC001: "Can't access intranet" (User A)
- INC002: "Intranet site won't load" (User B)
- INC003: "Getting timeout errors on intranet" (User C)

**Step 2: Identify Pattern**
IT notices multiple similar incidents and creates:
- PRB001: "Intranet server connectivity issues"

**Step 3: Link Records**
All incidents are linked to the problem for tracking.

**Step 4: Resolution**
- **Incidents:** Provide workarounds, communicate status
- **Problem:** Investigate root cause, implement permanent fix

Would you like me to show you how to:
1. Create and link incidents to problems?
2. Set up automatic problem creation for recurring incidents?
3. Generate reports on incident-to-problem relationships?
```

## 🎉 Success Stories

### Example 8: Complete Workflow Implementation

**You:** "I successfully implemented the automatic incident escalation using your guidance. Now I want to add automatic problem creation when we have 3 or more similar incidents. Can you help?"

**Claude:** "Excellent work on the escalation! Now let's implement automatic problem creation for recurring incidents. This is a great next step in your ITSM maturity."

*[Uses story analysis and implementation tools]*

**Claude Response:**
```
# Automatic Problem Creation Implementation 🎯

## Current State Analysis ✅
You already have:
- ✅ Incident escalation (4-hour rule)
- ✅ SLA monitoring
- ✅ Notification system

## New Requirement Analysis
**Goal:** Create problems automatically when 3+ similar incidents occur
**Benefit:** Proactive problem management, reduce recurring incidents

## Implementation Strategy

### Phase 1: Similarity Detection (3-4 hours)
1. **Create Script Include: "IncidentSimilarityAnalyzer"**
   ```javascript
   // Analyze incidents for similarity based on:
   // - Category and subcategory
   // - Short description keywords
   // - Affected CIs
   // - Time proximity (within 24-48 hours)
   ```

2. **Create Business Rule: "Check for Similar Incidents"**
   - **When:** After insert/update on Incident
   - **Condition:** State = New or In Progress
   - **Action:** Check for similar incidents

### Phase 2: Problem Creation Logic (2-3 hours)
3. **Create Script Include: "AutoProblemCreator"**
   ```javascript
   // Functions:
   // - findSimilarIncidents()
   // - createProblemFromIncidents()
   // - linkIncidentsToProblem()
   ```

4. **Create Business Rule: "Auto Create Problem"**
   - **Trigger:** When 3+ similar incidents found
   - **Action:** Create problem and link incidents

### Phase 3: Intelligence & Refinement (2-3 hours)
5. **Add Machine Learning Elements**
   - Keyword analysis for description similarity
   - CI relationship analysis
   - Historical pattern recognition

6. **Create Configuration Table**
   - Similarity thresholds by category
   - Auto-creation rules by priority
   - Exclusion patterns

## Sample Implementation

Let me create the core similarity analyzer:

**Script Include: IncidentSimilarityAnalyzer**
```javascript
var IncidentSimilarityAnalyzer = Class.create();
IncidentSimilarityAnalyzer.prototype = {
    initialize: function() {
        this.similarityThreshold = 0.7; // 70% similarity
        this.timeWindow = 48; // 48 hours
    },
    
    findSimilarIncidents: function(incident) {
        var similar = [];
        var gr = new GlideRecord('incident');
        
        // Time window filter
        var timeAgo = new GlideDateTime();
        timeAgo.addHours(-this.timeWindow);
        gr.addQuery('sys_created_on', '>=', timeAgo);
        
        // Category match
        gr.addQuery('category', incident.category);
        gr.addQuery('sys_id', '!=', incident.sys_id);
        gr.addQuery('state', 'NOT IN', '6,7,8'); // Not resolved/closed
        
        gr.query();
        
        while (gr.next()) {
            var similarity = this.calculateSimilarity(incident, gr);
            if (similarity >= this.similarityThreshold) {
                similar.push({
                    incident: gr.getUniqueValue(),
                    similarity: similarity
                });
            }
        }
        
        return similar;
    },
    
    calculateSimilarity: function(inc1, inc2) {
        var score = 0;
        var factors = 0;
        
        // Category match (30% weight)
        if (inc1.category == inc2.category) score += 0.3;
        factors++;
        
        // Subcategory match (20% weight)
        if (inc1.subcategory == inc2.subcategory) score += 0.2;
        factors++;
        
        // Description similarity (40% weight)
        var descSimilarity = this.compareDescriptions(
            inc1.short_description, 
            inc2.short_description
        );
        score += (descSimilarity * 0.4);
        factors++;
        
        // CI match (10% weight)
        if (inc1.cmdb_ci == inc2.cmdb_ci && inc1.cmdb_ci != '') {
            score += 0.1;
        }
        factors++;
        
        return score;
    },
    
    type: 'IncidentSimilarityAnalyzer'
};
```

Would you like me to:
1. **Implement this solution step by step?**
2. **Create it in dry-run mode first for testing?**
3. **Show you how to configure the similarity thresholds?**
4. **Add reporting to track auto-created problems?**

This will complete your intelligent incident management system! 🚀
```

---

These examples show the natural, conversational way you can work with ServiceNow through Claude Desktop. The AI understands context, provides detailed explanations, and guides you through complex implementations step by step.

**Key Benefits:**
- 💬 **Natural Language Interface** - No need to remember complex syntax
- 🧠 **Intelligent Guidance** - AI provides context and recommendations
- 🔄 **Iterative Development** - Build solutions step by step
- 📚 **Learning Support** - Explanations and best practices included
- ⚡ **Rapid Implementation** - From idea to working solution quickly

Start with simple queries and gradually explore more advanced features as you become comfortable with the system!