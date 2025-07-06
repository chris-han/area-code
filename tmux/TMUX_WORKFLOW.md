# Tmux Development Workflow

This setup provides a structured way to manage development processes using tmux, particularly useful when working with the Cursor agent to avoid command conflicts and maintain clear process separation.

## Quick Start

1. **Setup the environment:**
   ```bash
   chmod +x tmux-dev-setup.sh tmux-dev-helper.sh
   ./tmux-dev-helper.sh setup
   ```

2. **Attach to your preferred session:**
   ```bash
   ./tmux-dev-helper.sh user    # Your long-running services
   ./tmux-dev-helper.sh agent   # Agent command execution
   ./tmux-dev-helper.sh infra   # Infrastructure containers
   ./tmux-dev-helper.sh build   # Build processes
   ```

## Session Structure

### 📱 **user-services** - Your Domain
- **Purpose**: Long-running services you manage manually
- **Windows**: `main` (4 panes), `web-app`
- **Panes**: 
  - Transactional Service
  - Sync Service  
  - Retrieval Service
  - Analytics Service
- **Use for**: `pnpm run dev`, service monitoring, manual testing

### 🤖 **agent-tasks** - Cursor Agent Domain
- **Purpose**: Commands executed by the Cursor agent
- **Windows**: `commands`, `scratch`
- **Use for**: Agent-initiated builds, tests, migrations, deployments
- **Benefit**: Keeps agent commands isolated from your processes

### 🏗️ **infra** - Infrastructure
- **Purpose**: Docker containers, Moose, and redpanda operations
- **Windows**: `containers`, `logs`
- **Use for**: `docker-compose up/down`, Moose services, redpanda, container monitoring

### 🔧 **build-watch** - Build Processes
- **Purpose**: Turbo build processes and file watching
- **Windows**: `turbo`, `dev`
- **Use for**: `turbo dev`, `turbo build`, continuous compilation

## Key Benefits

1. **Process Isolation**: Agent commands won't interfere with your running services
2. **Clear Ownership**: Know immediately which processes are yours vs. agent-managed
3. **Context Switching**: Quickly jump between different aspects of development
4. **Parallel Development**: Run multiple services simultaneously without conflicts
5. **Session Persistence**: Processes continue running even if you disconnect

## Common Workflows

### Starting Development
```bash
# Setup tmux environment
./tmux-dev-helper.sh setup

# Start your services in user-services session
./tmux-dev-helper.sh user
# In pane 1: cd services/transactional-base && pnpm run dev
# In pane 2: cd services/sync-base && pnpm run dev
# etc.

# Start infrastructure in separate session
./tmux-dev-helper.sh infra
# docker-compose up -d
```

### Working with Cursor Agent
- The agent will automatically use the `agent-tasks` session via `tmux-agent-cmd.sh`
- Your services keep running uninterrupted
- Easy to monitor what the agent is doing
- Agent commands are logged separately
- See `CURSOR_AGENT_SETUP.md` for detailed configuration

### Monitoring Everything
```bash
# Quick status check
./tmux-dev-helper.sh status

# Jump between sessions
# Ctrl-a + u  (user-services)
# Ctrl-a + a  (agent-tasks)
# Ctrl-a + i  (infra)
# Ctrl-a + b  (build-watch)
```

## Helper Commands

```bash
# Show current sessions
./tmux-dev-helper.sh status

# Kill and restart everything
./tmux-dev-helper.sh restart

# Kill specific session
./tmux-dev-helper.sh kill user-services

# Kill all development sessions
./tmux-dev-helper.sh killall
```

## Tmux Keyboard Shortcuts

### Session Management
- `Ctrl-a + u` - Switch to user-services
- `Ctrl-a + a` - Switch to agent-tasks  
- `Ctrl-a + i` - Switch to infra
- `Ctrl-a + b` - Switch to build-watch

### Pane Management
- `Ctrl-a + |` - Split vertically
- `Ctrl-a + -` - Split horizontally
- `Ctrl-a + h/j/k/l` - Navigate panes (vim-style)
- `Ctrl-a + H/J/K/L` - Resize panes

### Window Management
- `Ctrl-a + c` - Create new window
- `Ctrl-a + n` - Next window
- `Ctrl-a + p` - Previous window
- `Ctrl-a + &` - Kill current window

## Integration with Development Tools

### Turborepo
```bash
# In build-watch session
turbo dev --filter=@workspace/vite-web-base
turbo build --filter=@workspace/ui
```

### Docker Compose & Moose
```bash
# In infra session
docker-compose -f services/transactional-base/docker-compose.yml up -d
cd services/analytical-base && moose dev
```

### Service Development
```bash
# In user-services session, different panes
cd services/transactional-base && pnpm run dev
cd services/sync-base && pnpm run dev
cd services/retrieval-base && pnpm run dev
cd services/analytical-base && pnpm run dev
```

## Troubleshooting

### Session Not Found
```bash
# Check what sessions exist
tmux list-sessions

# Recreate environment
./tmux-dev-helper.sh restart
```

### Agent Commands Not Working
- Ensure agent is using the `agent-tasks` session
- Check that the session exists: `tmux has-session -t agent-tasks`
- Restart if needed: `./tmux-dev-helper.sh restart`

### Config Not Loading
```bash
# Reload tmux configuration
tmux source-file ~/.tmux.conf
```

## Tips

1. **Use descriptive window names** - Rename windows to match what they're running
2. **Monitor activity** - Activity monitoring is enabled to see when processes have output
3. **Log everything** - Each session maintains its own history
4. **Keep sessions running** - Detach instead of killing to maintain state
5. **Use mouse support** - Mouse is enabled for easy pane switching and resizing

## Customization

Edit `tmux-dev-setup.sh` to:
- Add more sessions for specific projects
- Change pane layouts
- Customize window names
- Add startup commands

Edit `.tmux.conf` to:
- Change key bindings
- Modify colors and status bar
- Add more shortcuts
- Customize behavior 