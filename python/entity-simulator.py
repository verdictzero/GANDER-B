"""
Entity Simulator
Simulates entity movement patterns and behavior for battlespace visualization
"""

import random
import math
import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging


class PatrolBehavior(Enum):
    RANDOM_WAYPOINT = "RANDOM_WAYPOINT"
    ROAD_FOLLOWING = "ROAD_FOLLOWING"
    AREA_SWEEP = "AREA_SWEEP"
    PERIMETER_SCOUT = "PERIMETER_SCOUT"
    TRANSPORT_ROUTE = "TRANSPORT_ROUTE"
    STATIONARY = "STATIONARY"
    ORBITAL = "ORBITAL"


class MovementType(Enum):
    GROUND_TRACKED = "GROUND_TRACKED"
    GROUND_WHEELED = "GROUND_WHEELED"
    GROUND_FOOT = "GROUND_FOOT"
    FLIGHT_3D = "3D_FLIGHT"
    ROTORCRAFT_3D = "3D_ROTORCRAFT"


@dataclass
class Position3D:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def distance_to(self, other: 'Position3D') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def distance_to_2d(self, other: 'Position3D') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.z - other.z)**2)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class Velocity3D:
    speed: float = 0.0
    heading: float = 0.0  # Degrees
    climb_rate: float = 0.0  # Vertical speed
    
    def to_vector(self) -> Tuple[float, float, float]:
        """Convert to velocity vector (vx, vy, vz)"""
        heading_rad = math.radians(self.heading)
        vx = self.speed * math.sin(heading_rad)
        vz = self.speed * math.cos(heading_rad)
        return (vx, self.climb_rate, vz)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.speed, self.heading, self.climb_rate)


@dataclass
class TerrainBounds:
    min_x: float = -5000.0
    max_x: float = 5000.0
    min_z: float = -5000.0
    max_z: float = 5000.0
    min_y: float = 0.0
    max_y: float = 1000.0
    
    def is_within_bounds(self, position: Position3D, check_altitude: bool = False) -> bool:
        within_xz = (self.min_x <= position.x <= self.max_x and 
                    self.min_z <= position.z <= self.max_z)
        
        if not check_altitude:
            return within_xz
        
        return within_xz and self.min_y <= position.y <= self.max_y
    
    def get_random_position(self, include_altitude: bool = False) -> Position3D:
        x = random.uniform(self.min_x, self.max_x)
        z = random.uniform(self.min_z, self.max_z)
        y = random.uniform(self.min_y, self.max_y) if include_altitude else 0.0
        
        return Position3D(x, y, z)
    
    def clamp_position(self, position: Position3D, check_altitude: bool = False) -> Position3D:
        clamped = Position3D(
            x=max(self.min_x, min(self.max_x, position.x)),
            y=position.y,
            z=max(self.min_z, min(self.max_z, position.z))
        )
        
        if check_altitude:
            clamped.y = max(self.min_y, min(self.max_y, position.y))
        
        return clamped


@dataclass
class Waypoint:
    position: Position3D
    arrival_time: float = 0.0
    hold_time: float = 0.0
    speed_override: Optional[float] = None


