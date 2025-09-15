#!/bin/bash
# Battlespace Simulator Standalone Launcher
# This executable includes all dependencies

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting Battlespace Simulator (Standalone Edition)..."
echo "=================================================="
echo ""

# Run the standalone executable
./battlespace-simulator "$@"