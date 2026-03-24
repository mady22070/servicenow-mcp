# ServiceNow Background Script Execution Guide

## Overview

The ServiceNow MCP server now provides comprehensive background script execution capabilities, allowing you to safely run ServiceNow background scripts with built-in validation, templates, and monitoring.

## 🔒 **Safety First**

All script execution includes comprehensive safety validation:
- **Dangerous pattern detection** (infinite loops, bulk deletes)
- **Performance analysis** (unbounded queries, nested loops)
- **Security validation** (proper access controls, user context)
- **Syntax checking** (JavaScript validation, ServiceNow patterns)

## 🛠 **Available Tools**

### Core Execution
- `execute_background_script()` - Execute scripts with safety validation
- `validate_script_safety()` - Pre-validate scripts before execution
- `validate_script_syntax()` - Check JavaScript syntax

### Templates and Analysis
- `get_script_templates()` - Get common script templates
- `analyze_script_performance()` - Analyze performance implications
- `get_script_execution_history()` - View execution history

## 📝 **Script Templates**

### Data Cleanup Template
```javascript
// Clean up old records based on criteria
var tableName = 'your_table_name';
var daysOld = 90;
var maxRecords = 1000;

var cutoffDate = new GlideDateTime();
cutoffDate.addDaysLocalTime(-daysOld);

var gr = new GlideRecordSecure(tableName);
gr.addQuery('sys_created_on', '<', cutoffDate);
gr.addQuery('state', 'closed');
gr.setLimit(maxRecords);
gr.query();

var count = 0;
while (gr.next()) {
    // Add your cleanup logic here
    count++;
}

gs.info('Processed ' + count + ' records for cleanup');
```

### Data Migration Template
```javascript
// Migrate data between tables
var sourceTable = 'source_table';
var targetTable = 'target_table';
var batchSize = 100;

var sourceGr = new GlideRecordSecure(sourceTable);
sourceGr.addQuery('migrated', false);
sourceGr.setLimit(batchSize);
sourceGr.query();

var migrated = 0;
while (sourceGr.next()) {
    try {
        var targetGr = new GlideRecordSecure(targetTable);
        targetGr.initialize();
        
        // Map fields from source to target
        targetGr.setValue('field1', sourceGr.getValue('field1'));
        targetGr.setValue('field2', sourceGr.getValue('field2'));
        
        var newSysId = targetGr.insert();
        if (newSysId) {
            sourceGr.setValue('migrated', true);
            sourceGr.setValue('migrated_to', newSysId);
            sourceGr.update();
            migrated++;
        }
    } catch (ex) {
        gs.error('Migration failed for record ' + sourceGr.getUniqueValue() + ': ' + ex.message);
    }
}

gs.info('Successfully migrated ' + migrated + ' records');
```

### Bulk Update Template
```javascript
// Update multiple records based on criteria
var tableName = 'your_table_name';
var batchSize = 500;

var gr = new GlideRecordSecure(tableName);
gr.addQuery('field_to_check', 'old_value');
gr.setLimit(batchSize);
gr.query();

var updated = 0;
while (gr.next()) {
    try {
        gr.setValue('field_to_update', 'new_value');
        gr.setValue('last_updated_by', 'background_script');
        gr.update();
        updated++;
    } catch (ex) {
        gs.error('Update failed for record ' + gr.getUniqueValue() + ': ' + ex.message);
    }
}

gs.info('Successfully updated ' + updated + ' records');
```

## 🚨 **Safety Features**

### Dangerous Pattern Detection
The system automatically detects and blocks:
- **Infinite loops**: `while(true)`, `for(;;)`
- **Bulk deletes**: `.deleteRecord()`, `.deleteMultiple()`
- **Long sleeps**: `gs.sleep(1000+)`
- **Sensitive table access**: Direct user/role table modifications

