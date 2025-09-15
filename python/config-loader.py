"""
Configuration and Entity Database Loader
Handles loading and managing configuration files and entity definitions
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import shutil


@dataclass
class SimulatorConfiguration:
    # Paths
    terrain_sync_path: str = "~/__terrain_sync/"
    entity_sync_path: str = "~/__entity_sync/"
    
    # Network Configuration
    zmq_port: int = 5555
    zmq_address: str = "tcp://localhost"
    zmq_protocol: str = "tcp"
    zmq_bind_interface: str = "*"
    zmq_connection_timeout: int = 5000
    zmq_max_queue_size: int = 1000
    
    # Broadcasting Configuration
    broadcast_enabled: bool = True
    broadcast_full_interval: float = 30.0
    broadcast_compact_interval: float = 2.0
    broadcast_batch_size: int = 10
    update_rate: float = 2.0
    
    # Network Timeouts and Limits
    connection_retry_count: int = 3
    connection_retry_delay: float = 1.0
    heartbeat_interval: float = 10.0
    heartbeat_timeout: float = 30.0
    
    # Network Security
    enable_authentication: bool = False
    auth_key: str = ""
    enable_encryption: bool = False
    encryption_key: str = ""
    
    # Simulation
    max_entities: int = 20
    spawn_rate: float = 1.0
    
    # GUI
    window_width: int = 1200
    window_height: int = 800
    auto_refresh_interval: int = 5000  # milliseconds
    
    # Debug
    enable_logging: bool = True
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: str = "simulator.log"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulatorConfiguration':
        return cls(**data)


class ConfigurationLoader:
    """Handles loading and saving simulator configuration"""
    
    def __init__(self, config_file: str = "simulator_config.json"):
        self.config_file = config_file
        self.config: SimulatorConfiguration = SimulatorConfiguration()
        self.logger = logging.getLogger(__name__)
    
    def load_configuration(self) -> SimulatorConfiguration:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.config = SimulatorConfiguration.from_dict(config_data)
                    self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.info("No configuration file found, using defaults")
                self.save_configuration()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = SimulatorConfiguration()
        
        # Expand paths
        self.config.terrain_sync_path = os.path.expanduser(self.config.terrain_sync_path)
        self.config.entity_sync_path = os.path.expanduser(self.config.entity_sync_path)
        
        return self.config
    
    def save_configuration(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
                self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def update_configuration(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.debug(f"Updated config: {key} = {value}")
    
    def get_expanded_path(self, path_key: str) -> str:
        """Get expanded path for a configuration key"""
        path = getattr(self.config, path_key, "")
        return os.path.expanduser(path)


class EntityDatabaseLoader:
    """Handles loading and managing entity definition database"""
    
    def __init__(self, config_loader: ConfigurationLoader):
        self.config_loader = config_loader
        self.entity_database: Dict[str, Any] = {}
        self.entity_definitions: Dict[str, Dict[str, Any]] = {}
        self.disposition_colors: Dict[str, Dict[str, Any]] = {}
        self.current_path: str = ""
        self.logger = logging.getLogger(__name__)
    
    def load_entity_database(self, custom_path: Optional[str] = None) -> bool:
        """Load entity database from JSON file"""
        if custom_path:
            database_path = custom_path
        else:
            entity_sync_path = self.config_loader.get_expanded_path("entity_sync_path")
            database_path = os.path.join(entity_sync_path, "entity_sync.json")
        
        try:
            if not os.path.exists(database_path):
                self.logger.warning(f"Entity database not found at: {database_path}")
                self._create_default_database(database_path)
                # Now try to load the newly created database
                if not os.path.exists(database_path):
                    return False
            
            with open(database_path, 'r') as f:
                self.entity_database = json.load(f)
            
            # Extract entity definitions
            self.entity_definitions = {}
            if "entities" in self.entity_database:
                for entity in self.entity_database["entities"]:
                    entity_id = entity.get("id")
                    if entity_id:
                        self.entity_definitions[entity_id] = entity
            
            # Extract disposition colors
            self.disposition_colors = self.entity_database.get("dispositions", {}).get("colors", {})
            
            # Store current path for configuration saving
            self.current_path = database_path
            
            self.logger.info(f"Loaded entity database with {len(self.entity_definitions)} definitions from {database_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load entity database: {e}")
            return False
    
    def _create_default_database(self, database_path: str):
        """Create a default entity database if none exists"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(database_path), exist_ok=True)
            
            default_database = self._get_default_database()
            
            with open(database_path, 'w') as f:
                json.dump(default_database, f, indent=2)
            
            self.logger.info(f"Created default entity database at {database_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create default database: {e}")
    
    def _get_default_database(self) -> Dict[str, Any]:
        """Get default entity database structure"""
        return {
            "version": "1.0",
            "metadata": {
                "description": "Default Battlespace Entity Definitions",
                "created": "auto-generated",
                "author": "Battlespace Simulator"
            },
            "dispositions": {
                "colors": {
                    "FRIENDLY": {
                        "primary": {"hex": "#00FF00", "rgb": [0, 255, 0]},
                        "secondary": {"hex": "#66FF66", "rgb": [102, 255, 102]},
                        "gizmo": {"hex": "#00CC00", "rgb": [0, 204, 0]}
                    },
                    "HOSTILE": {
                        "primary": {"hex": "#FF0000", "rgb": [255, 0, 0]},
                        "secondary": {"hex": "#FF6666", "rgb": [255, 102, 102]},
                        "gizmo": {"hex": "#CC0000", "rgb": [204, 0, 0]}
                    },
                    "NEUTRAL": {
                        "primary": {"hex": "#FFFF00", "rgb": [255, 255, 0]},
                        "secondary": {"hex": "#FFFF66", "rgb": [255, 255, 102]},
                        "gizmo": {"hex": "#CCCC00", "rgb": [204, 204, 0]}
                    },
                    "UNKNOWN": {
                        "primary": {"hex": "#FFFFFF", "rgb": [255, 255, 255]},
                        "secondary": {"hex": "#CCCCCC", "rgb": [204, 204, 204]},
                        "gizmo": {"hex": "#999999", "rgb": [153, 153, 153]}
                    }
                },
                "symbols": {
                    "FRIENDLY": "F",
                    "HOSTILE": "H",
                    "NEUTRAL": "N",
                    "UNKNOWN": "U"
                }
            },
            "entity_categories": {
                "AIR": {
                    "description": "Aerial vehicles and aircraft",
                    "default_altitude": 500.0,
                    "movement_layer": "air_space"
                },
                "GROUND": {
                    "description": "Ground-based vehicles and personnel",
                    "default_altitude": 0.0,
                    "movement_layer": "terrain_surface"
                }
            },
            "entities": [
                {
                    "id": "unit_type_001",
                    "name": "Fighter Jet",
                    "description": "Multi-role fighter aircraft",
                    "category": "AIR",
                    "subcategory": "FIGHTER",
                    "specification": "MULTIROLE",
                    "kinematics": {
                        "minSpeed": 50.0,
                        "maxSpeed": 250.0,
                        "cruiseSpeed": 150.0,
                        "acceleration": 25.0,
                        "turnRate": 45.0,
                        "climbRate": 15.0,
                        "defaultAltitude": 500.0,
                        "movement_type": "3D_FLIGHT"
                    },
                    "disposition_types": ["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"],
                    "simulation_parameters": {
                        "spawn_probability": 0.15,
                        "max_concurrent": 8,
                        "patrol_behavior": "RANDOM_WAYPOINT"
                    }
                },
                {
                    "id": "unit_type_002",
                    "name": "Main Battle Tank",
                    "description": "Heavy armored ground vehicle",
                    "category": "GROUND",
                    "subcategory": "VEHICLE",
                    "specification": "TRACKED_MBT",
                    "kinematics": {
                        "minSpeed": 0.0,
                        "maxSpeed": 35.0,
                        "cruiseSpeed": 20.0,
                        "acceleration": 3.5,
                        "turnRate": 25.0,
                        "movement_type": "GROUND_TRACKED"
                    },
                    "disposition_types": ["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"],
                    "simulation_parameters": {
                        "spawn_probability": 0.25,
                        "max_concurrent": 15,
                        "patrol_behavior": "ROAD_FOLLOWING"
                    }
                },
                {
                    "id": "unit_type_003",
                    "name": "Infantry Squad",
                    "description": "Dismounted infantry unit",
                    "category": "GROUND",
                    "subcategory": "INFANTRY",
                    "specification": "DISMOUNTED",
                    "kinematics": {
                        "minSpeed": 0.0,
                        "maxSpeed": 5.0,
                        "cruiseSpeed": 2.5,
                        "acceleration": 1.0,
                        "turnRate": 90.0,
                        "movement_type": "GROUND_FOOT"
                    },
                    "disposition_types": ["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"],
                    "simulation_parameters": {
                        "spawn_probability": 0.35,
                        "max_concurrent": 25,
                        "patrol_behavior": "AREA_SWEEP"
                    }
                }
            ]
        }
    
    def get_entity_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all entity definitions"""
        return self.entity_definitions.copy()
    
    def get_entity_definition(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get specific entity definition"""
        return self.entity_definitions.get(entity_id)
    
    def get_entity_categories(self) -> List[str]:
        """Get list of entity categories"""
        categories = set()
        for entity in self.entity_definitions.values():
            category = entity.get("category")
            if category:
                categories.add(category)
        return sorted(list(categories))
    
    def get_entities_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get entities filtered by category"""
        return {
            entity_id: entity for entity_id, entity in self.entity_definitions.items()
            if entity.get("category") == category
        }
    
    def get_disposition_color(self, disposition: str, color_type: str = "primary") -> Tuple[int, int, int]:
        """Get RGB color for disposition"""
        try:
            disposition_colors = self.disposition_colors.get(disposition.upper(), {})
            color_data = disposition_colors.get(color_type, {})
            rgb = color_data.get("rgb", [255, 255, 255])
            return tuple(rgb)
        except Exception:
            # Default colors
            defaults = {
                "FRIENDLY": (0, 255, 0),
                "HOSTILE": (255, 0, 0),
                "NEUTRAL": (255, 255, 0),
                "UNKNOWN": (255, 255, 255)
            }
            return defaults.get(disposition.upper(), (255, 255, 255))
    
    def get_disposition_hex(self, disposition: str, color_type: str = "primary") -> str:
        """Get hex color for disposition"""
        try:
            disposition_colors = self.disposition_colors.get(disposition.upper(), {})
            color_data = disposition_colors.get(color_type, {})
            return color_data.get("hex", "#FFFFFF")
        except Exception:
            # Default colors
            defaults = {
                "FRIENDLY": "#00FF00",
                "HOSTILE": "#FF0000",
                "NEUTRAL": "#FFFF00",
                "UNKNOWN": "#FFFFFF"
            }
            return defaults.get(disposition.upper(), "#FFFFFF")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database metadata and summary"""
        info = {
            "version": self.entity_database.get("version", "unknown"),
            "metadata": self.entity_database.get("metadata", {}),
            "entity_count": len(self.entity_definitions),
            "categories": self.get_entity_categories(),
            "dispositions": list(self.disposition_colors.keys()) if self.disposition_colors else []
        }
        
        # Add category counts
        category_counts = {}
        for entity in self.entity_definitions.values():
            category = entity.get("category", "UNKNOWN")
            category_counts[category] = category_counts.get(category, 0) + 1
        info["category_counts"] = category_counts
        
        return info
    
    def get_current_path(self) -> str:
        """Get the current entity database file path"""
        return self.current_path
    
    def validate_database(self) -> Tuple[bool, List[str]]:
        """Validate entity database for completeness and correctness"""
        errors = []
        
        # Check required top-level structure
        required_keys = ["version", "dispositions", "entities"]
        for key in required_keys:
            if key not in self.entity_database:
                errors.append(f"Missing required key: {key}")
        
        # Validate entities
        if "entities" in self.entity_database:
            for i, entity in enumerate(self.entity_database["entities"]):
                entity_errors = self._validate_entity(entity, i)
                errors.extend(entity_errors)
        
        # Validate dispositions
        if "dispositions" in self.entity_database:
            disp_errors = self._validate_dispositions(self.entity_database["dispositions"])
            errors.extend(disp_errors)
        
        return len(errors) == 0, errors
    
    def _validate_entity(self, entity: Dict[str, Any], index: int) -> List[str]:
        """Validate individual entity definition"""
        errors = []
        prefix = f"Entity {index}: "
        
        # Required fields
        required_fields = ["id", "name", "category", "kinematics", "disposition_types", "simulation_parameters"]
        for field in required_fields:
            if field not in entity:
                errors.append(f"{prefix}Missing required field: {field}")
        
        # Validate kinematics
        if "kinematics" in entity:
            kinematics = entity["kinematics"]
            required_kinematic_fields = ["minSpeed", "maxSpeed", "cruiseSpeed"]
            for field in required_kinematic_fields:
                if field not in kinematics:
                    errors.append(f"{prefix}Missing kinematic field: {field}")
                elif not isinstance(kinematics[field], (int, float)):
                    errors.append(f"{prefix}Invalid kinematic field type: {field}")
        
        # Validate simulation parameters
        if "simulation_parameters" in entity:
            sim_params = entity["simulation_parameters"]
            if "spawn_probability" in sim_params:
                prob = sim_params["spawn_probability"]
                if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                    errors.append(f"{prefix}Invalid spawn_probability: must be between 0 and 1")
        
        return errors
    
    def _validate_dispositions(self, dispositions: Dict[str, Any]) -> List[str]:
        """Validate disposition configuration"""
        errors = []
        
        if "colors" not in dispositions:
            errors.append("Missing dispositions.colors")
            return errors
        
        required_dispositions = ["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"]
        colors = dispositions["colors"]
        
        for disposition in required_dispositions:
            if disposition not in colors:
                errors.append(f"Missing disposition color: {disposition}")
                continue
            
            disp_colors = colors[disposition]
            required_color_types = ["primary", "secondary", "gizmo"]
            
            for color_type in required_color_types:
                if color_type not in disp_colors:
                    errors.append(f"Missing color type {color_type} for disposition {disposition}")
        
        return errors
    
    def export_database_template(self, output_path: str) -> bool:
        """Export a template entity database"""
        try:
            template = self._get_default_database()
            
            with open(output_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            self.logger.info(f"Database template exported to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export template: {e}")
            return False
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create backup of current database"""
        try:
            entity_sync_path = self.config_loader.get_expanded_path("entity_sync_path")
            source_path = os.path.join(entity_sync_path, "entity_definitions.json")
            
            if not os.path.exists(source_path):
                self.logger.warning("No database file to backup")
                return False
            
            if backup_path is None:
                backup_path = source_path + ".backup"
            
            shutil.copy2(source_path, backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False


class TerrainBoundaryLoader:
    """Handles loading terrain boundary data from Unity export"""
    
    def __init__(self, config_loader: ConfigurationLoader):
        self.config_loader = config_loader
        self.terrain_data: Optional[Dict[str, Any]] = None
        self.current_path: str = ""
        self.logger = logging.getLogger(__name__)
    
    def load_terrain_boundaries(self, custom_path: Optional[str] = None) -> bool:
        """Load terrain boundary data"""
        if custom_path:
            # Check if custom_path is a file or directory
            if os.path.isfile(custom_path):
                boundary_path = custom_path
            elif os.path.isdir(custom_path):
                boundary_path = os.path.join(custom_path, "terrain_boundaries.json")
            else:
                # Assume it's a file path even if it doesn't exist yet
                boundary_path = custom_path
        else:
            terrain_sync_path = self.config_loader.get_expanded_path("terrain_sync_path")
            boundary_path = os.path.join(terrain_sync_path, "terrain_boundaries.json")
        
        try:
            if not os.path.exists(boundary_path):
                self.logger.warning(f"Terrain boundaries not found at: {boundary_path}")
                return False
            
            with open(boundary_path, 'r') as f:
                self.terrain_data = json.load(f)
            
            # Store current path for configuration saving
            self.current_path = boundary_path
            
            self.logger.info(f"Loaded terrain boundaries from {boundary_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load terrain boundaries: {e}")
            return False
    
    def get_terrain_bounds(self) -> Optional[Dict[str, float]]:
        """Get terrain boundary values"""
        if not self.terrain_data or "boundaries" not in self.terrain_data:
            return None
        
        boundaries = self.terrain_data["boundaries"]
        return {
            "min_x": boundaries.get("min_x", -5000.0),
            "max_x": boundaries.get("max_x", 5000.0),
            "min_z": boundaries.get("min_z", -5000.0),
            "max_z": boundaries.get("max_z", 5000.0),
            "min_y": boundaries.get("min_y", 0.0),
            "max_y": boundaries.get("max_y", 1000.0)
        }
    
    def get_terrain_info(self) -> Dict[str, Any]:
        """Get terrain information summary"""
        if not self.terrain_data:
            return {"loaded": False}
        
        info = {
            "loaded": True,
            "version": self.terrain_data.get("version", "unknown"),
            "timestamp": self.terrain_data.get("timestamp", "unknown"),
            "terrain_count": self.terrain_data.get("terrain_count", 0),
            "boundaries": self.get_terrain_bounds()
        }
        
        if "individual_terrains" in self.terrain_data:
            terrains = self.terrain_data["individual_terrains"]
            info["individual_terrains"] = [
                {
                    "name": terrain.get("name", "Unknown"),
                    "size": terrain.get("size", {}),
                    "position": terrain.get("position", {})
                }
                for terrain in terrains
            ]
        
        return info
    
    def is_terrain_loaded(self) -> bool:
        """Check if terrain data is loaded"""
        return self.terrain_data is not None
    
    def get_current_path(self) -> str:
        """Get the current terrain boundaries file path"""
        return self.current_path