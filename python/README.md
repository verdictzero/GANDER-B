# FENRIR Python Simulation Engine

The Python simulation engine provides sophisticated real-time entity simulation, TEDF message broadcasting, and comprehensive user interface for the FENRIR Battlespace Visualization System.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch main simulator (recommended)
python run-simulator.py

# Or launch entity editor
python battlespace-editor.py
```

## 📁 Core Applications

### 🎯 Primary Applications

#### **battlespace-simulator.py** (634 lines)
**Main simulation coordinator** - Integrates all components for complete simulation experience
- **Purpose**: Central application hub coordinating all simulation components
- **Features**:
  - Multi-component integration (simulation + broadcasting + GUI)
  - Network configuration and connection management
  - Comprehensive error handling and recovery
  - Statistics collection and performance monitoring
- **Launch**: `python run-simulator.py` (recommended entry point)

#### **battlespace-editor.py** (922 lines)
**Visual entity definition editor** - Complete database management with modern GUI
- **Purpose**: Visual editing tool for entity definitions and simulation parameters
- **Features**:
  - Tabbed interface (Metadata | Dispositions | Categories | Entities)
  - Live color picker for disposition schemes
  - Entity property validation and error checking
  - Import/export functionality for entity databases
- **Launch**: `python battlespace-editor.py`

### 🔧 Core Engine Components

#### **entity-simulator.py** (637 lines)
**Advanced entity behavior engine** - Realistic movement simulation with multiple behavior patterns
- **Classes**:
  - `SimulatedEntity`: Individual entity with kinematic properties
  - `EntitySimulator`: Main simulation engine with spawning and lifecycle management
- **Features**:
  - 7 patrol behaviors (Random Waypoint, Area Sweep, Orbital, etc.)
  - Realistic physics with speed/acceleration constraints
  - Terrain boundary enforcement with automatic despawning
  - Probabilistic spawning with configurable parameters
- **Entity Types**: Air (3D_FLIGHT, 3D_ROTORCRAFT), Ground (TRACKED, WHEELED, FOOT), Naval (SURFACE, SUBSURFACE)

#### **tedf-broadcaster.py** (620 lines)  
**TEDF message broadcasting system** - High-performance ZeroMQ publisher with message optimization
- **Classes**:
  - `TEDFBroadcaster`: Main broadcasting engine with queuing and statistics
- **Message Types**:
  - **Full Messages**: Complete entity state (spawn, periodic updates)
  - **Compact Messages**: Position-only updates (high frequency, low bandwidth)
  - **Batch Messages**: Multiple entities in single transmission
  - **Despawn Messages**: Entity removal notifications
- **Features**:
  - Message queuing with priority handling
  - Network statistics and performance monitoring
  - Graceful error recovery and reconnection
  - Configurable update rates and batching

#### **gui-components.py** (951 lines)
**Modern Azure-themed user interface** - Comprehensive control interface with real-time monitoring
- **Classes**:
  - `BattlespaceSimulatorGUI`: Main application window with three-pane layout
  - `EntitySummaryFrame`: Real-time entity list with filtering and search
  - `EntityDetailFrame`: Detailed entity information display
  - `SimulationControlFrame`: Tabbed control interface
- **Features**:
  - Live entity tracking with disposition-based filtering
  - Real-time statistics dashboard
  - Configuration management with visual editors
  - Dark/light theme support with persistent preferences
  - Entity refresh buttons and imported entity list display

#### **config-loader.py** (475 lines)
**Configuration and entity database management** - Centralized configuration system
- **Classes**:
  - `ConfigurationLoader`: Main configuration management
  - `EntityDatabaseLoader`: Entity definition database handling
  - `TerrainBoundaryLoader`: Terrain synchronization management
- **Features**:
  - JSON-based configuration with validation
  - Default entity database creation with 3 entity types
  - File synchronization between Python and Unity
  - Path expansion and environment variable support

### 🛠️ Utility Components

#### **run-simulator.py** (201 lines)
**Smart launcher script** - Dependency checking and application startup
- **Features**:
  - Automatic dependency validation
  - Environment checking and setup assistance
  - Error reporting with troubleshooting guidance
  - Cross-platform compatibility

#### **tedf-python.py** (396 lines)
**TEDF data structures and utilities** - Core protocol implementation
- **Classes**:
  - `Position`, `EntityType`, `EntityDisposition`, `Kinematics`: Core data structures
  - `TEDFHandler`: Protocol processing and validation
  - `TEDFNetworkSimulator`: Network simulation utilities
- **Features**:
  - Complete TEDF protocol implementation
  - Message serialization and validation
  - Network testing and debugging tools

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   battlespace-simulator.py                 │
│                    (Main Coordinator)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┬─────────────────────┐
    │                 │                 │                     │
┌───▼────┐    ┌──────▼──────┐    ┌─────▼─────┐    ┌─────────▼─────────┐
│entity- │    │tedf-        │    │gui-       │    │config-            │
│simulator│    │broadcaster  │    │components │    │loader             │
└───┬────┘    └──────┬──────┘    └─────┬─────┘    └─────────┬─────────┘
    │                │                 │                    │
    │                │                 │                    │
    └────────────────┼─────────────────┼────────────────────┘
                     │                 │
                ┌────▼────┐       ┌────▼────┐
                │ ZeroMQ  │       │ Azure   │
                │Port 5555│       │ GUI     │
                └─────────┘       └─────────┘
```

