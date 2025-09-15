#!/usr/bin/env python3
"""
Battlespace Simulator Main Application
Integrates all components to provide a complete entity simulation and broadcasting system
"""

import sys
import os
import time
import threading
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import traceback
from colorama import Fore, Back, Style, init

# Import version manager
from version_manager import version_manager, print_version_banner

# Import our modules using importlib for hyphenated names
import importlib.util

# Import tedf-broadcaster
spec = importlib.util.spec_from_file_location("tedf_broadcaster", "tedf-broadcaster.py")
tedf_broadcaster_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tedf_broadcaster_module)
TEDFBroadcaster = tedf_broadcaster_module.TEDFBroadcaster
create_entity_data = tedf_broadcaster_module.create_entity_data

# Import entity-simulator
spec = importlib.util.spec_from_file_location("entity_simulator", "entity-simulator.py")
entity_simulator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entity_simulator_module)
EntitySimulator = entity_simulator_module.EntitySimulator
TerrainBounds = entity_simulator_module.TerrainBounds

# Import config-loader
spec = importlib.util.spec_from_file_location("config_loader", "config-loader.py")
config_loader_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_loader_module)
ConfigurationLoader = config_loader_module.ConfigurationLoader
EntityDatabaseLoader = config_loader_module.EntityDatabaseLoader
TerrainBoundaryLoader = config_loader_module.TerrainBoundaryLoader

# Import gui-components
spec = importlib.util.spec_from_file_location("gui_components", "gui-components.py")
gui_components_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui_components_module)
BattlespaceSimulatorGUI = gui_components_module.BattlespaceSimulatorGUI


