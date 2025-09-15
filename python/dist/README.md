# Battlespace Simulation Tools - Standalone Distribution

This directory contains standalone executable versions of the Battlespace simulation tools. No Python installation or dependencies are required.

## Included Tools

### 1. Battlespace Simulator
The main simulation engine that generates and broadcasts TEDF (Tactical Entity Data Format) messages.

**Files:**
- `battlespace-simulator` - Console version (recommended)
- `battlespace-simulator-gui` - GUI-only version
- `run-battlespace-simulator.sh` - Launcher script

**Usage:**
```bash
./battlespace-simulator
# or
./run-battlespace-simulator.sh
```

### 2. TEDF Listener
A monitoring tool that displays TEDF messages from the simulator in real-time.

**Files:**
- `tedf-listener` - Standalone listener executable
- `run-tedf-listener.sh` - Launcher script
- `example_entities.json` - Sample entity database

**Usage:**
```bash
./tedf-listener
# or
./run-tedf-listener.sh
```

## Quick Start

1. **Terminal 1 - Start the Simulator:**
   ```bash
   ./battlespace-simulator
   ```
   This will open a GUI where you can configure and start the simulation.

2. **Terminal 2 - Monitor Messages:**
   ```bash
   ./tedf-listener
   ```
   This will display incoming TEDF messages as entities are created and updated.

## System Requirements

- Linux x86_64 system
- No Python installation required
- Ports 5555 (default) should be available

## Example Workflow

1. Start the battlespace simulator
2. Load entities from the GUI or use default entities
3. Start simulation broadcasting
4. In another terminal, run the TEDF listener
5. Observe entity messages being transmitted

## File Sizes

- Battlespace Simulator: ~17MB each version
- TEDF Listener: ~12MB
- Total distribution: ~46MB

## Documentation

- See `README-STANDALONE.md` for Battlespace Simulator details
- See `README-TEDF-LISTENER.md` for TEDF Listener details

## Distribution

These executables can be copied to any Linux x86_64 system and run without installing Python or any dependencies. All required libraries are bundled within the executables.