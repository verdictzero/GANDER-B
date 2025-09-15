# Battlespace Simulator - Standalone Edition

This is a standalone executable version of the Battlespace Simulator that includes all Python dependencies.

## Files Included

- `battlespace-simulator` - The main standalone executable (console version)
- `battlespace-simulator-gui` - GUI-only version (no console window)
- `run-battlespace-simulator.sh` - Convenience launcher script
- `README-STANDALONE.md` - This file

## Running the Simulator

### Option 1: Direct Execution
```bash
./battlespace-simulator
```

### Option 2: Using the Launcher Script
```bash
./run-battlespace-simulator.sh
```

## Features

This standalone executable includes:
- All Python dependencies (pyzmq, psutil, colorama, tkinter)
- The complete battlespace simulation system
- GUI interface with Azure theme
- TEDF message broadcasting via ZeroMQ

## System Requirements

- Linux x86_64 system
- No Python installation required
- No additional dependencies needed

## Command Line Options

The simulator supports the same command line options as the regular version:
- `--check-deps` - Check dependencies (always reports success for standalone)
- `--log-level` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--config` - Path to configuration file

## Technical Details

Built with:
- PyInstaller 6.14.2
- Python 3.12.3
- Includes all required Python modules and data files

## Troubleshooting

If you encounter issues:
1. Ensure the executable has proper permissions: `chmod +x battlespace-simulator`
2. Check that your system is x86_64 Linux
3. Try the console version if the GUI version has issues

## Distribution

This standalone executable can be distributed without requiring Python or any dependencies to be installed on the target system.