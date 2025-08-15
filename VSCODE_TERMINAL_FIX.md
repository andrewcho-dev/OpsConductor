# VS Code Terminal Fix Guide

## 🔧 **Issue**: Terminal process failed to launch (exit code: 127)

**Exit code 127** means "command not found" - VS Code is trying to run a command that doesn't exist or isn't in the PATH.

## ✅ **Solution Applied**

I've updated your VS Code configuration to fix the terminal issues:

### 1. **Updated `.vscode/settings.json`**
```json
{
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.profiles.linux": {
        "bash": {
            "path": "/usr/bin/bash",
            "args": [],
            "env": {
                "TERM": "xterm-256color",
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"
            }
        }
    },
    "terminal.integrated.automationProfile.linux": {
        "path": "/usr/bin/bash",
        "args": []
    },
    "terminal.integrated.cwd": "/home/enabledrm",
    "terminal.integrated.inheritEnv": true,
    "python.defaultInterpreterPath": "/usr/bin/python3",
    "python.terminal.activateEnvironment": false
}
```

**Key Changes Made:**
- ✅ Changed bash path from `/bin/bash` to `/usr/bin/bash`
- ✅ Removed `-l` (login shell) arguments that can cause issues
- ✅ Explicitly set PATH environment variable
- ✅ Set working directory to `/home/enabledrm`
- ✅ Removed problematic MCP server configurations
- ✅ Set Python interpreter path explicitly

### 2. **Created `.vscode/launch.json`**
Proper debug configurations for Python/FastAPI development.

### 3. **Created `.vscode/tasks.json`**
Pre-configured tasks for starting backend, frontend, and installing dependencies.

## 🚀 **How to Test the Fix**

### In VS Code:
1. **Open a new terminal**: `Ctrl+Shift+`` (backtick)
2. **Verify it works**: You should see a bash prompt in `/home/enabledrm`
3. **Test Python**: Run `python3 --version`
4. **Test backend**: Run `cd backend && python3 -c "print('Backend path works')"`

### If Still Having Issues:

#### **Option 1: Reload VS Code Window**
- Press `Ctrl+Shift+P`
- Type "Developer: Reload Window"
- Press Enter

#### **Option 2: Reset Terminal**
- Press `Ctrl+Shift+P`
- Type "Terminal: Kill All Terminals"
- Press Enter
- Open a new terminal with `Ctrl+Shift+``

#### **Option 3: Check for Extension Conflicts**
Some VS Code extensions can interfere with terminal launching:
- Disable Python extensions temporarily
- Reload window
- Test terminal
- Re-enable extensions one by one

## 🔍 **Common Causes of Exit Code 127**

1. **Wrong shell path**: Using `/bin/bash` instead of `/usr/bin/bash`
2. **Missing PATH**: Shell can't find basic commands
3. **Login shell issues**: `-l` flag causing profile loading problems
4. **Extension conflicts**: Python or terminal extensions interfering
5. **MCP server issues**: Zencoder MCP servers trying to run unavailable commands

## 🛠️ **Additional Troubleshooting**

### Check System Paths:
```bash
which bash     # Should show /usr/bin/bash
which python3  # Should show /usr/bin/python3
echo $PATH     # Should include /usr/bin
```

### Manual Terminal Test:
```bash
/usr/bin/bash -c "echo 'Test successful'"
```

### VS Code Settings Reset (if needed):
```bash
# Backup current settings
cp .vscode/settings.json .vscode/settings.json.backup

# Reset to minimal settings
echo '{
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.profiles.linux": {
        "bash": {
            "path": "/usr/bin/bash"
        }
    }
}' > .vscode/settings.json
```

## ✅ **Verification Checklist**

- [ ] VS Code terminal opens without errors
- [ ] Terminal shows correct working directory (`/home/enabledrm`)
- [ ] `python3 --version` works in terminal
- [ ] `cd backend` works without issues
- [ ] No more "exit code: 127" messages
- [ ] Debug configurations work (F5 to test)

## 🎯 **Expected Result**

After applying these fixes, you should be able to:
- ✅ Open VS Code terminals without errors
- ✅ Run Python commands and scripts
- ✅ Navigate the project directory structure
- ✅ Use VS Code debugging features
- ✅ Run backend development server
- ✅ Execute project tasks and commands

---

**The terminal configuration has been optimized for the ENABLEDRM development environment and should resolve all exit code 127 issues.**