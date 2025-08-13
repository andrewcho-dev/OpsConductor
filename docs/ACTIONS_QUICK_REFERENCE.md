# Actions Workspace Quick Reference

## 🚀 Getting Started
1. **Jobs** → **Create New Job**
2. Enter name/description → Select targets → **Configure Actions**
3. Drag actions from palette → Configure parameters → Set conditions/dependencies
4. Review in **Settings** tab → **Save & Configure**

## 🎯 Action Types

| Icon | Type | Purpose | Key Parameters |
|------|------|---------|----------------|
| 🖥️ | **Command** | Execute shell commands | `command`, `workingDirectory`, `expectedExitCodes` |
| 📜 | **Script** | Run scripts (Bash, Python, etc.) | `scriptType`, `scriptContent`, `arguments` |
| 🌐 | **API** | HTTP REST API calls | `method`, `url`, `headers`, `body` |
| 🗄️ | **Database** | SQL queries & operations | `connectionString`, `queryType`, `query` |
| 📁 | **File** | File system operations | `operation`, `source`, `destination` |
| 📧 | **Email** | Send notifications | `to`, `subject`, `body` |
| 🔀 | **Condition** | Conditional logic | `conditionType`, `expression` |
| ⚡ | **Parallel** | Concurrent execution | `maxConcurrency`, `waitForAll` |

## 🔀 Conditional Logic

### Operators
- `==` Equal to
- `!=` Not equal to  
- `>` Greater than
- `<` Less than
- `contains` String contains
- `matches` Regex match

### Common Conditions
```
${PREVIOUS_ACTION_EXIT_CODE} == 0    # Previous action succeeded
${TARGET_OS} contains "linux"        # Linux targets only
${PREVIOUS_ACTION_OUTPUT} contains "success"  # Output check
```

## 🔗 Dependencies

### Status Types
- **success** - Action completed successfully
- **failure** - Action failed
- **completed** - Action finished (any status)
- **skipped** - Action was skipped

### Example
```json
{
  "dependencies": [
    {
      "actionId": "health-check",
      "status": "success"
    }
  ]
}
```

## 📝 System Variables

| Variable | Description |
|----------|-------------|
| `${JOB_NAME}` | Current job name |
| `${EXECUTION_ID}` | Unique execution ID |
| `${TARGET_HOST}` | Target hostname |
| `${TARGET_OS}` | Target OS |
| `${EXECUTION_TIME}` | Start time |
| `${PREVIOUS_ACTION_EXIT_CODE}` | Previous exit code |
| `${PREVIOUS_ACTION_OUTPUT}` | Previous output |

## ⚙️ Common Settings

### Execution Modes
- **Sequential** - One after another
- **Parallel** - Concurrent where possible
- **Batch** - Group similar actions

### Error Handling
- **Stop Workflow** - Halt on first error
- **Continue** - Keep going on errors
- **Skip Remaining** - Skip rest of workflow
- **Rollback** - Execute rollback actions

### Log Levels
- **Debug** - Verbose logging
- **Info** - Standard logging
- **Warning** - Errors only
- **Error** - Critical only

## 🎨 UI Tips

### Workspace Navigation
- **Left Panel** - Action palette
- **Center Panel** - Workflow designer
- **Right Panel** - Configuration

### Keyboard Shortcuts
- **Drag & Drop** - Reorder actions
- **Click Action** - Configure parameters
- **Tab Navigation** - Workflow → Variables → Settings

### Visual Indicators
- 🔴 **Red** - Unconfigured/Error
- 🟡 **Yellow** - Warning/Conditional
- 🟢 **Green** - Configured/Success
- 🔵 **Blue** - Dependencies/Info

## 📋 Workflow Examples

### Simple Health Check
```
1. Command: "systemctl status nginx"
2. Email: Send status to ops team
```

### Deployment Pipeline
```
1. Command: Pre-deployment health check
   ↓ (if success)
2. Script: Deploy application
   ↓ (if success)
3. Command: Post-deployment verification
   ↓ (if success)
4. Email: Success notification
   ↓ (if failure at any step)
5. Script: Rollback deployment
```

### Parallel Monitoring
```
1. Parallel: System checks
   ├─ Command: Check disk space
   ├─ Command: Check memory usage
   └─ Command: Check CPU load
   ↓ (wait for all)
2. API: Send metrics to monitoring
3. Email: Send report (if any issues)
```

## 🔧 Troubleshooting

### Common Issues
- **Action not executing** → Check conditions & dependencies
- **Variables not substituting** → Verify syntax: `${VARIABLE_NAME}`
- **Circular dependencies** → Use workflow validation
- **Timeout errors** → Increase timeout values

### Validation Checks
- ✅ All actions configured
- ✅ No circular dependencies
- ✅ Valid variable references
- ✅ Reachable action dependencies

## 🚀 Best Practices

### Design
1. **Start simple** - Begin with basic workflows
2. **Use descriptive names** - Clear action names
3. **Add documentation** - Use descriptions
4. **Test incrementally** - Test on dev first

### Performance
1. **Use parallel execution** - For independent actions
2. **Set appropriate timeouts** - Prevent hanging
3. **Optimize commands** - Efficient scripts
4. **Limit concurrency** - Don't overwhelm targets

### Security
1. **Use variables** - Don't hardcode secrets
2. **Validate inputs** - Check variable values
3. **Limit permissions** - Least privilege
4. **Audit workflows** - Review for security

---

*For detailed information, see the [Actions Workspace Guide](ACTIONS_WORKSPACE_GUIDE.md)*