### Performance Warnings
Identifies potential performance issues:
- **Unbounded queries**: Missing `setLimit()`
- **Nested database operations**: Queries within loops
- **Large result sets**: Potential memory issues

### Security Validation
Ensures proper security practices:
- **Secure record access**: Recommends `GlideRecordSecure`
- **User context validation**: Proper authentication checks
- **Role-based access**: Appropriate permission checks

## 💡 **Usage Examples**

### Basic Script Execution
```
"Execute this background script to clean up old incidents:
var gr = new GlideRecordSecure('incident');
gr.addQuery('state', 7);
gr.addQuery('sys_created_on', '<', gs.daysAgoStart(90));
gr.setLimit(100);
gr.query();
while (gr.next()) {
    gs.info('Processing incident: ' + gr.number);
}"
```

### Get Script Templates
```
"Show me available background script templates"
```

### Validate Script Safety
```
"Check if this script is safe to run:
while (true) {
    gs.info('This runs forever');
}"
```

### Performance Analysis
```
"Analyze the performance of this script:
var gr = new GlideRecord('incident');
gr.query();
while (gr.next()) {
    var tasks = new GlideRecord('task');
    tasks.addQuery('parent', gr.sys_id);
    tasks.query();
}"
```

## ⚙️ **Execution Options**

### Safety Validation (Default: Enabled)
```javascript
// Safe execution with validation
execute_background_script(script, "Description", validate_safety=true)

// Skip validation (use with caution)
execute_background_script(script, "Description", validate_safety=false)

// Allow dangerous patterns (admin override)
execute_background_script(script, "Description", allow_dangerous=true)
```

### Dry Run Mode
```javascript
// Test script without execution
execute_background_script(script, "Description", dry_run=true)
```

## 📊 **Monitoring and History**

### Execution Tracking
Every script execution is tracked with:
- **Execution ID**: Unique identifier
- **Start/end timestamps**: Timing information
- **Safety analysis**: Risk assessment
- **Results**: Success/failure status
- **Performance metrics**: Execution time

### History Access
```
"Show me the last 10 background script executions"
```

## 🎯 **Best Practices**

### Script Development
1. **Start with templates** - Use provided templates as starting points
2. **Validate first** - Always check safety before execution
3. **Use dry run** - Test scripts without actual execution
4. **Add logging** - Include `gs.info()` for monitoring
5. **Handle errors** - Use try-catch blocks

### Performance Optimization
1. **Use setLimit()** - Always limit query results
2. **Use GlideRecordSecure** - Better security and performance
3. **Avoid nested queries** - Minimize database operations in loops
4. **Batch processing** - Process records in manageable chunks
5. **Monitor execution time** - Keep scripts under 60 seconds

### Security Guidelines
1. **Validate user context** - Check permissions before operations
2. **Use secure APIs** - Prefer GlideRecordSecure over GlideRecord
3. **Sanitize inputs** - Validate any external data
4. **Log activities** - Track what the script does
5. **Test in development** - Never run untested scripts in production

## 🔧 **Advanced Features**

### Custom Safety Rules
The system can be extended with custom safety patterns and validation rules.

### Integration with Other Packs
Background scripts can leverage:
- **Best practices validation** from the best practices pack
- **Scoped development** enforcement
- **Documentation lookup** for API guidance

### Execution Environment
Scripts run in the ServiceNow background script environment with:
- **Full API access** to ServiceNow APIs
- **System context** for administrative operations
- **Logging integration** with ServiceNow logs
- **Error handling** with proper exception management

## 🚀 **Getting Started**

1. **Get templates**: `"Show me background script templates"`
2. **Choose template**: Select appropriate template for your task
3. **Customize script**: Modify template for your specific needs
4. **Validate safety**: `"Check if this script is safe"`
5. **Test with dry run**: `"Execute this script in dry run mode"`
6. **Execute safely**: Run with full safety validation enabled

The background script execution capability makes the ServiceNow MCP server a powerful automation platform while maintaining safety and best practices!