#!/bin/bash

# Tmux Development Helper Script
# Provides common operations for the development workflow

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

show_help() {
    echo "Tmux Development Helper"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup           - Initial tmux environment setup"
    echo "  status          - Show current tmux sessions"
    echo "  attach [name]   - Attach to a specific session"
    echo "  agent           - Quick attach to agent-tasks session"
echo "  user            - Quick attach to user-services session"
echo "  infra           - Quick attach to infra session"
echo "  build           - Quick attach to build-watch session"
    echo "  kill [name]     - Kill a specific session"
    echo "  killall         - Kill all development sessions"
    echo "  restart         - Kill all and setup fresh"
    echo "  logs            - Show tmux server logs"
    echo ""
    echo "Available sessions:"
echo "  📱 user-services  - Your long-running services"
echo "  🤖 agent-tasks    - Cursor agent commands"
echo "  🏗️  infra          - Infrastructure (containers, Moose, redpanda)"
echo "  🔧 build-watch    - Build processes"
}

check_tmux() {
    if ! command -v tmux &> /dev/null; then
        echo "❌ tmux is not installed. Please install tmux first."
        exit 1
    fi
}

setup_environment() {
    echo "Setting up tmux development environment..."
    chmod +x "$SCRIPT_DIR/tmux-dev-setup.sh"
    bash "$SCRIPT_DIR/tmux-dev-setup.sh"
}

show_status() {
    echo "Current tmux sessions:"
    if tmux list-sessions 2>/dev/null; then
        echo ""
        echo "Use 'tmux attach -t <session-name>' to attach"
    else
        echo "No active tmux sessions found."
        echo "Run '$0 setup' to create the development environment."
    fi
}

attach_session() {
    local session_name="$1"
    if [ -z "$session_name" ]; then
        echo "Available sessions:"
        tmux list-sessions 2>/dev/null || echo "No sessions found."
        return 1
    fi
    
    if tmux has-session -t "$session_name" 2>/dev/null; then
        tmux attach-session -t "$session_name"
    else
        echo "❌ Session '$session_name' not found."
        echo "Available sessions:"
        tmux list-sessions 2>/dev/null || echo "No sessions found."
    fi
}

kill_session() {
    local session_name="$1"
    if [ -z "$session_name" ]; then
        echo "Please specify a session name to kill."
        return 1
    fi
    
    if tmux has-session -t "$session_name" 2>/dev/null; then
        tmux kill-session -t "$session_name"
        echo "✅ Killed session: $session_name"
    else
        echo "❌ Session '$session_name' not found."
    fi
}

kill_all_sessions() {
    echo "Killing all development sessions..."
    tmux kill-session -t user-services 2>/dev/null && echo "✅ Killed user-services"
    tmux kill-session -t agent-tasks 2>/dev/null && echo "✅ Killed agent-tasks"
    tmux kill-session -t infra 2>/dev/null && echo "✅ Killed infra"
    tmux kill-session -t build-watch 2>/dev/null && echo "✅ Killed build-watch"
    echo "✅ All development sessions killed."
}

restart_environment() {
    echo "Restarting tmux development environment..."
    kill_all_sessions
    sleep 1
    setup_environment
}

show_logs() {
    echo "Tmux server information:"
    tmux info
}

# Main script logic
check_tmux

case "$1" in
    setup)
        setup_environment
        ;;
    status)
        show_status
        ;;
    attach)
        attach_session "$2"
        ;;
    agent)
        attach_session "agent-tasks"
        ;;
    user)
        attach_session "user-services"
        ;;
    infra)
        attach_session "infra"
        ;;
    build)
        attach_session "build-watch"
        ;;
    kill)
        kill_session "$2"
        ;;
    killall)
        kill_all_sessions
        ;;
    restart)
        restart_environment
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            echo "Unknown command: $1"
            echo ""
            show_help
        fi
        ;;
esac 