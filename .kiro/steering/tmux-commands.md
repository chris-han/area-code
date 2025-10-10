---
inclusion: manual
---
# Cursor Agent Rules for Tmux Integration

## Command Execution Rules

### Primary Rule: Use Tmux Wrapper for All Commands
When executing terminal commands, ALWAYS use the tmux wrapper system to ensure commands run in the dedicated agent-tasks session:

**For regular commands:**
```bash
# Instead of: npm run build
# Use: ./tmux-agent-cmd.sh exec "npm run build"
```

**For background processes:**
```bash
# Instead of: npm run dev &
# Use: ./tmux-agent-cmd.sh bg "npm run dev"
```

**For complex tasks requiring dedicated workspace:**
```bash
# Instead of: npm test
# Use: ./tmux-agent-cmd.sh window "testing" "npm test"
```

### Command Translation Examples:

- `npm install` → `./tmux-agent-cmd.sh exec "npm install"`
- `npm run build` → `./tmux-agent-cmd.sh exec "npm run build"`
- `npm run dev` → `./tmux-agent-cmd.sh bg "npm run dev"`
- `npm test` → `./tmux-agent-cmd.sh window "testing" "npm test"`
- `docker-compose up -d` → `./tmux-agent-cmd.sh exec "docker-compose up -d"`
- `turbo build` → `./tmux-agent-cmd.sh exec "turbo build"`
- `pnpm install` → `./tmux-agent-cmd.sh exec "pnpm install"`

### Session Management:

Before running commands, check if the tmux environment is set up:
```bash
# Check if agent session exists
tmux has-session -t agent-tasks 2>/dev/null || ./tmux-dev-helper.sh setup
```

### Monitoring and Status:

Always inform the user how to monitor agent activities:
```bash
# Show agent status
./tmux-agent-cmd.sh status

# Attach to agent session
./tmux-dev-helper.sh agent
```

### Process Management:

When stopping processes or cleaning up:
```bash
# Kill agent processes
./tmux-agent-cmd.sh kill

# Or kill specific window
tmux kill-window -t agent-tasks:window-name
```

## Development Workflow Integration

### Project Structure Awareness:
This is a turborepo with:
- `apps/` - User-facing applications
- `services/` - Shared infrastructure and capabilities
- `packages/` - Shared functionality

### Service-Specific Commands:

For transactional service:
```bash
cd services/transactional-base
./tmux-agent-cmd.sh exec "npm run dev"
```

For analytical service (Moose):
```bash
cd services/analytical-base
./tmux-agent-cmd.sh exec "moose dev"
```

For sync service:
```bash
cd services/sync-base
./tmux-agent-cmd.sh exec "npm run dev"
```

### Build Commands:

For turbo commands:
```bash
./tmux-agent-cmd.sh exec "turbo build"
./tmux-agent-cmd.sh exec "turbo dev --filter=@workspace/vite-web-base"
```

### Long-Running Processes:

Always use background execution for servers and watchers:
```bash
./tmux-agent-cmd.sh bg "npm run dev"
./tmux-agent-cmd.sh bg "moose dev"
./tmux-agent-cmd.sh bg "docker-compose up"
```

### Testing Commands:

Create dedicated windows for testing:
```bash
./tmux-agent-cmd.sh window "testing" "npm test"
./tmux-agent-cmd.sh window "e2e-tests" "npm run test:e2e"
```

## Error Handling and Fallbacks

### If Tmux is Not Available:
The wrapper scripts include fallback mechanisms. If tmux is not installed or the session doesn't exist, commands will fall back to direct execution with appropriate warnings.

### Session Recovery:
If the agent session is lost or corrupted:
```bash
./tmux-dev-helper.sh restart
```

## User Communication

### Always Inform About Session Usage:
When running commands, inform the user:
- Which session the command is running in
- How to monitor the command
- How to attach to the session if needed

Example:
```
🤖 Executing in agent-tasks session: npm run build
💡 Monitor progress: tmux attach -t agent-tasks
```

### Provide Session Navigation:
Remind users about session switching:
```
Use Ctrl-a + a to switch to agent-tasks session
Use Ctrl-a + u to switch to your user-services session
```

## Special Cases

### Interactive Commands:
For commands that require user interaction, inform the user they need to attach to the session:
```bash
./tmux-agent-cmd.sh exec "npm init"
# Then inform user: "Please attach to agent session to complete interactive setup"
```

### File Operations:
File operations (reading, writing, editing) should still use the regular file tools, not the tmux wrapper. Only terminal commands should use the wrapper.

### IDE Operations:
Operations that open files in the IDE or manipulate the project structure directly should not use the tmux wrapper.

## Verification Commands

Before executing complex operations, verify the environment:
```bash
# Check tmux is available
command -v tmux >/dev/null 2>&1

# Check agent session exists
tmux has-session -t agent-tasks 2>/dev/null

# Check wrapper script exists
[ -f "./tmux-agent-cmd.sh" ] && [ -x "./tmux-agent-cmd.sh" ]
```