@dataclass
class SimulatedEntity:
    entity_id: str
    entity_definition: Dict[str, Any]
    position: Position3D = field(default_factory=Position3D)
    velocity: Velocity3D = field(default_factory=Velocity3D)
    
    # Movement state
    target_position: Optional[Position3D] = None
    waypoints: List[Waypoint] = field(default_factory=list)
    current_waypoint_index: int = 0
    last_update_time: float = field(default_factory=time.time)
    
    # Entity properties
    callsign: str = ""
    disposition: str = "UNKNOWN"
    patrol_behavior: PatrolBehavior = PatrolBehavior.RANDOM_WAYPOINT
    movement_type: MovementType = MovementType.GROUND_TRACKED
    
    # Timing
    last_full_message_time: float = 0.0
    last_compact_message_time: float = 0.0
    spawn_time: float = field(default_factory=time.time)
    
    # State flags
    is_active: bool = True
    needs_full_update: bool = True
    is_moving: bool = False
    
    # Speed control
    base_speed: float = 0.0  # Original speed from entity definition
    speed_multiplier: float = 1.0  # Current speed multiplier
    
    def __post_init__(self):
        if self.entity_definition:
            self._load_from_definition()
    
    def _load_from_definition(self):
        """Load entity properties from definition"""
        self.callsign = self._generate_callsign()
        
        # Set movement type
        movement_type_str = self.entity_definition.get("kinematics", {}).get("movement_type", "GROUND_TRACKED")
        try:
            self.movement_type = MovementType(movement_type_str)
        except ValueError:
            self.movement_type = MovementType.GROUND_TRACKED
        
        # Set patrol behavior
        behavior_str = self.entity_definition.get("simulation_parameters", {}).get("patrol_behavior", "RANDOM_WAYPOINT")
        try:
            self.patrol_behavior = PatrolBehavior(behavior_str)
        except ValueError:
            self.patrol_behavior = PatrolBehavior.RANDOM_WAYPOINT
        
        # Set random disposition
        available_dispositions = self.entity_definition.get("disposition_types", ["UNKNOWN"])
        self.disposition = random.choice(available_dispositions)
        
        # Set initial altitude based on category
        if self.entity_definition.get("category") == "AIR":
            kinematics = self.entity_definition.get("kinematics", {})
            self.position.y = kinematics.get("defaultAltitude", 500.0)
    
    def _generate_callsign(self) -> str:
        """Generate a realistic callsign"""
        prefixes = ["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT", 
                   "GOLF", "HOTEL", "INDIA", "JULIET", "KILO", "LIMA"]
        suffix = random.randint(1, 99)
        return f"{random.choice(prefixes)}-{suffix:02d}"
    
    def get_max_speed(self) -> float:
        """Get maximum speed from entity definition"""
        return self.entity_definition.get("kinematics", {}).get("maxSpeed", 10.0)
    
    def get_min_speed(self) -> float:
        """Get minimum speed from entity definition"""
        return self.entity_definition.get("kinematics", {}).get("minSpeed", 0.0)
    
    def get_cruise_speed(self) -> float:
        """Get cruise speed from entity definition"""
        return self.entity_definition.get("kinematics", {}).get("cruiseSpeed", 5.0)
    
    def get_turn_rate(self) -> float:
        """Get turn rate from entity definition"""
        return self.entity_definition.get("kinematics", {}).get("turnRate", 30.0)
    
    def get_acceleration(self) -> float:
        """Get acceleration from entity definition"""
        return self.entity_definition.get("kinematics", {}).get("acceleration", 2.0)
    
    def apply_speed_multiplier(self, multiplier: float):
        """Apply speed multiplier to entity's current speed"""
        if self.base_speed == 0.0:
            # First time setting multiplier - store current speed as base
            self.base_speed = self.velocity.speed
        
        self.speed_multiplier = multiplier
        self.velocity.speed = self.base_speed * multiplier


