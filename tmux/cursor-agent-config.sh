#!/bin/bash

# Cursor Agent Configuration
# This script sets up environment variables and functions for the cursor agent

# Export tmux session configuration
export CURSOR_AGENT_SESSION="agent-tasks"
export CURSOR_AGENT_WINDOW="commands"
export CURSOR_AGENT_USE_TMUX=true

# Function to execute commands in the agent session
agent_exec() {
    local cmd="$1"
    local bg_flag="$2"
    
    if [ "$CURSOR_AGENT_USE_TMUX" = "true" ]; then
        if [ "$bg_flag" = "bg" ]; then
            ./tmux-agent-cmd.sh bg "$cmd"
        else
            ./tmux-agent-cmd.sh exec "$cmd"
        fi
    else
        # Fallback to direct execution
        if [ "$bg_flag" = "bg" ]; then
            nohup bash -c "$cmd" &
        else
            bash -c "$cmd"
        fi
    fi
}

# Function to create a dedicated window for a task
agent_window() {
    local name="$1"
    local cmd="$2"
    
    if [ "$CURSOR_AGENT_USE_TMUX" = "true" ]; then
        ./tmux-agent-cmd.sh window "$name" "$cmd"
    else
        echo "Tmux not configured, running directly: $cmd"
        bash -c "$cmd"
    fi
}

# Function to show agent status
agent_status() {
    if [ "$CURSOR_AGENT_USE_TMUX" = "true" ]; then
        ./tmux-agent-cmd.sh status
    else
        echo "Tmux not configured"
    fi
}

# Function to kill agent processes
agent_kill() {
    if [ "$CURSOR_AGENT_USE_TMUX" = "true" ]; then
        ./tmux-agent-cmd.sh kill
    else
        echo "Tmux not configured - cannot kill processes"
    fi
}

# Set up aliases for common operations
alias agent-exec="agent_exec"
alias agent-bg="agent_exec bg"
alias agent-window="agent_window"
alias agent-status="agent_status"
alias agent-kill="agent_kill"

# Display configuration
echo "🤖 Cursor Agent Configuration Loaded"
echo "Session: $CURSOR_AGENT_SESSION"
echo "Window: $CURSOR_AGENT_WINDOW"
echo "Use Tmux: $CURSOR_AGENT_USE_TMUX"
echo ""
echo "Available commands:"
echo "  agent-exec <cmd>      - Execute command in agent session"
echo "  agent-bg <cmd>        - Execute command in background"
echo "  agent-window <name>   - Create new window for task"
echo "  agent-status          - Show agent session status"
echo "  agent-kill            - Kill all agent processes" 