#!/bin/bash

# Tmux Development Environment Setup
# This script creates separate tmux sessions for different aspects of development

echo "Setting up tmux development environment..."

# Kill existing sessions if they exist
tmux kill-session -t user-services 2>/dev/null || true
tmux kill-session -t agent-tasks 2>/dev/null || true
tmux kill-session -t infra 2>/dev/null || true
tmux kill-session -t build-watch 2>/dev/null || true

# Create main user-controlled services session
tmux new-session -d -s user-services -c "$(pwd)"
tmux rename-window -t user-services:0 "main"

# Split into panes for different services
tmux split-window -t user-services:0 -h -c "$(pwd)"
tmux split-window -t user-services:0.1 -v -c "$(pwd)"
tmux split-window -t user-services:0.0 -v -c "$(pwd)"

# Label the panes
tmux send-keys -t user-services:0.0 "echo 'Transactional Service (User)'" C-m
tmux send-keys -t user-services:0.1 "echo 'Sync Service (User)'" C-m
tmux send-keys -t user-services:0.2 "echo 'Retrieval Service (User)'" C-m
tmux send-keys -t user-services:0.3 "echo 'Analytics Service (User)'" C-m

# Create agent-controlled session for temporary tasks
tmux new-session -d -s agent-tasks -c "$(pwd)"
tmux rename-window -t agent-tasks:0 "commands"
tmux send-keys -t agent-tasks:0 "echo 'Agent Command Execution Area'" C-m
tmux send-keys -t agent-tasks:0 "echo 'The cursor agent will run commands here'" C-m

# Create infrastructure session
tmux new-session -d -s infra -c "$(pwd)"
tmux rename-window -t infra:0 "containers"
tmux send-keys -t infra:0 "echo 'Infrastructure Containers'" C-m
tmux send-keys -t infra:0 "echo 'Use this for docker-compose up/down, Moose, redpanda'" C-m

# Create build/watch session
tmux new-session -d -s build-watch -c "$(pwd)"
tmux rename-window -t build-watch:0 "turbo"
tmux send-keys -t build-watch:0 "echo 'Turbo Build/Watch Processes'" C-m

# Create additional windows for each session
tmux new-window -t user-services -n "web-app" -c "$(pwd)/apps/vite-web-base"
tmux new-window -t agent-tasks -n "scratch" -c "$(pwd)"
tmux new-window -t infra -n "logs" -c "$(pwd)"
tmux new-window -t build-watch -n "dev" -c "$(pwd)"

echo ""
echo "✅ Tmux development environment created!"
echo ""
echo "Available sessions:"
echo "  📱 user-services  - Your long-running services"
echo "  🤖 agent-tasks    - Cursor agent commands"
echo "  🏗️  infra          - Infrastructure (containers, Moose, redpanda)"
echo "  🔧 build-watch    - Build processes"
echo ""
echo "Quick access commands:"
echo "  tmux attach -t user-services"
echo "  tmux attach -t agent-tasks"
echo "  tmux attach -t infra"
echo "  tmux attach -t build-watch"
echo ""
echo "Or use: tmux list-sessions" 