## 🎛️ Configuration System

### Primary Configuration (`simulator_config.json`)
```json
{
  "terrain_sync_path": "~/__terrain_sync/",
  "entity_sync_path": "~/__entity_sync/",
  "zmq_port": 5555,
  "update_rate": 30.0,
  "max_entities": 100,
  "spawn_rate": 10.0,
  "window_width": 1200,
  "window_height": 800,
  "enable_logging": true,
  "log_level": "INFO"
}
```

### Entity Database Structure
```json
{
  "version": "1.0",
  "metadata": {
    "description": "Battlespace Entity Definitions",
    "author": "Battlespace Visualization System"
  },
  "dispositions": {
    "colors": {
      "FRIENDLY": {"primary": {"hex": "#00FF00"}},
      "HOSTILE": {"primary": {"hex": "#FF0000"}},
      "NEUTRAL": {"primary": {"hex": "#FFFF00"}},
      "UNKNOWN": {"primary": {"hex": "#FFFFFF"}}
    }
  },
  "entities": [
    {
      "id": "unit_type_001",
      "name": "Fighter Jet",
      "category": "AIR",
      "subcategory": "FIGHTER",
      "kinematics": {
        "maxSpeed": 250.0,
        "movement_type": "3D_FLIGHT"
      }
    }
  ]
}
```

### File Synchronization System
- **Entity Sync**: `~/__entity_sync/entity_definitions.json`
- **Terrain Sync**: `~/__terrain_sync/terrain_boundaries.json`
- **Theme Preferences**: `.theme_preference`, `.theme_preference_editor`

## 🚀 Performance Features

### Network Optimization
- **Message Batching**: Reduces network overhead for multiple entities
- **Compression**: Compact message format for high-frequency updates
- **Priority Queuing**: Critical messages prioritized over routine updates
- **Connection Pooling**: Efficient ZeroMQ socket management

### Entity Simulation Optimization
- **Spatial Partitioning**: Efficient boundary checking and collision detection
- **Predictive Movement**: Reduces network updates through movement prediction
- **Adaptive Update Rates**: Dynamic frequency adjustment based on entity activity
- **Memory Management**: Efficient entity lifecycle with automatic cleanup

### GUI Performance
- **Lazy Loading**: Entity list updates only when visible
- **Filtered Rendering**: Display optimization for large entity counts
- **Asynchronous Updates**: Non-blocking UI updates for responsiveness
- **Theme Caching**: Preloaded Azure theme assets for smooth transitions

## 🎮 Usage Examples

### Basic Simulation Launch
```python
# Method 1: Using launcher (recommended)
python run-simulator.py

# Method 2: Direct launch with custom config
python battlespace-simulator.py --config custom_config.json

# Method 3: Entity editor for database management
python battlespace-editor.py
```

### Programmatic Integration
```python
from config_loader import ConfigurationLoader, EntityDatabaseLoader
from entity_simulator import EntitySimulator
from tedf_broadcaster import TEDFBroadcaster

# Initialize components
config_loader = ConfigurationLoader()
config_loader.load_configuration()

entity_db_loader = EntityDatabaseLoader(config_loader)
entity_db_loader.load_entity_database()

# Start simulation
simulator = EntitySimulator(terrain_bounds)
entities = entity_db_loader.get_entity_definitions()
simulator.load_entity_definitions(entities)
simulator.start_simulation()

# Start broadcasting
broadcaster = TEDFBroadcaster(port=5555)
broadcaster.start_broadcasting()
```