class EntitySimulator:
    """Manages simulation of multiple entities with realistic movement patterns"""
    
    def __init__(self, terrain_bounds: TerrainBounds = None):
        self.terrain_bounds = terrain_bounds or TerrainBounds()
        self.entities: Dict[str, SimulatedEntity] = {}
        self.entity_definitions: Dict[str, Dict[str, Any]] = {}
        
        # Simulation settings
        self.max_entities = 100
        self.spawn_rate = 10.0  # entities per minute
        self.update_rate = 30.0  # Hz
        self.full_update_interval = 30.0  # seconds
        self.compact_update_interval = 2.0  # seconds
        self.speed_multiplier = 1.0  # Global speed multiplier
        
        # Simulation state
        self.is_running = False
        self.simulation_thread = None
        self.stop_event = threading.Event()
        self.last_spawn_time = 0.0
        
        # Statistics
        self.stats = {
            "entities_spawned": 0,
            "entities_despawned": 0,
            "active_entities": 0,
            "updates_per_second": 0.0,
            "simulation_time": 0.0
        }
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
    
    def load_entity_definitions(self, definitions: Dict[str, Dict[str, Any]]):
        """Load entity definitions from configuration"""
        self.entity_definitions = definitions
        self.logger.info(f"Loaded {len(definitions)} entity definitions")
    
    def set_terrain_bounds(self, bounds: TerrainBounds):
        """Set terrain boundaries"""
        self.terrain_bounds = bounds
        self.logger.info(f"Terrain bounds set: {bounds}")
    
    def set_speed_multiplier(self, multiplier: float):
        """Set global speed multiplier for all entities"""
        if multiplier <= 0:
            self.logger.warning("Speed multiplier must be positive")
            return
        
        old_multiplier = self.speed_multiplier
        self.speed_multiplier = multiplier
        self.logger.info(f"Speed multiplier changed from {old_multiplier:.2f} to {multiplier:.2f}")
        
        # Update all existing entities with new speed multiplier
        for entity in self.entities.values():
            entity.apply_speed_multiplier(multiplier)
    
    def set_update_rate(self, rate: float):
        """Set simulation update rate with validation"""
        if rate <= 0:
            self.logger.warning(f"Update rate must be positive, got {rate}. Using minimum 0.1")
            rate = 0.1
        
        old_rate = self.update_rate
        self.update_rate = rate
        self.logger.info(f"Update rate changed from {old_rate:.2f} to {rate:.2f}")
    
    def set_spawn_rate(self, rate: float):
        """Set entity spawn rate with validation"""
        if rate <= 0:
            self.logger.warning(f"Spawn rate must be positive, got {rate}. Using minimum 0.1")
            rate = 0.1
        
        old_rate = self.spawn_rate
        self.spawn_rate = rate
        self.logger.info(f"Spawn rate changed from {old_rate:.2f} to {rate:.2f}")
    
    def start_simulation(self) -> bool:
        """Start the entity simulation"""
        if self.is_running:
            self.logger.warning("Simulation is already running")
            return False
        
        if not self.entity_definitions:
            self.logger.error("No entity definitions loaded")
            return False
        
        self.stop_event.clear()
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        
        self.is_running = True
        self.logger.info("Entity simulation started")
        return True
    
    def stop_simulation(self):
        """Stop the entity simulation"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.stop_event.set()
        
        if self.simulation_thread:
            self.simulation_thread.join(timeout=5.0)
        
        self.logger.info("Entity simulation stopped")
    
    def _simulation_loop(self):
        """Main simulation loop"""
        last_update_time = time.time()
        # Prevent division by zero for update_rate
        safe_update_rate = max(0.1, self.update_rate)
        update_interval = 1.0 / safe_update_rate
        
        while not self.stop_event.wait(update_interval):
            current_time = time.time()
            dt = current_time - last_update_time
            
            try:
                # Spawn new entities if needed
                self._maybe_spawn_entities()
                
                # Update all entities
                self._update_entities(dt)
                
                # Remove entities that are out of bounds
                self._cleanup_entities()
                
                # Update statistics
                self._update_statistics()
                
                last_update_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in simulation loop: {e}")
    
    def _maybe_spawn_entities(self):
        """Spawn new entities based on spawn rate and availability"""
        current_time = time.time()
        
        if len(self.entities) >= self.max_entities:
            return
        
        # Check if it's time to spawn a new entity
        time_since_last_spawn = current_time - self.last_spawn_time
        # Prevent division by zero for spawn_rate
        safe_spawn_rate = max(0.1, self.spawn_rate)
        spawn_interval = 60.0 / safe_spawn_rate  # Convert per-minute to interval
        
        if time_since_last_spawn >= spawn_interval:
            self._spawn_random_entity()
            self.last_spawn_time = current_time
    
    def _spawn_random_entity(self):
        """Spawn a random entity based on definition probabilities"""
        # Select entity type based on spawn probability
        available_definitions = []
        probabilities = []
        
        for def_id, definition in self.entity_definitions.items():
            spawn_prob = definition.get("simulation_parameters", {}).get("spawn_probability", 0.1)
            max_concurrent = definition.get("simulation_parameters", {}).get("max_concurrent", 10)
            
            # Count existing entities of this type
            current_count = sum(1 for entity in self.entities.values() 
                              if entity.entity_definition.get("id") == def_id)
            
            if current_count < max_concurrent:
                available_definitions.append((def_id, definition))
                probabilities.append(spawn_prob)
        
        if not available_definitions:
            return
        
        # Select entity type
        selected_def = random.choices(available_definitions, weights=probabilities)[0]
        def_id, definition = selected_def
        
        # Generate unique entity ID
        entity_id = f"SIM-{def_id}-{int(time.time())}-{random.randint(1000, 9999)}"
        
        # Create entity
        entity = SimulatedEntity(
            entity_id=entity_id,
            entity_definition=definition
        )
        
        # Set initial position
        if definition.get("category") == "AIR":
            entity.position = self.terrain_bounds.get_random_position(include_altitude=True)
        else:
            entity.position = self.terrain_bounds.get_random_position(include_altitude=False)
        
        # Set initial velocity
        cruise_speed = entity.get_cruise_speed()
        initial_heading = random.uniform(0, 360)
        entity.velocity = Velocity3D(speed=cruise_speed, heading=initial_heading)
        
        # Initialize speed control
        entity.base_speed = cruise_speed
        entity.speed_multiplier = self.speed_multiplier
        entity.velocity.speed = entity.base_speed * entity.speed_multiplier
        
        # Initialize movement pattern
        self._initialize_entity_movement(entity)
        
        # Add to simulation
        self.entities[entity_id] = entity
        self.stats["entities_spawned"] += 1
        
        self.logger.debug(f"Spawned entity: {entity_id} ({entity.callsign})")
    
    def spawn_entity_at_position(self, entity_id: str, entity_type: Dict[str, Any], 
                               position: Tuple[float, float, float], 
                               disposition: str) -> bool:
        """
        Manually spawn an entity at a specific position
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Entity definition dictionary
            position: (x, y, z) position tuple
            disposition: Entity disposition (FRIENDLY, HOSTILE, NEUTRAL, etc.)
        
        Returns:
            bool: True if entity was successfully spawned, False otherwise
        """
        try:
            # Debug: Log the entity definition being passed
            self.logger.info(f"[PREFAB_DEBUG_SPAWN] Entity definition keys: {list(entity_type.keys()) if entity_type else 'None'}")
            self.logger.info(f"[PREFAB_DEBUG_SPAWN] Entity category: {entity_type.get('category', 'MISSING')}")
            self.logger.info(f"[PREFAB_DEBUG_SPAWN] Entity specification: {entity_type.get('specification', 'MISSING')}")
            self.logger.info(f"[PREFAB_DEBUG_SPAWN] Entity model: {entity_type.get('model', 'MISSING')}")
            
            # Create entity
            entity = SimulatedEntity(
                entity_id=entity_id,
                entity_definition=entity_type
            )
            
            # Set specified position
            entity.position = Position3D(x=position[0], y=position[1], z=position[2])
            
            # Set disposition
            entity.disposition = disposition
            
            # Set initial velocity
            cruise_speed = entity.get_cruise_speed()
            initial_heading = random.uniform(0, 360)
            entity.velocity = Velocity3D(speed=cruise_speed, heading=initial_heading)
            
            # Initialize speed control
            entity.base_speed = cruise_speed
            entity.speed_multiplier = self.speed_multiplier
            entity.velocity.speed = entity.base_speed * entity.speed_multiplier
            
            # Initialize movement pattern
            self._initialize_entity_movement(entity)
            
            # Add to simulation
            self.entities[entity_id] = entity
            self.stats["entities_spawned"] += 1
            
            self.logger.debug(f"Manually spawned entity: {entity_id} at {position}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to spawn entity {entity_id}: {e}")
            return False
    
    def spawn_random_entities(self, count: int) -> int:
        """
        Spawn multiple random entities
        
        Args:
            count: Number of entities to spawn
            
        Returns:
            int: Number of entities successfully spawned
        """
        spawned_count = 0
        
        for i in range(count):
            if len(self.entities) >= self.max_entities:
                self.logger.warning(f"Cannot spawn more entities - max limit {self.max_entities} reached")
                break
                
            try:
                self._spawn_random_entity()
                spawned_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to spawn random entity {i+1}: {e}")
        
        self.logger.info(f"Spawned {spawned_count}/{count} random entities")
        return spawned_count
    
    def _initialize_entity_movement(self, entity: SimulatedEntity):
        """Initialize movement pattern for an entity"""
        if entity.patrol_behavior == PatrolBehavior.RANDOM_WAYPOINT:
            self._generate_random_waypoints(entity)
        elif entity.patrol_behavior == PatrolBehavior.ORBITAL:
            self._generate_orbital_pattern(entity)
        elif entity.patrol_behavior == PatrolBehavior.AREA_SWEEP:
            self._generate_sweep_pattern(entity)
        elif entity.patrol_behavior == PatrolBehavior.PERIMETER_SCOUT:
            self._generate_perimeter_pattern(entity)
        elif entity.patrol_behavior == PatrolBehavior.TRANSPORT_ROUTE:
            self._generate_transport_route(entity)
        else:
            # Default to random waypoints
            self._generate_random_waypoints(entity)
    
    def _generate_random_waypoints(self, entity: SimulatedEntity, count: int = 5):
        """Generate random waypoints for an entity"""
        entity.waypoints.clear()
        
        for _ in range(count):
            if entity.entity_definition.get("category") == "AIR":
                waypoint_pos = self.terrain_bounds.get_random_position(include_altitude=True)
            else:
                waypoint_pos = self.terrain_bounds.get_random_position(include_altitude=False)
            
            waypoint = Waypoint(
                position=waypoint_pos,
                hold_time=random.uniform(10, 60)  # Hold for 10-60 seconds
            )
            entity.waypoints.append(waypoint)
        
        entity.current_waypoint_index = 0
        entity.target_position = entity.waypoints[0].position if entity.waypoints else None
    
    def _generate_orbital_pattern(self, entity: SimulatedEntity):
        """Generate circular/orbital movement pattern"""
        center = entity.position
        radius = random.uniform(500, 2000)
        waypoint_count = 8
        
        entity.waypoints.clear()
        
        for i in range(waypoint_count):
            angle = (2 * math.pi * i) / waypoint_count
            x = center.x + radius * math.cos(angle)
            z = center.z + radius * math.sin(angle)
            y = center.y  # Maintain altitude for air units
            
            waypoint = Waypoint(
                position=Position3D(x, y, z),
                hold_time=0  # No holding, continuous movement
            )
            entity.waypoints.append(waypoint)
        
        entity.current_waypoint_index = 0
        entity.target_position = entity.waypoints[0].position
    
    def _generate_sweep_pattern(self, entity: SimulatedEntity):
        """Generate area sweep pattern (back and forth)"""
        # Implementation would create a grid-like sweep pattern
        self._generate_random_waypoints(entity, 4)  # Simplified for now
    
    def _generate_perimeter_pattern(self, entity: SimulatedEntity):
        """Generate perimeter patrol pattern"""
        # Implementation would follow terrain boundaries
        self._generate_random_waypoints(entity, 6)  # Simplified for now
    
    def _generate_transport_route(self, entity: SimulatedEntity):
        """Generate transport route (point A to point B)"""
        start = entity.position
        end = self.terrain_bounds.get_random_position(
            include_altitude=(entity.entity_definition.get("category") == "AIR")
        )
        
        entity.waypoints = [
            Waypoint(position=start, hold_time=0),
            Waypoint(position=end, hold_time=30)  # Hold at destination
        ]
        entity.current_waypoint_index = 0
        entity.target_position = end
    
    def _update_entities(self, dt: float):
        """Update all entities"""
        for entity in list(self.entities.values()):
            self._update_entity(entity, dt)
    
    def _update_entity(self, entity: SimulatedEntity, dt: float):
        """Update a single entity"""
        if not entity.is_active:
            return
        
        # Update movement
        self._update_entity_movement(entity, dt)
        
        # Check boundaries
        if not self.terrain_bounds.is_within_bounds(entity.position, 
                                                   check_altitude=(entity.entity_definition.get("category") == "AIR")):
            entity.is_active = False
            return
        
        entity.last_update_time = time.time()
    
    def _update_entity_movement(self, entity: SimulatedEntity, dt: float):
        """Update entity movement towards target"""
        if not entity.target_position:
            return
        
        # Calculate distance to target
        distance_to_target = entity.position.distance_to(entity.target_position)
        
        # Check if we've reached the current waypoint
        if distance_to_target < 50.0:  # Within 50 units of target
            self._advance_to_next_waypoint(entity)
            return
        
        # Move towards target
        direction_x = entity.target_position.x - entity.position.x
        direction_z = entity.target_position.z - entity.position.z
        direction_y = entity.target_position.y - entity.position.y
        
        # Calculate heading
        new_heading = math.degrees(math.atan2(direction_x, direction_z))
        if new_heading < 0:
            new_heading += 360
        
        # Smooth heading changes (limited turn rate)
        max_turn = entity.get_turn_rate() * dt
        heading_diff = new_heading - entity.velocity.heading
        
        # Handle heading wrap-around
        if heading_diff > 180:
            heading_diff -= 360
        elif heading_diff < -180:
            heading_diff += 360
        
        if abs(heading_diff) > max_turn:
            heading_diff = max_turn if heading_diff > 0 else -max_turn
        
        entity.velocity.heading += heading_diff
        entity.velocity.heading = entity.velocity.heading % 360
        
        # Calculate new position
        speed = entity.velocity.speed
        heading_rad = math.radians(entity.velocity.heading)
        
        # Update position
        entity.position.x += speed * math.sin(heading_rad) * dt
        entity.position.z += speed * math.cos(heading_rad) * dt
        
        # Handle altitude for air units
        if entity.entity_definition.get("category") == "AIR":
            if abs(direction_y) > 10:  # If significant altitude difference
                climb_rate = entity.entity_definition.get("kinematics", {}).get("climbRate", 5.0)
                if direction_y > 0:
                    entity.velocity.climb_rate = min(climb_rate, direction_y / dt)
                else:
                    entity.velocity.climb_rate = max(-climb_rate, direction_y / dt)
                
                entity.position.y += entity.velocity.climb_rate * dt
        
        entity.is_moving = speed > 0.1
    
    def _advance_to_next_waypoint(self, entity: SimulatedEntity):
        """Advance entity to next waypoint"""
        if not entity.waypoints:
            return
        
        entity.current_waypoint_index = (entity.current_waypoint_index + 1) % len(entity.waypoints)
        entity.target_position = entity.waypoints[entity.current_waypoint_index].position
    
    def _cleanup_entities(self):
        """Remove inactive entities"""
        inactive_entities = [entity_id for entity_id, entity in self.entities.items() 
                           if not entity.is_active]
        
        for entity_id in inactive_entities:
            del self.entities[entity_id]
            self.stats["entities_despawned"] += 1
            self.logger.debug(f"Despawned entity: {entity_id}")
    
    def _update_statistics(self):
        """Update simulation statistics"""
        self.stats["active_entities"] = len(self.entities)
        self.stats["simulation_time"] = time.time() - getattr(self, 'start_time', time.time())
    
    def get_entities_for_update(self, message_type: str = "compact") -> List[Dict[str, Any]]:
        """Get entities that need updates of specified type"""
        current_time = time.time()
        entities_to_update = []
        
        for entity in self.entities.values():
            if not entity.is_active:
                continue
            
            needs_update = False
            
            if message_type == "full":
                if (entity.needs_full_update or 
                    current_time - entity.last_full_message_time >= self.full_update_interval):
                    needs_update = True
                    entity.last_full_message_time = current_time
                    entity.needs_full_update = False
            
            elif message_type == "compact":
                if current_time - entity.last_compact_message_time >= self.compact_update_interval:
                    needs_update = True
                    entity.last_compact_message_time = current_time
            
            if needs_update:
                entity_data = self._entity_to_dict(entity)
                entities_to_update.append(entity_data)
        
        return entities_to_update
    
    def get_despawned_entities(self) -> List[str]:
        """Get list of entities that should be despawned"""
        # This would return entities that have been marked for despawn
        # For now, we handle despawning in _cleanup_entities
        return []
    
    def _entity_to_dict(self, entity: SimulatedEntity) -> Dict[str, Any]:
        """Convert entity to dictionary format for TEDF messages"""
        # Debug: Log entity definition being converted
        self.logger.info(f"[PREFAB_DEBUG_CONVERT] Entity {entity.entity_id} definition keys: {list(entity.entity_definition.keys()) if entity.entity_definition else 'None'}")
        self.logger.info(f"[PREFAB_DEBUG_CONVERT] Entity category: {entity.entity_definition.get('category', 'MISSING')}")
        self.logger.info(f"[PREFAB_DEBUG_CONVERT] Entity specification: {entity.entity_definition.get('specification', 'MISSING')}")
        self.logger.info(f"[PREFAB_DEBUG_CONVERT] Entity model: {entity.entity_definition.get('model', 'MISSING')}")
        
        # Extract model from entity definition, fallback to specification if not found
        model = entity.entity_definition.get("model", 
                                           entity.entity_definition.get("specification", "UNKNOWN"))
        
        result = {
            "entity_id": entity.entity_id,
            "unit_name": entity.callsign.split('-')[0] if '-' in entity.callsign else entity.callsign,
            "callsign": entity.callsign,
            "position": {
                "x": entity.position.x,
                "y": entity.position.y,
                "z": entity.position.z
            },
            "velocity": {
                "speed": entity.velocity.speed,
                "heading": entity.velocity.heading,
                "climb_rate": entity.velocity.climb_rate
            },
            "type": {
                "category": entity.entity_definition.get("category", "UNKNOWN"),
                "subcategory": entity.entity_definition.get("subcategory", "UNKNOWN"),
                "specification": entity.entity_definition.get("specification", "UNKNOWN")
            },
            "model": model,
            "disposition": {
                "affiliation": entity.disposition,
                "confidence": 1.0
            },
            "disposition_code": entity.disposition[0] if entity.disposition else "U"  # First letter
        }
        
        # Debug: Log the final TEDF data being returned
        self.logger.info(f"[PREFAB_DEBUG_FINAL] Final TEDF data for {entity.entity_id}: type={{category: {result['type']['category']}, subcategory: {result['type']['subcategory']}, specification: {result['type']['specification']}}}, model: {result['model']}")
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics"""
        return self.stats.copy()
    
    def force_despawn_entity(self, entity_id: str) -> bool:
        """Force despawn of specific entity"""
        if entity_id in self.entities:
            self.entities[entity_id].is_active = False
            return True
        return False
    
    def get_entity_count_by_type(self) -> Dict[str, int]:
        """Get count of entities by type"""
        counts = {}
        for entity in self.entities.values():
            entity_type = entity.entity_definition.get("id", "unknown")
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts