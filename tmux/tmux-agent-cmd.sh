#!/bin/bash

# Tmux Agent Command Wrapper
# This script ensures cursor agent commands run in the agent-tasks session

AGENT_SESSION="agent-tasks"
AGENT_WINDOW="commands"

# Check if tmux is running and session exists
check_agent_session() {
    if ! command -v tmux &> /dev/null; then
        echo "❌ tmux is not installed"
        return 1
    fi
    
    if ! tmux has-session -t "$AGENT_SESSION" 2>/dev/null; then
        echo "❌ Agent session '$AGENT_SESSION' not found"
        echo "Run './tmux-dev-helper.sh setup' to create the environment"
        return 1
    fi
    
    return 0
}

# Execute command in agent session
execute_in_agent_session() {
    local cmd="$1"
    local window="${2:-$AGENT_WINDOW}"
    
    if ! check_agent_session; then
        echo "Falling back to direct execution..."
        bash -c "$cmd"
        return $?
    fi
    
    echo "🤖 Executing in agent-tasks session: $cmd"
    
    # Clear the current line and send the command
    tmux send-keys -t "$AGENT_SESSION:$window" C-c
    tmux send-keys -t "$AGENT_SESSION:$window" "clear" C-m
    tmux send-keys -t "$AGENT_SESSION:$window" "$cmd" C-m
    
    # Wait a moment for command to start
    sleep 0.5
    
    # Capture and return the exit status
    # Note: This is a simplified approach - for complex commands you might need more sophisticated status checking
    echo "✅ Command sent to agent-tasks session"
    echo "💡 Monitor progress: tmux attach -t $AGENT_SESSION"
}

# Execute command in background in agent session
execute_in_agent_session_bg() {
    local cmd="$1"
    local window="${2:-$AGENT_WINDOW}"
    
    if ! check_agent_session; then
        echo "Falling back to direct execution..."
        nohup bash -c "$cmd" &
        return $?
    fi
    
    echo "🤖 Executing in background in agent-tasks session: $cmd"
    
    # Send command to run in background
    tmux send-keys -t "$AGENT_SESSION:$window" C-c
    tmux send-keys -t "$AGENT_SESSION:$window" "clear" C-m
    tmux send-keys -t "$AGENT_SESSION:$window" "$cmd &" C-m
    
    echo "✅ Background command sent to agent-tasks session"
    echo "💡 Monitor progress: tmux attach -t $AGENT_SESSION"
}

# Create a new window in agent session for a specific task
create_agent_window() {
    local window_name="$1"
    local cmd="$2"
    
    if ! check_agent_session; then
        echo "❌ Cannot create agent window - session not available"
        return 1
    fi
    
    echo "🤖 Creating new window '$window_name' in agent-tasks session"
    
    # Create new window
    tmux new-window -t "$AGENT_SESSION" -n "$window_name" -c "$(pwd)"
    
    # Execute command if provided
    if [ -n "$cmd" ]; then
        tmux send-keys -t "$AGENT_SESSION:$window_name" "$cmd" C-m
    fi
    
    echo "✅ Window '$window_name' created in agent-tasks session"
    echo "💡 Switch to it: tmux select-window -t $AGENT_SESSION:$window_name"
}

# Show current status of agent session
show_agent_status() {
    if ! check_agent_session; then
        return 1
    fi
    
    echo "🤖 Agent Session Status:"
    tmux list-windows -t "$AGENT_SESSION"
    echo ""
    echo "💡 To monitor: tmux attach -t $AGENT_SESSION"
}

# Kill all processes in agent session
kill_agent_processes() {
    if ! check_agent_session; then
        return 1
    fi
    
    echo "🤖 Killing all processes in agent-tasks session..."
    
    # Send Ctrl+C to all windows in the session
    for window in $(tmux list-windows -t "$AGENT_SESSION" -F "#{window_name}"); do
        echo "Stopping processes in window: $window"
        tmux send-keys -t "$AGENT_SESSION:$window" C-c
        tmux send-keys -t "$AGENT_SESSION:$window" "clear" C-m
    done
    
    echo "✅ All agent processes stopped"
}

# Main command dispatcher
case "$1" in
    exec)
        execute_in_agent_session "$2" "$3"
        ;;
    bg)
        execute_in_agent_session_bg "$2" "$3"
        ;;
    window)
        create_agent_window "$2" "$3"
        ;;
    status)
        show_agent_status
        ;;
    kill)
        kill_agent_processes
        ;;
    *)
        echo "Tmux Agent Command Wrapper"
        echo ""
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  exec <cmd> [window]     - Execute command in agent session"
        echo "  bg <cmd> [window]       - Execute command in background"
        echo "  window <name> [cmd]     - Create new window with optional command"
        echo "  status                  - Show agent session status"
        echo "  kill                    - Kill all processes in agent session"
        echo ""
        echo "Examples:"
        echo "  $0 exec 'npm run build'"
        echo "  $0 bg 'npm run dev'"
        echo "  $0 window 'testing' 'npm test'"
        echo "  $0 status"
        ;;
esac 