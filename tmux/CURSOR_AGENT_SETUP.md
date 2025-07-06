# Cursor Agent Tmux Integration

This guide explains how to ensure the Cursor agent uses the dedicated `agent-tasks` tmux session for all commands, keeping agent operations isolated from your user processes.

## Quick Setup

1. **Make scripts executable:**
   ```bash
   chmod +x tmux-agent-cmd.sh cursor-agent-config.sh
   ```

2. **Setup tmux environment:**
   ```bash
   ./tmux-dev-helper.sh setup
   ```

3. **Load agent configuration:**
   ```bash
   source cursor-agent-config.sh
   ```

## How It Works

### The Problem
By default, when the Cursor agent runs commands, they execute in your current terminal session. This can interfere with your running services and create process conflicts.

### The Solution
The tmux integration system automatically routes all agent commands to the dedicated `agent-tasks` session, ensuring:
- ✅ Agent commands don't interfere with your services
- ✅ Easy monitoring of agent activities
- ✅ Process isolation and organization
- ✅ Ability to kill agent processes independently

## Components

### 1. `tmux-agent-cmd.sh` - Command Wrapper
Routes commands to the agent-tasks session:
```bash
./tmux-agent-cmd.sh exec "npm run build"     # Execute command
./tmux-agent-cmd.sh bg "npm run dev"         # Background execution
./tmux-agent-cmd.sh window "testing" "npm test"  # New window
./tmux-agent-cmd.sh status                   # Show status
./tmux-agent-cmd.sh kill                     # Kill processes
```

### 2. `cursor-agent-config.sh` - Configuration
Sets up environment and aliases:
```bash
agent-exec "npm run build"    # Execute in agent session
agent-bg "npm run dev"        # Background execution
agent-window "testing"        # Create new window
agent-status                  # Show status
agent-kill                    # Kill processes
```

## Usage Patterns

### For Regular Commands
Instead of running commands directly, the agent will use:
```bash
# Before (runs in your terminal)
npm run build

# After (runs in agent-tasks session)
./tmux-agent-cmd.sh exec "npm run build"
```

### For Background Processes
```bash
# Before (backgrounds in your terminal)
npm run dev &

# After (backgrounds in agent session)
./tmux-agent-cmd.sh bg "npm run dev"
```

### For Complex Tasks
```bash
# Create dedicated window for testing
./tmux-agent-cmd.sh window "testing" "npm test"

# Create window for building
./tmux-agent-cmd.sh window "build" "npm run build"
```

## Monitoring Agent Activities

### View Agent Session
```bash
# Quick attach to agent session
./tmux-dev-helper.sh agent

# Or directly
tmux attach -t agent-tasks
```

### Check Agent Status
```bash
./tmux-agent-cmd.sh status
```

### Switch Between Sessions
```bash
# Your services
Ctrl-a + u

# Agent activities  
Ctrl-a + a

# Infrastructure
Ctrl-a + i

# Build processes
Ctrl-a + b
```

## Example Workflow

### 1. Setup Environment
```bash
# One-time setup
./tmux-dev-helper.sh setup
chmod +x tmux-agent-cmd.sh cursor-agent-config.sh

# Load configuration
source cursor-agent-config.sh
```

### 2. Start Your Services
```bash
# In user-services session
./tmux-dev-helper.sh user
# Start your services manually in different panes
```

### 3. Agent Executes Commands
When you ask the agent to run commands, they automatically go to the agent-tasks session:
```bash
# Agent runs build
./tmux-agent-cmd.sh exec "npm run build"

# Agent starts dev server
./tmux-agent-cmd.sh bg "npm run dev"

# Agent runs tests
./tmux-agent-cmd.sh window "testing" "npm test"
```

### 4. Monitor Everything
```bash
# Check what agent is doing
./tmux-agent-cmd.sh status

# View agent session
./tmux-dev-helper.sh agent

# View your services
./tmux-dev-helper.sh user
```

## Agent Command Integration

### Automatic Routing
The system is designed so that when you instruct the Cursor agent to run commands, they automatically use the tmux wrapper. The agent should:

1. **Check for tmux environment** before running commands
2. **Use tmux wrapper** if available
3. **Fall back to direct execution** if tmux is not available

### Command Examples
When you tell the agent to:
- "Run npm run build" → Executes in agent-tasks session
- "Start the dev server" → Backgrounds in agent-tasks session  
- "Run tests" → Creates new window in agent-tasks session
- "Install dependencies" → Executes in agent-tasks session

## Troubleshooting

### Agent Commands Not Using Tmux
If commands are still running in your terminal:
```bash
# Check if session exists
tmux has-session -t agent-tasks

# Recreate if needed
./tmux-dev-helper.sh restart

# Verify wrapper works
./tmux-agent-cmd.sh exec "echo 'test'"
```

### Session Not Found
```bash
# Recreate environment
./tmux-dev-helper.sh setup

# Check sessions
tmux list-sessions
```

### Commands Hanging
```bash
# Kill agent processes
./tmux-agent-cmd.sh kill

# Or kill specific window
tmux kill-window -t agent-tasks:commands
```

## Advanced Configuration

### Custom Session Names
Edit `tmux-agent-cmd.sh`:
```bash
AGENT_SESSION="my-agent-session"
AGENT_WINDOW="my-commands"
```

### Disable Tmux Integration
```bash
export CURSOR_AGENT_USE_TMUX=false
```

### Multiple Agent Windows
```bash
# Create specialized windows
./tmux-agent-cmd.sh window "build" "npm run build"
./tmux-agent-cmd.sh window "test" "npm test"
./tmux-agent-cmd.sh window "lint" "npm run lint"
```

## Best Practices

1. **Always monitor agent session** - Keep an eye on what the agent is doing
2. **Use descriptive window names** - Name windows based on their purpose
3. **Kill processes cleanly** - Use `agent-kill` to stop processes
4. **Keep sessions organized** - Don't let too many windows accumulate
5. **Check status regularly** - Use `agent-status` to see current state

## Integration with Development Workflow

This tmux integration works seamlessly with your existing development workflow:

- **Your services** run in `user-services` session
- **Agent commands** run in `agent-tasks` session  
- **Infrastructure** runs in `infra` session
- **Build processes** run in `build-watch` session

Each session is isolated but easy to monitor and manage, giving you complete control over your development environment while allowing the agent to work efficiently without interference. 