This ensures optimal development workflow separation and monitoring capabilities. # Cursor Agent Rules for Tmux Integration

## Command Execution Rules

### Primary Rule: Use Tmux Wrapper for All Commands
When executing terminal commands, ALWAYS use the tmux wrapper system to ensure commands run in the dedicated agent-tasks session:

**For regular commands:**
```bash
# Instead of: npm run build
# Use: ./tmux-agent-cmd.sh exec "npm run build"
```

**For background processes:**
```bash
# Instead of: npm run dev &
# Use: ./tmux-agent-cmd.sh bg "npm run dev"
```

**For complex tasks requiring dedicated workspace:**
```bash
# Instead of: npm test
# Use: ./tmux-agent-cmd.sh window "testing" "npm test"
```

### Command Translation Examples:

- `npm install` → `./tmux-agent-cmd.sh exec "npm install"`
- `npm run build` → `./tmux-agent-cmd.sh exec "npm run build"`
- `npm run dev` → `./tmux-agent-cmd.sh bg "npm run dev"`
- `npm test` → `./tmux-agent-cmd.sh window "testing" "npm test"`
- `docker-compose up -d` → `./tmux-agent-cmd.sh exec "docker-compose up -d"`
- `turbo build` → `./tmux-agent-cmd.sh exec "turbo build"`
- `pnpm install` → `./tmux-agent-cmd.sh exec "pnpm install"`

### Session Management:

Before running commands, check if the tmux environment is set up:
```bash
# Check if agent session exists
tmux has-session -t agent-tasks 2>/dev/null || ./tmux-dev-helper.sh setup
```

### Monitoring and Status:

Always inform the user how to monitor agent activities:
```bash
# Show agent status
./tmux-agent-cmd.sh status

# Attach to agent session
./tmux-dev-helper.sh agent
```

### Process Management:

When stopping processes or cleaning up:
```bash
# Kill agent processes
./tmux-agent-cmd.sh kill

# Or kill specific window
tmux kill-window -t agent-tasks:window-name
```

## Development Workflow Integration

### Project Structure Awareness:
This is a turborepo with:
- `apps/` - User-facing applications
- `services/` - Shared infrastructure and capabilities
- `packages/` - Shared functionality

### Service-Specific Commands:

For transactional service:
```bash
cd services/transactional-base
./tmux-agent-cmd.sh exec "npm run dev"
```

For analytical service (Moose):
```bash
cd services/analytical-base
./tmux-agent-cmd.sh exec "moose dev"
```

For sync service:
```bash
cd services/sync-base
./tmux-agent-cmd.sh exec "npm run dev"
```

### Build Commands:

For turbo commands:
```bash
./tmux-agent-cmd.sh exec "turbo build"
./tmux-agent-cmd.sh exec "turbo dev --filter=@workspace/vite-web-base"
```

### Long-Running Processes:

Always use background execution for servers and watchers:
```bash
./tmux-agent-cmd.sh bg "npm run dev"
./tmux-agent-cmd.sh bg "moose dev"
./tmux-agent-cmd.sh bg "docker-compose up"
```

### Testing Commands:

Create dedicated windows for testing:
```bash
./tmux-agent-cmd.sh window "testing" "npm test"
./tmux-agent-cmd.sh window "e2e-tests" "npm run test:e2e"
```

## Error Handling and Fallbacks

### If Tmux is Not Available:
The wrapper scripts include fallback mechanisms. If tmux is not installed or the session doesn't exist, commands will fall back to direct execution with appropriate warnings.

### Session Recovery:
If the agent session is lost or corrupted:
```bash
./tmux-dev-helper.sh restart
```

## User Communication

### Always Inform About Session Usage:
When running commands, inform the user:
- Which session the command is running in
- How to monitor the command
- How to attach to the session if needed

Example:
```
🤖 Executing in agent-tasks session: npm run build
💡 Monitor progress: tmux attach -t agent-tasks
```

### Provide Session Navigation:
Remind users about session switching:
```
Use Ctrl-a + a to switch to agent-tasks session
Use Ctrl-a + u to switch to your user-services session
```

## Special Cases

### Interactive Commands:
For commands that require user interaction, inform the user they need to attach to the session:
```bash
./tmux-agent-cmd.sh exec "npm init"
# Then inform user: "Please attach to agent session to complete interactive setup"
```

### File Operations:
File operations (reading, writing, editing) should still use the regular file tools, not the tmux wrapper. Only terminal commands should use the wrapper.

### IDE Operations:
Operations that open files in the IDE or manipulate the project structure directly should not use the tmux wrapper.

## Verification Commands

Before executing complex operations, verify the environment:
```bash
# Check tmux is available
command -v tmux >/dev/null 2>&1

# Check agent session exists
tmux has-session -t agent-tasks 2>/dev/null

# Check wrapper script exists
[ -f "./tmux-agent-cmd.sh" ] && [ -x "./tmux-agent-cmd.sh" ]
```

This ensures optimal development workflow separation and monitoring capabilities. 