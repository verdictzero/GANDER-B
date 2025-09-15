# TEDF Message Listener

A command-line utility for monitoring and analyzing TEDF (Tactical Entity Data Format) messages broadcast by the Battlespace Simulator.

## Features

- **Real-time monitoring** of TEDF messages via ZeroMQ
- **Multiple display modes** for different use cases
- **Human-readable analysis** with military terminology
- **Message filtering** by type
- **Statistical analysis** and reporting
- **Graceful shutdown** with Ctrl+C

## Quick Start

```bash
# Basic usage - connect to localhost:5555 with pretty display
python3 tedf-listener.py

# Compact mode for monitoring many entities
python3 tedf-listener.py -m compact

# Raw JSON output for debugging
python3 tedf-listener.py -m raw

# Filter for only position updates
python3 tedf-listener.py -f compact
```

## Display Modes

### Pretty Mode (Default)
Shows detailed, human-readable information with icons and analysis:
```
[14:23:45.123] 📊 FULL - Complete entity data
--------------------------------------------------
✈️ Entity: a1b2c3d4...
   Type: Multirole Fighter Air
   📻 Callsign: VIPER-1
   🟢 Disposition: Friendly (High confidence)
   📍 Position: 1250m northeast, medium altitude
      Coordinates: (1000.0, 300.0, 800.0)
   🧭 Movement: cruising speed (120 m/s), heading northeast (45°)
```

### Compact Mode
One-line summaries for high-throughput monitoring:
```
[14:23:45] F | a1b2c3d4 (AIR) | Pos: (1000.0, 300.0, 800.0) | Spd: 120.0 | Hdg: 45°
[14:23:46] C | b2c3d4e5 (GROUND) | Pos: (500.0, 0.0, -200.0) | Spd: 15.0 | Hdg: 180°
```

### Raw Mode
Complete JSON messages for debugging and logging:
```
[14:23:45.123] {"messageType":"full","entityId":"a1b2c3d4-e5f6-7890-abcd-ef1234567890",...}
```

### Stats Mode
Only displays periodic statistics, no individual messages:
```
📊 STATS: 1,247 msgs | 5.2 msgs/s | 23 entities | Uptime: 240s
```

## Command Line Options

```
-a, --address ADDRESS     ZMQ address (default: tcp://localhost)
-p, --port PORT          ZMQ port (default: 5555)
-m, --mode MODE          Display mode: raw, pretty, compact, stats
-f, --filter TYPE        Show only: full, compact, batch, despawn messages
--no-timestamps          Hide timestamps
--stats-interval N       Statistics update interval in seconds
```

## Analysis Features

### Entity Type Recognition
- **Icons**: ✈️ Aircraft, 🚗 Vehicles, 🚶 Infantry, 🚢 Naval
- **Classifications**: Air/Ground/Naval with subcategories
- **Human names**: "Multirole Fighter Air" instead of "AIR/FIGHTER/MULTIROLE"

### Disposition Analysis
- **Color coding**: 🟢 Friendly, 🔴 Hostile, 🟡 Neutral, ⚪ Unknown
- **Confidence levels**: High/Medium/Low confidence descriptions

### Movement Analysis
- **Speed context**: Different scales for aircraft vs ground vs infantry
- **Heading**: Cardinal directions with degrees
- **Altitude changes**: Climbing/descending with rates
- **Movement patterns**: Stationary, slow, moderate, fast, high speed

### Positional Analysis
- **Coordinate quadrants**: Northeast, southwest, etc.
- **Distance from origin**: Meters from center point
- **Altitude context**: Ground level, low/medium/high altitude

### Batch Analysis
- **Composition breakdown**: Entity types and percentages
- **Force distribution**: Friendly/hostile ratios
- **Sample entities**: Shows first few entities in detail

## Use Cases

### Development & Debugging
```bash
# Monitor all messages in raw format for debugging
python3 tedf-listener.py -m raw > debug_log.json

# Watch only despawn events
python3 tedf-listener.py -f despawn -m pretty
```

### Operations Monitoring
```bash
# Compact view for situation awareness
python3 tedf-listener.py -m compact

# Statistics only for performance monitoring
python3 tedf-listener.py -m stats --stats-interval 5
```

### Analysis & Testing
```bash
# Monitor batch updates during heavy load testing
python3 tedf-listener.py -f batch -m pretty

# Track entity movements only
python3 tedf-listener.py -f compact -m compact
```

### Remote Monitoring
```bash
# Connect to remote simulator
python3 tedf-listener.py -a tcp://192.168.1.100 -p 5555

# Monitor production system
python3 tedf-listener.py -a tcp://prod-server -p 5556 -m stats
```

## Statistics Tracking

The listener continuously tracks:
- **Message counts** by type (full, compact, batch, despawn)
- **Entity counts** by category (air, ground, etc.)
- **Connection statistics** (attempts, errors, uptime)
- **Performance metrics** (messages per second, data age)

Final statistics are displayed on exit:
```
📊 FINAL STATISTICS
============================================================
Total Messages Received: 1,247
Average Rate: 5.19 messages/second
Total Runtime: 240.1 seconds
Active Entities: 23

Message Types:
  compact: 1,089 (87.3%)
  full: 123 (9.9%)
  batch: 30 (2.4%)
  despawn: 5 (0.4%)

Entity Types Seen:
  AIR: 8
  GROUND: 15
```

## Error Handling

- **Connection failures**: Automatic retry with backoff
- **Malformed JSON**: Error reporting with raw message display
- **Network timeouts**: Graceful handling with reconnection
- **Signal handling**: Clean shutdown with Ctrl+C

## Integration

The listener can be easily integrated into:
- **CI/CD pipelines**: For automated testing and validation
- **Monitoring systems**: For operational oversight
- **Analysis tools**: Raw JSON output for further processing
- **Development workflows**: Real-time debugging during development

## Examples

See `examples/listen-example.sh` for more usage examples and patterns.