### Custom Entity Creation
```python
# Define custom entity type
custom_entity = {
    "id": "custom_001",
    "name": "Stealth Fighter",
    "category": "AIR",
    "subcategory": "FIGHTER",
    "specification": "STEALTH",
    "kinematics": {
        "minSpeed": 80.0,
        "maxSpeed": 300.0,
        "cruiseSpeed": 200.0,
        "acceleration": 30.0,
        "turnRate": 60.0,
        "climbRate": 20.0,
        "movement_type": "3D_FLIGHT"
    },
    "disposition_types": ["FRIENDLY", "HOSTILE"],
    "simulation_parameters": {
        "spawn_probability": 0.1,
        "max_concurrent": 5,
        "patrol_behavior": "RANDOM_WAYPOINT"
    }
}

# Add to database
entity_db_loader.add_entity_definition(custom_entity)
```

## 🔧 Advanced Configuration

### Network Tuning
```python
# High-performance setup
config = {
    "zmq_port": 5555,
    "update_rate": 60.0,        # Higher update frequency
    "batch_size": 10,           # Larger message batches
    "compression": True,        # Enable message compression
    "priority_queue": True      # Enable priority messaging
}
```

### Entity Behavior Customization
```python
# Custom patrol behavior
PATROL_BEHAVIORS = {
    "RANDOM_WAYPOINT": "Random movement within boundaries",
    "ORBITAL": "Circular movement around center point", 
    "AREA_SWEEP": "Systematic area coverage pattern",
    "PERIMETER_SCOUT": "Boundary following behavior",
    "ROAD_FOLLOWING": "Road and path following",
    "TRANSPORT_ROUTE": "Point-to-point transportation",
    "STATIC": "Stationary with heading changes"
}
```

### Debug and Monitoring
```python
# Enable comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('battlespace_simulator.log'),
        logging.StreamHandler()
    ]
)

# Performance monitoring
stats = simulator.get_statistics()
print(f"Active entities: {stats['active_entities']}")
print(f"Messages sent: {stats['messages_sent']}")
print(f"CPU usage: {stats['cpu_percent']}%")
```

## 🚨 Troubleshooting

### Common Issues

#### Port Binding Problems
```bash
# Check if port 5555 is in use
netstat -tulpn | grep 5555

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:5555)
```

#### Dependency Issues
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Check ZMQ installation
python -c "import zmq; print(f'ZMQ version: {zmq.zmq_version()}')"
```

#### Performance Issues
```python
# Reduce entity count for testing
config.max_entities = 50
config.spawn_rate = 5.0
config.update_rate = 20.0
```

### Error Codes and Solutions

| Error Code | Description | Solution |
|------------|-------------|----------|
| `CONN_001` | ZeroMQ port binding failed | Check port availability, try different port |
| `ENTITY_002` | Entity database loading failed | Verify file path and JSON syntax |
| `SIM_003` | Simulation initialization error | Check terrain boundaries and entity definitions |
| `GUI_004` | Theme loading failed | Reinstall Azure theme package |

## 📈 Performance Benchmarks

### Typical Performance Metrics
- **Entity Capacity**: 100-500 concurrent entities (depending on hardware)
- **Update Rate**: 30-60 Hz (configurable)
- **Network Throughput**: 1-10 MB/s (depending on entity count and update rate)
- **Memory Usage**: 50-200 MB (scales with entity count)
- **CPU Usage**: 10-40% (single core, varies with entity behaviors)

### Optimization Recommendations
1. **For High Entity Counts**: Reduce update rate, enable batching
2. **For Low Latency**: Increase update rate, disable batching
3. **For Memory Efficiency**: Enable entity pooling, limit concurrent entities
4. **For Network Efficiency**: Enable compression, use compact messages

---

**Dependencies**: Python 3.7+, PyZMQ, Tkinter, Matplotlib (optional)  
**Compatibility**: Windows 10+, macOS 10.15+, Ubuntu 18.04+  
**License**: Proprietary - ISD SWE © 2024