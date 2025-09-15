# TEDF Listener - Standalone Edition

This is a standalone executable version of the TEDF (Tactical Entity Data Format) Listener that monitors and displays messages from the Battlespace Simulator.

## Files Included

- `tedf-listener` - The standalone executable
- `example_entities.json` - Example entity database file
- `README-TEDF-LISTENER.md` - This file
- `run-tedf-listener.sh` - Convenience launcher script

## Running the Listener

### Basic Usage
```bash
./tedf-listener
```

### With Options
```bash
# Pretty print mode (default)
./tedf-listener --mode pretty

# Raw JSON mode
./tedf-listener --mode raw

# Compact mode
./tedf-listener --mode compact

# Filter by message type
./tedf-listener --filter full
./tedf-listener --filter compact
./tedf-listener --filter batch

# Custom port
./tedf-listener --port 5556

# Show help
./tedf-listener --help
```

## Display Modes

1. **Pretty Mode** (default)
   - Formatted output with colors
   - Shows entity details in readable format
   - Displays statistics every 10 seconds

2. **Raw Mode**
   - Shows complete JSON messages
   - Useful for debugging
   - No formatting applied

3. **Compact Mode**
   - One-line summary per message
   - Shows entity count and types
   - Minimal output

4. **Stats Mode**
   - Shows message statistics only
   - Updates every second
   - No individual messages shown

## Example Entity File

The included `example_entities.json` file contains sample entity definitions that can be loaded into the Battlespace Simulator. It includes various military unit types with NATO symbols and 3D models.

### Entity Structure
```json
{
  "entities": [
    {
      "id": "unique_id",
      "name": "Display Name",
      "symbolCode": "NATO_2525_CODE",
      "modelPath": "path/to/3d/model.fbx",
      "description": "Entity description"
    }
  ]
}
```

## Features

- Real-time TEDF message monitoring
- Multiple display formats
- Message type filtering
- Connection statistics
- Automatic reconnection
- Signal handling (Ctrl+C to exit)

## System Requirements

- Linux x86_64 system
- No Python installation required
- No additional dependencies needed

## Technical Details

- Built with PyInstaller 6.14.2
- Includes ZeroMQ (pyzmq) for messaging
- Listens on TCP port 5555 by default
- Supports all TEDF message types

## Typical Workflow

1. Start the Battlespace Simulator
2. Run the TEDF Listener to monitor messages
3. Watch entities being created, updated, and destroyed
4. Use different modes to analyze message flow

## Troubleshooting

### No Messages Received
- Ensure the Battlespace Simulator is running
- Check that port 5555 is not blocked
- Verify the simulator is broadcasting

### Connection Errors
- Check if another listener is already running
- Ensure proper network permissions
- Try a different port with --port option

### Performance Issues
- Use compact or stats mode for high message rates
- Filter specific message types to reduce load

## Message Types

- **Full Update**: Complete entity state
- **Compact Update**: Position and velocity only
- **Batch Update**: Multiple entities at once
- **Despawn**: Entity removal notification

## Exit

Press Ctrl+C to gracefully shutdown the listener.