class BattlespaceSimulator:
    """Main simulator application that coordinates all components"""
    
    def __init__(self):
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.config_loader = ConfigurationLoader()
        self.entity_db_loader = EntityDatabaseLoader(self.config_loader)
        self.terrain_loader = TerrainBoundaryLoader(self.config_loader)
        
        # Simulation components
        self.entity_simulator = None
        self.tedf_broadcaster = None
        
        # GUI
        self.gui = None
        
        # State
        self.is_running = False
        self.is_simulation_active = False
        self.is_broadcasting_active = False
        
        # Background threads
        self.update_thread = None
        self.stop_event = threading.Event()
        
        # Statistics
        self.stats = {
            "start_time": None,
            "entities_created": 0,
            "entities_destroyed": 0,
            "messages_sent": 0,
            "uptime_seconds": 0
        }
        
        self.logger.info(f"Battlespace Simulator {version_manager.full_version_string} initialized")
    
    def setup_logging(self):
        """Setup logging configuration with colorization"""
        # Initialize colorama for cross-platform color support
        init(autoreset=True)
        
        # Create custom formatter for colorized output with individual field colors
        class ColorizedFormatter(logging.Formatter):
            def format(self, record):
                # Format the timestamp
                timestamp = self.formatTime(record, self.datefmt)
                
                # Color scheme for different fields
                timestamp_color = Fore.WHITE + Style.DIM
                logger_name_color = Fore.WHITE
                level_color = self._get_level_color(record.levelno)
                message_color = self._get_message_color(record.getMessage())
                bracket_color = Fore.WHITE
                separator_color = Fore.WHITE
                
                # Build colorized log entry field by field
                colored_log = (
                    f"{timestamp_color}{timestamp}{Style.RESET_ALL}"
                    f"{separator_color} - {Style.RESET_ALL}"
                    f"{bracket_color}[{Style.RESET_ALL}"
                    f"{logger_name_color}{record.name}{Style.RESET_ALL}"
                    f"{bracket_color}]{Style.RESET_ALL}"
                    f"{separator_color} - {Style.RESET_ALL}"
                    f"{bracket_color}[{Style.RESET_ALL}"
                    f"{level_color}{record.levelname}{Style.RESET_ALL}"
                    f"{bracket_color}]{Style.RESET_ALL}"
                    f"{separator_color} - {Style.RESET_ALL}"
                    f"{message_color}{record.getMessage()}{Style.RESET_ALL}"
                )
                
                return colored_log
            
            def _get_level_color(self, level):
                """Get color for log level"""
                if level >= logging.ERROR:
                    return Fore.RED + Style.BRIGHT
                elif level >= logging.WARNING:
                    return Fore.YELLOW + Style.BRIGHT
                elif level >= logging.INFO:
                    return Fore.BLUE + Style.BRIGHT
                else:
                    return Fore.CYAN
            
            def _get_message_color(self, message):
                """Get color for message content based on keywords"""
                # Entity operations (Green family)
                if any(keyword in message for keyword in ["[MANUAL SPAWN]", "[PREFAB_DEBUG", "Entity", "spawned", "despawned"]):
                    return Fore.GREEN + Style.BRIGHT
                
                # Network/Broadcasting (Magenta family)
                elif any(keyword in message for keyword in ["Broadcasting", "ZMQ", "TEDF", "Port", "socket", "connection"]):
                    return Fore.MAGENTA + Style.BRIGHT
                
                # Configuration (Yellow family)
                elif any(keyword in message for keyword in ["Configuration", "Entity database", "Terrain", "loaded", "config"]):
                    return Fore.YELLOW + Style.BRIGHT
                
                # Simulation Control (Cyan family)
                elif any(keyword in message for keyword in ["Simulator", "initialized", "started", "stopped", "Battlespace"]):
                    return Fore.CYAN + Style.BRIGHT
                
                # Debug/Development (Light colors)
                elif any(keyword in message for keyword in ["DEBUG", "TRACE", "development"]):
                    return Fore.WHITE + Style.DIM
                
                # Statistics/Performance (Blue family)
                elif any(keyword in message for keyword in ["stats", "performance", "FPS", "rate", "count"]):
                    return Fore.BLUE
                
                # Errors in message content (even if INFO level)
                elif any(keyword in message for keyword in ["error", "failed", "exception", "Error"]):
                    return Fore.RED
                
                # Default message color
                else:
                    return Fore.WHITE
        
        # Standard format for file logging (no colors)
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Console handler with individual field colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorizedFormatter())
        
        # File handler without colors (plain text)
        file_handler = logging.FileHandler('battlespace_simulator.log')
        file_handler.setFormatter(logging.Formatter(log_format))
        
        logging.basicConfig(
            level=logging.INFO,
            handlers=[console_handler, file_handler]
        )
    
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            self.logger.info("Initializing simulator components...")
            
            # Load configuration
            self.config_loader.load_configuration()
            config = self.config_loader.config
            
            # Load entity database
            if not self.entity_db_loader.load_entity_database():
                self.logger.warning("Failed to load entity database, using defaults")
            
            # Try to load terrain boundaries
            self.terrain_loader.load_terrain_boundaries()
            
            # Initialize entity simulator
            terrain_bounds = self._get_terrain_bounds()
            self.entity_simulator = EntitySimulator(terrain_bounds)
            
            # Load entity definitions into simulator
            entity_definitions = self.entity_db_loader.get_entity_definitions()
            self.entity_simulator.load_entity_definitions(entity_definitions)
            
            # Configure simulation parameters
            self.entity_simulator.max_entities = config.max_entities
            self.entity_simulator.spawn_rate = config.spawn_rate
            self.entity_simulator.update_rate = config.update_rate
            
            # Initialize TEDF broadcaster
            self.tedf_broadcaster = TEDFBroadcaster(
                port=config.zmq_port,
                update_rate=config.update_rate
            )
            
            # Initialize GUI
            self.gui = BattlespaceSimulatorGUI()
            self._setup_gui_callbacks()
            
            # Initialize GUI with current data
            self._update_gui_info()
            
            self.logger.info("Simulator initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize simulator: {e}")
            self.logger.debug(traceback.format_exc())
            return False
    
    def _get_terrain_bounds(self) -> TerrainBounds:
        """Get terrain boundaries from loaded data or defaults"""
        terrain_data = self.terrain_loader.get_terrain_bounds()
        
        if terrain_data:
            return TerrainBounds(
                min_x=terrain_data["min_x"],
                max_x=terrain_data["max_x"],
                min_z=terrain_data["min_z"],
                max_z=terrain_data["max_z"],
                min_y=terrain_data["min_y"],
                max_y=terrain_data["max_y"]
            )
        else:
            # Default bounds
            return TerrainBounds(
                min_x=-5000.0, max_x=5000.0,
                min_z=-5000.0, max_z=5000.0,
                min_y=0.0, max_y=1000.0
            )
    
    def _setup_gui_callbacks(self):
        """Setup GUI event callbacks"""
        callbacks = {
            "load_terrain": self.load_terrain_data,
            "reload_entities": self.reload_entity_database,
            "set_manual_boundaries": self.set_manual_boundaries,
            "start_simulation": self.start_simulation,
            "stop_simulation": self.stop_simulation,
            "clear_entities": self.clear_all_entities,
            "refresh_statistics": self.refresh_gui_statistics,
            "refresh_entities": self.refresh_gui_entities,
            "load_config": self.load_configuration,
            "save_config": self.save_configuration,
            "export_stats": self.export_statistics,
            "speed_multiplier_changed": self.set_speed_multiplier,
            "spawn_entities": self.spawn_entities_manually,
            "spawn_random_entities": self.spawn_random_entities
        }
        
        for event_name, callback in callbacks.items():
            self.gui.set_callback(event_name, callback)
    
    def _update_gui_info(self):
        """Update GUI with current information"""
        if not self.gui:
            return
        
        # Update terrain info
        terrain_info = self.terrain_loader.get_terrain_info()
        if terrain_info["loaded"]:
            terrain_text = f"Loaded: {terrain_info['terrain_count']} terrain(s), bounds: {terrain_info['boundaries']}"
        else:
            terrain_text = "No terrain data loaded (using defaults)"
        
        self.gui.control_frame.update_terrain_info(terrain_text)
        
        # Update entity database info
        db_info = self.entity_db_loader.get_database_info()
        db_text = f"Loaded: {db_info['entity_count']} entities, {len(db_info['categories'])} categories"
        self.gui.control_frame.update_entity_db_info(db_text)
        
        # Update imported entities list
        entity_definitions = self.entity_db_loader.get_entity_definitions()
        if entity_definitions:
            # Convert dict of entity definitions to list for GUI display
            entity_list = list(entity_definitions.values())
            self.gui.control_frame.update_imported_entities_list(entity_list)
            
            # Populate entity types for manual spawning
            self.gui.control_frame.populate_entity_types(entity_list)
        
        # Update configuration paths
        config = self.config_loader.config
        # Set terrain path to the actual boundaries file
        terrain_boundaries_file = os.path.join(config.terrain_sync_path, "terrain_boundaries.json")
        self.gui.control_frame.terrain_path_var.set(terrain_boundaries_file)
        self.gui.control_frame.entity_db_path_var.set(
            os.path.join(config.entity_sync_path, "entity_sync.json")
        )
    
    def start_simulation(self, params: Dict[str, Any]):
        """Start the simulation with given parameters"""
        try:
            if self.is_simulation_active:
                self.logger.warning("Simulation is already active")
                return
            
            self.logger.info(f"Starting simulation with parameters: {params}")
            
            # Update configuration
            self.entity_simulator.max_entities = params["max_entities"]
            self.entity_simulator.spawn_rate = params["spawn_rate"]
            self.entity_simulator.update_rate = params["update_rate"]
            
            # Update broadcaster settings
            self.tedf_broadcaster.port = params["zmq_port"]
            self.tedf_broadcaster.update_rate = params["broadcast_rate"]
            
            # Start broadcasting
            if not self.tedf_broadcaster.start_broadcasting():
                raise Exception("Failed to start TEDF broadcasting")
            
            self.is_broadcasting_active = True
            
            # Start entity simulation
            if not self.entity_simulator.start_simulation():
                raise Exception("Failed to start entity simulation")
            
            self.is_simulation_active = True
            
            # Start update thread
            self.stop_event.clear()
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            self.stats["start_time"] = time.time()
            self.is_running = True
            
            self.gui.update_status("Simulation running")
            self.logger.info("Simulation started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            self.gui.update_status(f"Failed to start: {e}")
            self.stop_simulation()
    
    def stop_simulation(self):
        """Stop the simulation"""
        try:
            self.logger.info("Stopping simulation...")
            
            self.is_running = False
            self.stop_event.set()
            
            # FIRST: Wait for update thread to finish BEFORE touching broadcaster
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=10.0)
                if self.update_thread.is_alive():
                    self.logger.warning("Update thread did not terminate gracefully")
            
            # Stop entity simulation
            if self.entity_simulator:
                try:
                    self.entity_simulator.stop_simulation()
                except Exception as e:
                    self.logger.error(f"Error stopping entity simulator: {e}")
            self.is_simulation_active = False
            
            # Stop broadcasting (use stop_broadcasting, not cleanup to avoid double context termination)
            if self.tedf_broadcaster:
                try:
                    self.tedf_broadcaster.stop_broadcasting()
                except Exception as e:
                    self.logger.error(f"Error stopping broadcaster: {e}")
            self.is_broadcasting_active = False
            
            if self.gui:
                self.gui.update_status("Simulation stopped")
            self.logger.info("Simulation stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping simulation: {e}")
    
    def _update_loop(self):
        """Main update loop for message generation and broadcasting"""
        last_full_update = 0
        last_compact_update = 0
        full_update_interval = 30.0  # Full updates every 30 seconds
        compact_update_interval = 2.0  # Compact updates every 2 seconds
        
        while not self.stop_event.wait(0.1):
            try:
                current_time = time.time()
                
                # Send full updates
                if current_time - last_full_update >= full_update_interval:
                    entities_for_full = self.entity_simulator.get_entities_for_update("full")
                    for entity_data in entities_for_full:
                        self.tedf_broadcaster.queue_full_message(entity_data)
                    last_full_update = current_time
                
                # Send compact updates
                if current_time - last_compact_update >= compact_update_interval:
                    entities_for_compact = self.entity_simulator.get_entities_for_update("compact")
                    
                    # Send as batch if multiple entities
                    if len(entities_for_compact) > 5:
                        self.tedf_broadcaster.queue_batch_message(entities_for_compact)
                    else:
                        for entity_data in entities_for_compact:
                            self.tedf_broadcaster.queue_compact_message(entity_data)
                    
                    last_compact_update = current_time
                
                # Handle despawned entities
                despawned_entities = self.entity_simulator.get_despawned_entities()
                for entity_id in despawned_entities:
                    self.tedf_broadcaster.queue_despawn_message(entity_id, "SIMULATION_ENDED")
                
                # Update statistics
                self._update_statistics()
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
    
    def _update_statistics(self):
        """Update simulation statistics"""
        if self.stats["start_time"]:
            self.stats["uptime_seconds"] = time.time() - self.stats["start_time"]
        
        # Get statistics from components
        if self.entity_simulator:
            sim_stats = self.entity_simulator.get_statistics()
            self.stats["entities_created"] = sim_stats.get("entities_spawned", 0)
            self.stats["entities_destroyed"] = sim_stats.get("entities_despawned", 0)
        
        if self.tedf_broadcaster:
            broadcast_stats = self.tedf_broadcaster.get_statistics()
            self.stats["messages_sent"] = broadcast_stats.get("messages_sent", 0)
    
    def clear_all_entities(self):
        """Clear all entities from simulation"""
        if self.entity_simulator:
            # Get all active entities before clearing
            entities = list(self.entity_simulator.entities.keys())
            
            # Send despawn messages
            for entity_id in entities:
                if self.tedf_broadcaster:
                    self.tedf_broadcaster.queue_despawn_message(entity_id, "MANUAL_CLEAR")
            
            # Clear from simulator
            self.entity_simulator.entities.clear()
            
            self.logger.info(f"Cleared {len(entities)} entities")
            self.gui.update_status(f"Cleared {len(entities)} entities")
    
    def load_terrain_data(self, path: str):
        """Load terrain data from specified path"""
        try:
            if self.terrain_loader.load_terrain_boundaries(path):
                # Update entity simulator with new bounds
                terrain_bounds = self._get_terrain_bounds()
                self.entity_simulator.set_terrain_bounds(terrain_bounds)
                
                self._update_gui_info()
                self.gui.update_status("Terrain data loaded")
                self.logger.info(f"Terrain data loaded from: {path}")
            else:
                self.gui.update_status("Failed to load terrain data")
        except Exception as e:
            self.logger.error(f"Error loading terrain data: {e}")
            self.gui.update_status(f"Error loading terrain: {e}")
    
    def reload_entity_database(self, path: str = None):
        """Reload entity database"""
        try:
            if self.entity_db_loader.load_entity_database(path):
                # Update entity simulator with new definitions
                entity_definitions = self.entity_db_loader.get_entity_definitions()
                self.entity_simulator.load_entity_definitions(entity_definitions)
                
                self._update_gui_info()
                self.gui.update_status("Entity database reloaded")
                self.logger.info("Entity database reloaded")
            else:
                self.gui.update_status("Failed to reload entity database")
        except Exception as e:
            self.logger.error(f"Error reloading entity database: {e}")
            self.gui.update_status(f"Error reloading database: {e}")
    
    def set_manual_boundaries(self, boundaries: Dict[str, float]):
        """Set manual terrain boundaries"""
        try:
            terrain_bounds = TerrainBounds(
                min_x=boundaries["min_x"],
                max_x=boundaries["max_x"],
                min_z=boundaries["min_z"],
                max_z=boundaries["max_z"],
                min_y=boundaries["min_y"],
                max_y=boundaries["max_y"]
            )
            
            self.entity_simulator.set_terrain_bounds(terrain_bounds)
            self.gui.update_status("Manual boundaries applied")
            self.logger.info(f"Manual boundaries set: {boundaries}")
            
        except Exception as e:
            self.logger.error(f"Error setting manual boundaries: {e}")
            self.gui.update_status(f"Error setting boundaries: {e}")
    
    def set_speed_multiplier(self, multiplier: float):
        """Set global speed multiplier for all entities"""
        try:
            if self.entity_simulator:
                self.entity_simulator.set_speed_multiplier(multiplier)
                self.logger.info(f"Speed multiplier set to {multiplier:.2f}")
                if self.gui:
                    self.gui.update_status(f"Speed multiplier: {multiplier:.2f}x")
            else:
                self.logger.warning("Entity simulator not initialized")
                
        except Exception as e:
            self.logger.error(f"Error setting speed multiplier: {e}")
            if self.gui:
                self.gui.update_status(f"Error setting speed multiplier: {e}")
    
    def refresh_gui_entities(self):
        """Refresh entity display in GUI"""
        if self.entity_simulator and self.gui:
            # Convert simulator entities to GUI format
            gui_entities = {}
            
            for entity_id, sim_entity in self.entity_simulator.entities.items():
                gui_entities[entity_id] = self.entity_simulator._entity_to_dict(sim_entity)
            
            self.gui.update_entities(gui_entities)
    
    def spawn_entities_manually(self, entity_type_display: str, disposition: str, count: int):
        """Manually spawn entities of specified type"""
        try:
            if not self.entity_simulator:
                raise Exception("Entity simulator not initialized")
            
            if not self.tedf_broadcaster:
                raise Exception("TEDF broadcaster not initialized")
            
            # Parse entity type from display string (format: "Name (Category)")
            if "(" in entity_type_display and ")" in entity_type_display:
                entity_name = entity_type_display.split(" (")[0]
                category = entity_type_display.split("(")[1].split(")")[0]
            else:
                entity_name = entity_type_display
                category = "UNKNOWN"
            
            # Find matching entity definition
            entity_definitions = self.entity_db_loader.get_entity_definitions()
            matching_entity = None
            
            self.logger.info(f"[MANUAL SPAWN] Attempting to spawn: {entity_type_display}")
            self.logger.info(f"[MANUAL SPAWN] Parsed - Name: '{entity_name}', Category: '{category}'")
            
            # First, try exact name match
            for entity_def in entity_definitions.values():
                entity_display_name = entity_def.get('displayName', entity_def.get('name', ''))
                if entity_display_name == entity_name:
                    matching_entity = entity_def
                    self.logger.info(f"[MANUAL SPAWN] Exact name match found: {entity_def.get('name', 'Unknown')}")
                    break
            
            # If no exact match, try name and category combination
            if not matching_entity:
                for entity_def in entity_definitions.values():
                    entity_display_name = entity_def.get('displayName', entity_def.get('name', ''))
                    entity_category = entity_def.get('category', '')
                    if entity_display_name == entity_name and entity_category == category:
                        matching_entity = entity_def
                        self.logger.info(f"[MANUAL SPAWN] Name+Category match found: {entity_def.get('name', 'Unknown')}")
                        break
            
            if not matching_entity:
                available_entities = [f"{e.get('name', 'Unknown')} ({e.get('category', 'Unknown')})" 
                                     for e in entity_definitions.values()]
                error_msg = f"No entity definition found for: {entity_type_display}\nAvailable entities: {', '.join(available_entities[:5])}..."
                self.logger.error(f"[MANUAL SPAWN] {error_msg}")
                raise Exception(error_msg)
            
            # Get terrain bounds for spawning
            bounds_dict = self.terrain_loader.get_terrain_bounds()
            if not bounds_dict:
                # Default bounds if no terrain loaded
                bounds_dict = {
                    "min_x": -1000.0, "max_x": 1000.0,
                    "min_z": -1000.0, "max_z": 1000.0,
                    "min_y": 0.0, "max_y": 500.0
                }
            
            spawned_count = 0
            for i in range(count):
                try:
                    # Generate random position within bounds
                    import random
                    x = random.uniform(bounds_dict["min_x"], bounds_dict["max_x"])
                    z = random.uniform(bounds_dict["min_z"], bounds_dict["max_z"])
                    y = random.uniform(bounds_dict["min_y"], bounds_dict["max_y"])
                    
                    # Create entity in simulator
                    entity_id = f"MANUAL_{matching_entity.get('id', 'UNK')}_{int(time.time() * 1000)}_{i}"
                    
                    self.logger.info(f"[MANUAL SPAWN] Creating entity: {entity_id}")
                    self.logger.info(f"[MANUAL SPAWN] Entity Model: {matching_entity.get('model', 'None')}")
                    self.logger.info(f"[MANUAL SPAWN] Position: ({x:.1f}, {y:.1f}, {z:.1f})")
                    self.logger.info(f"[MANUAL SPAWN] Disposition: {disposition}")
                    
                    # Use entity simulator to create the entity
                    if self.entity_simulator.spawn_entity_at_position(
                        entity_id=entity_id,
                        entity_type=matching_entity,
                        position=(x, y, z),
                        disposition=disposition
                    ):
                        spawned_count += 1
                        self.stats["entities_created"] += 1
                        self.logger.info(f"[MANUAL SPAWN] Successfully spawned: {entity_id}")
                    else:
                        self.logger.error(f"[MANUAL SPAWN] Failed to spawn entity: {entity_id}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to spawn entity {i+1}: {e}")
                    continue
            
            # Update GUI and log results
            self.gui.update_status(f"Spawned {spawned_count}/{count} {entity_name} entities")
            self.logger.info(f"Manually spawned {spawned_count} {entity_name} entities")
            
            # Refresh entity display
            self.refresh_gui_entities()
            
        except Exception as e:
            error_msg = f"Failed to spawn entities: {e}"
            self.logger.error(error_msg)
            if self.gui:
                self.gui.update_status(error_msg)
    
    def spawn_random_entities(self, count: int):
        """Spawn random entities using the entity simulator"""
        try:
            if not self.entity_simulator:
                raise Exception("Entity simulator not initialized")
            
            spawned_count = self.entity_simulator.spawn_random_entities(count)
            
            # Update GUI and log results
            self.gui.update_status(f"Spawned {spawned_count}/{count} random entities")
            self.logger.info(f"Spawned {spawned_count} random entities")
            
            # Refresh entity display
            self.refresh_gui_entities()
            
        except Exception as e:
            error_msg = f"Failed to spawn random entities: {e}"
            self.logger.error(error_msg)
            if self.gui:
                self.gui.update_status(error_msg)
    
    def refresh_gui_statistics(self):
        """Refresh statistics display in GUI"""
        if not self.gui:
            return
        
        stats_text = self._format_statistics()
        self.gui.control_frame.update_statistics(stats_text)
    
    def _format_statistics(self) -> str:
        """Format statistics for display"""
        lines = [
            "=== Battlespace Simulator Statistics ===",
            f"Simulation Status: {'Running' if self.is_running else 'Stopped'}",
            f"Broadcasting Status: {'Active' if self.is_broadcasting_active else 'Inactive'}",
            ""
        ]
        
        if self.stats["start_time"]:
            uptime = time.time() - self.stats["start_time"]
            lines.append(f"Uptime: {uptime:.1f} seconds")
        
        lines.extend([
            f"Entities Created: {self.stats['entities_created']}",
            f"Entities Destroyed: {self.stats['entities_destroyed']}",
            f"Messages Sent: {self.stats['messages_sent']}",
            ""
        ])
        
        if self.entity_simulator:
            sim_stats = self.entity_simulator.get_statistics()
            lines.extend([
                "=== Entity Simulation ===",
                f"Active Entities: {sim_stats.get('active_entities', 0)}",
                f"Simulation Time: {sim_stats.get('simulation_time', 0):.1f}s",
                ""
            ])
            
            # Entity type breakdown
            type_counts = self.entity_simulator.get_entity_count_by_type()
            if type_counts:
                lines.append("Entity Types:")
                for entity_type, count in type_counts.items():
                    lines.append(f"  {entity_type}: {count}")
                lines.append("")
        
        if self.tedf_broadcaster:
            broadcast_stats = self.tedf_broadcaster.get_statistics()
            lines.extend([
                "=== TEDF Broadcasting ===",
                f"Total Messages: {broadcast_stats.get('messages_sent', 0)}",
                f"Full Messages: {broadcast_stats.get('full_messages_sent', 0)}",
                f"Compact Messages: {broadcast_stats.get('compact_messages_sent', 0)}",
                f"Batch Messages: {broadcast_stats.get('batch_messages_sent', 0)}",
                f"Despawn Messages: {broadcast_stats.get('despawn_messages_sent', 0)}",
                f"Errors: {broadcast_stats.get('errors', 0)}",
                f"Messages/sec: {broadcast_stats.get('messages_per_second', 0):.1f}",
                ""
            ])
        
        lines.append(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        return "\n".join(lines)
    
    def load_configuration_file(self, filename: str):
        """Load configuration from file"""
        try:
            # Save current config file and load new one
            self.config_loader.config_file = filename
            self.config_loader.load_configuration()
            
            self._update_gui_info()
            self.gui.update_status(f"Configuration loaded: {filename}")
            self.logger.info(f"Configuration loaded from: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.gui.update_status(f"Error loading config: {e}")
    
    def save_configuration_file(self, filename: str):
        """Save configuration to file"""
        try:
            # Update config with GUI values
            params = self.gui.control_frame.get_simulation_params()
            
            self.config_loader.update_configuration(
                max_entities=params["max_entities"],
                spawn_rate=params["spawn_rate"],
                update_rate=params["update_rate"],
                zmq_port=params["zmq_port"]
            )
            
            # Save to specified file
            original_file = self.config_loader.config_file
            self.config_loader.config_file = filename
            self.config_loader.save_configuration()
            self.config_loader.config_file = original_file
            
            self.gui.update_status(f"Configuration saved: {filename}")
            self.logger.info(f"Configuration saved to: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            self.gui.update_status(f"Error saving config: {e}")
    
    def export_statistics(self, filename: str):
        """Export statistics to file"""
        try:
            stats_text = self._format_statistics()
            
            with open(filename, 'w') as f:
                f.write(stats_text)
            
            self.gui.update_status(f"Statistics exported: {filename}")
            self.logger.info(f"Statistics exported to: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting statistics: {e}")
            self.gui.update_status(f"Error exporting stats: {e}")
    
    def save_configuration(self, filename: str):
        """Save current simulator configuration to sidecar file"""
        try:
            config_data = {
                "version": "1.0",
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "simulator_version": "1.2.1",
                    "description": "Battlespace Simulator Configuration"
                },
                "simulation_parameters": {
                    "max_entities": self.gui.max_entities_var.get() if self.gui else 100,
                    "spawn_rate": self.gui.spawn_rate_var.get() if self.gui else 10.0,
                    "update_rate": self.gui.update_rate_var.get() if self.gui else 30.0,
                    "broadcast_rate": self.gui.broadcast_rate_var.get() if self.gui else 2.0,
                    "zmq_port": self.gui.port_var.get() if self.gui else 5555
                },
                "entity_database": {
                    "path": self.entity_db_loader.get_current_path(),
                    "count": len(self.entity_db_loader.get_entity_definitions())
                },
                "terrain_boundaries": {
                    "path": self.terrain_loader.get_current_path(),
                    "bounds": self.terrain_loader.get_terrain_bounds()
                },
                "gui_settings": {
                    "theme": self.gui.current_theme if self.gui else "dark",
                    "auto_scroll": self.gui.auto_scroll_var.get() if self.gui else True
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.gui.update_status(f"Configuration saved: {filename}")
            self.logger.info(f"Configuration saved to: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            self.gui.update_status(f"Error saving config: {e}")
    
    def load_configuration(self, filename: str):
        """Load simulator configuration from sidecar file"""
        try:
            with open(filename, 'r') as f:
                config_data = json.load(f)
            
            # Validate configuration format
            if config_data.get("version") != "1.0":
                raise ValueError(f"Unsupported configuration version: {config_data.get('version')}")
            
            # Apply simulation parameters
            sim_params = config_data.get("simulation_parameters", {})
            if self.gui:
                self.gui.max_entities_var.set(sim_params.get("max_entities", 100))
                self.gui.spawn_rate_var.set(sim_params.get("spawn_rate", 10.0))
                self.gui.update_rate_var.set(sim_params.get("update_rate", 30.0))
                self.gui.broadcast_rate_var.set(sim_params.get("broadcast_rate", 2.0))
                self.gui.port_var.set(sim_params.get("zmq_port", 5555))
            
            # Apply GUI settings
            gui_settings = config_data.get("gui_settings", {})
            if self.gui:
                theme = gui_settings.get("theme", "dark")
                if theme != self.gui.current_theme:
                    self.gui.toggle_theme()
                
                self.gui.auto_scroll_var.set(gui_settings.get("auto_scroll", True))
            
            # Load entity database if path exists
            entity_db = config_data.get("entity_database", {})
            entity_db_path = entity_db.get("path")
            if entity_db_path and os.path.exists(entity_db_path):
                try:
                    self.entity_db_loader.load_entity_database(entity_db_path)
                    self.entity_simulator.load_entity_definitions(self.entity_db_loader.get_entity_definitions())
                    self.logger.info(f"Loaded entity database: {entity_db_path}")
                except Exception as e:
                    self.logger.warning(f"Could not load entity database from config: {e}")
            
            # Load terrain boundaries if path exists
            terrain_data = config_data.get("terrain_boundaries", {})
            terrain_path = terrain_data.get("path")
            if terrain_path and os.path.exists(terrain_path):
                try:
                    self.terrain_loader.load_terrain_boundaries(terrain_path)
                    self.logger.info(f"Loaded terrain boundaries: {terrain_path}")
                except Exception as e:
                    self.logger.warning(f"Could not load terrain boundaries from config: {e}")
            
            # Update GUI with loaded information
            if self.gui:
                config_info = f"Config loaded: {config_data.get('metadata', {}).get('description', 'Unknown')}"
                self.gui.update_status(config_info)
                
                # Update entity and terrain info displays
                entity_count = len(self.entity_db_loader.get_entity_definitions())
                self.gui.update_entity_info(f"Entities loaded: {entity_count}")
                
                bounds = self.terrain_loader.get_terrain_bounds()
                if bounds:
                    terrain_info = f"Terrain: {bounds.get('min_x', 0):.0f},{bounds.get('min_z', 0):.0f} to {bounds.get('max_x', 0):.0f},{bounds.get('max_z', 0):.0f}"
                    self.gui.update_terrain_info(terrain_info)
            
            self.logger.info(f"Configuration loaded from: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            if self.gui:
                self.gui.update_status(f"Error loading config: {e}")
    
    def run(self):
        """Run the main application"""
        try:
            if not self.initialize():
                self.logger.error("Failed to initialize simulator")
                return False
            
            self.logger.info("Starting Battlespace Simulator GUI...")
            self.gui.run()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.logger.debug(traceback.format_exc())
        finally:
            try:
                self.shutdown()
            except Exception as shutdown_error:
                self.logger.error(f"Error during final shutdown: {shutdown_error}")
    
    def shutdown(self):
        """Clean shutdown of all components"""
        self.logger.info("Shutting down simulator...")
        
        try:
            # Stop simulation first
            self.stop_simulation()
            
            # Cleanup TEDF broadcaster explicitly
            if self.tedf_broadcaster:
                try:
                    self.tedf_broadcaster.cleanup()
                    self.tedf_broadcaster = None
                except Exception as e:
                    self.logger.error(f"Error cleaning up broadcaster during shutdown: {e}")
            
            # Cleanup GUI
            if self.gui:
                try:
                    self.gui.destroy()
                except Exception as e:
                    self.logger.error(f"Error destroying GUI: {e}")
            
            self.logger.info("Simulator shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    print_version_banner()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        return 1
    
    # Create and run simulator
    simulator = BattlespaceSimulator()
    
    try:
        success = simulator.run()
        return 0 if success else 1
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}")
        logging.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())