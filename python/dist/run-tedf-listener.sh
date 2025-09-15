#!/bin/bash
# TEDF Listener Standalone Launcher
# This executable includes all dependencies

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "TEDF Listener - Standalone Edition"
echo "=================================="
echo ""
echo "Listening for TEDF messages on port 5555..."
echo "Press Ctrl+C to exit"
echo ""

# Run the standalone executable
./tedf-listener "$@"