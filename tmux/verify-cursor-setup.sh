#!/bin/bash

# Cursor Agent Tmux Integration Verification Script

echo "🔍 Verifying Cursor Agent Tmux Integration Setup..."
echo ""

# Check if .cursorrules exists
if [ -f ".cursor/rules/tmux-commands.mdc" ]; then
    echo "✅ .cursor/rules/tmux-commands.mdc file found"
else
    echo "❌ .cursor/rules/tmux-commands.mdc file missing"
    exit 1
fi

# Check if tmux wrapper script exists and is executable
if [ -f "./tmux-agent-cmd.sh" ] && [ -x "./tmux-agent-cmd.sh" ]; then
    echo "✅ tmux-agent-cmd.sh exists and is executable"
else
    echo "❌ tmux-agent-cmd.sh missing or not executable"
    exit 1
fi

# Check if helper script exists and is executable
if [ -f "./tmux-dev-helper.sh" ] && [ -x "./tmux-dev-helper.sh" ]; then
    echo "✅ tmux-dev-helper.sh exists and is executable"
else
    echo "❌ tmux-dev-helper.sh missing or not executable"
    exit 1
fi

# Check if configuration script exists
if [ -f "./cursor-agent-config.sh" ] && [ -x "./cursor-agent-config.sh" ]; then
    echo "✅ cursor-agent-config.sh exists and is executable"
else
    echo "❌ cursor-agent-config.sh missing or not executable"
    exit 1
fi

# Check if documentation exists
if [ -f "CURSOR_AGENT_SETUP.md" ]; then
    echo "✅ CURSOR_AGENT_SETUP.md documentation found"
else
    echo "❌ CURSOR_AGENT_SETUP.md documentation missing"
fi

if [ -f "TMUX_WORKFLOW.md" ]; then
    echo "✅ TMUX_WORKFLOW.md documentation found"
else
    echo "❌ TMUX_WORKFLOW.md documentation missing"
fi

echo ""
echo "🧪 Testing tmux wrapper functionality..."

# Test the wrapper with a simple command
echo "Testing: ./tmux-agent-cmd.sh exec 'echo \"Test successful\"'"
./tmux-agent-cmd.sh exec "echo 'Test successful'"

echo ""
echo "📋 Setup Summary:"
echo "✅ .cursorrules configured - Agent will use tmux wrapper"
echo "✅ Scripts created and executable"
echo "✅ Documentation available"
echo ""

# Check if tmux is installed
if command -v tmux &> /dev/null; then
    echo "✅ tmux is installed"
    
    # Check if session exists
    if tmux has-session -t agent-tasks 2>/dev/null; then
        echo "✅ agent-tasks session exists"
        echo ""
        echo "🎉 Full tmux integration is ACTIVE!"
        echo "   Agent commands will run in the agent-tasks session"
        echo "   Monitor with: ./tmux-dev-helper.sh agent"
    else
        echo "⚠️  agent-tasks session not found"
        echo "   Run: ./tmux-dev-helper.sh setup"
        echo "   Then agent commands will use tmux integration"
    fi
else
    echo "⚠️  tmux not installed"
    echo "   Install with: brew install tmux (macOS) or apt-get install tmux (Linux)"
    echo "   Agent commands will fall back to direct execution"
fi

echo ""
echo "🚀 Next Steps:"
echo "1. Install tmux if not available"
echo "2. Run: ./tmux-dev-helper.sh setup"
echo "3. Start interacting with the Cursor agent"
echo "4. Monitor agent activities with: ./tmux-dev-helper.sh agent"
echo ""
echo "The agent will now automatically use tmux wrapper commands based on .cursorrules" 