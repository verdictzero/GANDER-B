#!/usr/bin/env python3
"""
TEDF Message Listener
Command-line utility that listens to the battlespace simulator broadcast
and displays raw TEDF messages in real-time
"""

import argparse
import json
import time
import signal
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import zmq
import threading


class TEDFMessageListener:
    """Listens to TEDF messages and displays them"""
    
    def __init__(self, address: str = "tcp://localhost", port: int = 5555, 
                 display_mode: str = "pretty", filter_type: Optional[str] = None):
        self.address = address
        self.port = port
        self.display_mode = display_mode
        self.filter_type = filter_type
        
        # ZMQ setup
        self.context = None
        self.socket = None
        self.is_listening = False
        
        # Statistics
        self.stats = {
            "messages_received": 0,
            "messages_by_type": {},
            "start_time": None,
            "last_message_time": None,
            "connection_attempts": 0,
            "connection_errors": 0
        }
        
        # Message tracking
        self.entity_count = {}
        self.last_entities = set()
        
        # Display settings
        self.show_timestamps = True
        self.show_stats_interval = 10  # seconds
        self.last_stats_display = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n\n🛑 Received signal {signum}, shutting down gracefully...")
        self.stop_listening()
        sys.exit(0)
    
    def start_listening(self) -> bool:
        """Start listening to TEDF messages"""
        try:
            print(f"🔗 Connecting to TEDF broadcaster...")
            print(f"   Address: {self.address}:{self.port}")
            print(f"   Display Mode: {self.display_mode}")
            if self.filter_type:
                print(f"   Filter: {self.filter_type} messages only")
            print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # Initialize ZMQ
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            
            # Subscribe to all messages (empty string means all)
            self.socket.setsockopt(zmq.SUBSCRIBE, b"")
            
            # Set socket options
            self.socket.setsockopt(zmq.RCVHWM, 1000)  # Receive buffer
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            
            # Connect to broadcaster
            full_address = f"{self.address}:{self.port}"
            self.socket.connect(full_address)
            
            self.is_listening = True
            self.stats["start_time"] = time.time()
            self.stats["connection_attempts"] += 1
            
            print(f"✅ Connected to {full_address}")
            print(f"🎧 Listening for TEDF messages... (Press Ctrl+C to stop)\n")
            
            # Start listening loop
            self._listen_loop()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start listening: {e}")
            self.stats["connection_errors"] += 1
            self._cleanup()
            return False
    
    def stop_listening(self):
        """Stop listening and cleanup"""
        self.is_listening = False
        self._cleanup()
        self._display_final_stats()
    
    def _cleanup(self):
        """Clean up ZMQ resources"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
            self.socket = None
        
        if self.context:
            try:
                self.context.term()
            except Exception as e:
                print(f"Error terminating context: {e}")
            self.context = None
    
    def _listen_loop(self):
        """Main listening loop"""
        while self.is_listening:
            try:
                # Try to receive message with timeout
                try:
                    message = self.socket.recv_string(zmq.NOBLOCK)
                    self._process_message(message)
                except zmq.Again:
                    # No message available, continue
                    time.sleep(0.01)
                    continue
                
                # Display periodic stats
                current_time = time.time()
                if current_time - self.last_stats_display > self.show_stats_interval:
                    self._display_periodic_stats()
                    self.last_stats_display = current_time
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in listen loop: {e}")
                self.stats["connection_errors"] += 1
                time.sleep(1)
    
    def _process_message(self, raw_message: str):
        """Process received message"""
        try:
            self.stats["messages_received"] += 1
            self.stats["last_message_time"] = time.time()
            
            # Parse JSON
            message_data = json.loads(raw_message)
            
            # Determine message type based on actual message structure
            message_type = "unknown"
            
            if "header" in message_data:
                # Full or despawn message
                header = message_data["header"]
                if "messageType" in header:
                    if header["messageType"] == "ENTITY_DESPAWN":
                        message_type = "despawn"
                    else:
                        message_type = "full"
                else:
                    message_type = "full"
            elif "batch" in message_data:
                message_type = "batch"
            elif "h" in message_data and "e" in message_data:
                message_type = "compact"
            
            
            # Update type statistics
            if message_type not in self.stats["messages_by_type"]:
                self.stats["messages_by_type"][message_type] = 0
            self.stats["messages_by_type"][message_type] += 1
            
            # Filter messages if requested
            if self.filter_type and message_type != self.filter_type:
                return
            
            # Track entities
            self._track_entities(message_data, message_type)
            
            # Display message based on mode
            if self.display_mode == "raw":
                self._display_raw_message(raw_message)
            elif self.display_mode == "pretty":
                self._display_pretty_message(message_data, message_type)
            elif self.display_mode == "compact":
                self._display_compact_message(message_data)
            elif self.display_mode == "stats":
                # Only show stats, no individual messages
                pass
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON received: {e}")
            if self.display_mode == "raw":
                print(f"Raw message: {raw_message}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def _track_entities(self, message_data: Dict[str, Any], message_type: str):
        """Track entity statistics"""
        
        if message_type == "batch":
            batch_data = message_data.get("batch", {})
            entities = batch_data.get("entities", [])
            current_entities = {entity.get("entityId") for entity in entities if isinstance(entity, dict) and entity.get("entityId")}
        elif message_type == "full":
            entity_data = message_data.get("entity", {})
            entity_id = entity_data.get("entityId")
            current_entities = {entity_id} if entity_id else set()
        elif message_type == "compact":
            entity_data = message_data.get("e", {})
            if isinstance(entity_data, dict):
                entity_id = entity_data.get("id", entity_data.get("eId"))
                current_entities = {entity_id} if entity_id else set()
            else:
                current_entities = set()
        elif message_type == "despawn":
            entity_data = message_data.get("entity", {})
            entity_id = entity_data.get("entityId")
            if entity_id and entity_id in self.last_entities:
                self.last_entities.remove(entity_id)
            return
        else:
            return
        
        # Update entity tracking
        self.last_entities.update(current_entities)
        
        # Track entity types
        if message_type == "batch":
            batch_data = message_data.get("batch", {})
            for entity in batch_data.get("entities", []):
                if isinstance(entity, dict):
                    entity_type = entity.get("entityType", {}).get("category", "unknown")
                    if entity_type not in self.entity_count:
                        self.entity_count[entity_type] = 0
                    self.entity_count[entity_type] += 1
        elif message_type == "full":
            entity_data = message_data.get("entity", {})
            entity_type = entity_data.get("entityType", {}).get("category", "unknown")
            if entity_type not in self.entity_count:
                self.entity_count[entity_type] = 0
            self.entity_count[entity_type] += 1
        elif message_type == "compact":
            entity_data = message_data.get("e", {})
            if isinstance(entity_data, dict):
                # Handle new compact format (flat structure)
                if "id" in entity_data and "d" in entity_data:
                    entity_type = "unknown"  # New format doesn't include type info
                # Handle old compact format (nested structure)
                else:
                    entity_type_data = entity_data.get("eT", {})
                    if isinstance(entity_type_data, dict):
                        entity_type = entity_type_data.get("c", "unknown")
                    else:
                        entity_type = "unknown"
                
                if entity_type not in self.entity_count:
                    self.entity_count[entity_type] = 0
                self.entity_count[entity_type] += 1
            # Handle string entity data for compact messages
            elif isinstance(entity_data, str):
                entity_type = "unknown"
                if entity_type not in self.entity_count:
                    self.entity_count[entity_type] = 0
                self.entity_count[entity_type] += 1
    
    def _display_raw_message(self, raw_message: str):
        """Display raw JSON message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3] if self.show_timestamps else ""
        print(f"[{timestamp}] {raw_message}")
    
    def _display_pretty_message(self, message_data: Dict[str, Any], message_type: str):
        """Display formatted message with human-readable analysis"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3] if self.show_timestamps else ""
        message_type_upper = message_type.upper()
        
        # Message type icons and colors
        type_info = {
            "FULL": {"icon": "📊", "desc": "Complete entity data"},
            "COMPACT": {"icon": "📍", "desc": "Position update"},
            "BATCH": {"icon": "📦", "desc": "Multiple entities"},
            "DESPAWN": {"icon": "💥", "desc": "Entity removed"}
        }
        
        info = type_info.get(message_type_upper, {"icon": "❓", "desc": "Unknown"})
        
        print(f"\n[{timestamp}] {info['icon']} {message_type_upper} - {info['desc']}")
        print("-" * 50)
        
        if message_type == "batch":
            batch_data = message_data.get("batch", {})
            entities = batch_data.get("entities", [])
            print(f"📦 Batch contains {len(entities)} entities")
            
            # Analyze batch composition
            self._analyze_batch_composition(entities)
            
            # Show sample entities
            for i, entity in enumerate(entities[:3]):  # Show first 3 entities
                if isinstance(entity, dict):
                    print(f"\n  🔸 Entity {i+1}/{len(entities)}:")
                    self._display_batch_entity_info(entity, "    ")
            if len(entities) > 3:
                print(f"\n  ⏩ ... and {len(entities) - 3} more entities")
        elif message_type == "despawn":
            entity_data = message_data.get("entity", {})
            entity_id = entity_data.get("entityId", "unknown")
            header = message_data.get("header", {})
            reason = header.get("reason", "unknown")
            print(f"💥 Entity {entity_id[:8]}... removed")
            print(f"   Reason: {self._humanize_despawn_reason(reason)}")
        elif message_type == "full":
            entity_data = message_data.get("entity", {})
            self._display_entity_info(entity_data)
        elif message_type == "compact":
            entity_data = message_data.get("e", {})
            self._display_compact_entity_info(entity_data)
            # Add movement analysis for position updates
            if isinstance(entity_data, dict) and "k" in entity_data:
                self._analyze_compact_movement(entity_data["k"])
        
        print()
    
    def _display_compact_message(self, message_data: Dict[str, Any]):
        """Display compact one-line message"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.show_timestamps else ""
        
        # Determine message type based on structure
        if "batch" in message_data:
            message_type = "B"
            batch_data = message_data.get("batch", {})
            entities = batch_data.get("entities", [])
            print(f"[{timestamp}] {message_type} | Batch: {len(entities)} entities")
        elif "header" in message_data:
            header = message_data["header"]
            if header.get("messageType") == "ENTITY_DESPAWN":
                message_type = "D"
            else:
                message_type = "F"
            
            entity_data = message_data.get("entity", {})
            entity_id = entity_data.get("entityId", "unknown")
            entity_type = entity_data.get("entityType", {}).get("category", "?")
            
            if "kinematics" in entity_data:
                pos = entity_data["kinematics"]["position"]
                vel = entity_data["kinematics"]["velocity"]
                print(f"[{timestamp}] {message_type} | {entity_id[:8]} ({entity_type}) | "
                      f"Pos: ({pos['x']:.1f}, {pos['y']:.1f}, {pos['z']:.1f}) | "
                      f"Spd: {vel['speed']:.1f} | Hdg: {vel['heading']:.1f}°")
            else:
                print(f"[{timestamp}] {message_type} | {entity_id[:8]} ({entity_type})")
        elif "h" in message_data and "e" in message_data:
            message_type = "C"
            entity_data = message_data.get("e", {})
            
            # Handle new compact message format
            if isinstance(entity_data, dict):
                entity_id = entity_data.get("id", entity_data.get("eId", "unknown"))
                entity_type = "?"
                
                # Check for position data in new format
                if "p" in entity_data and "v" in entity_data:
                    pos = entity_data["p"]
                    vel = entity_data["v"]
                    if isinstance(pos, list) and len(pos) >= 3 and isinstance(vel, list) and len(vel) >= 2:
                        print(f"[{timestamp}] {message_type} | {entity_id[:8]} ({entity_type}) | "
                              f"Pos: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}) | "
                              f"Spd: {vel[0]:.1f} | Hdg: {vel[1]:.1f}°")
                    else:
                        print(f"[{timestamp}] {message_type} | {entity_id[:8]} ({entity_type})")
                # Handle old compact format for backward compatibility
                elif "k" in entity_data:
                    pos = entity_data["k"]["p"]
                    vel = entity_data["k"]["v"]
                    print(f"[{timestamp}] {message_type} | {entity_id[:8]} ({entity_type}) | "
                          f"Pos: ({pos['x']:.1f}, {pos['y']:.1f}, {pos['z']:.1f}) | "
                          f"Spd: {vel['s']:.1f} | Hdg: {vel['h']:.1f}°")
                else:
                    print(f"[{timestamp}] {message_type} | {entity_id[:8]} ({entity_type})")
            else:
                print(f"[{timestamp}] {message_type} | Entity data is not a dictionary: {type(entity_data)}")
        else:
            message_type = "?"
            print(f"[{timestamp}] {message_type} | Unknown message structure")
    
    def _display_entity_info(self, entity_data: Dict[str, Any], prefix: str = ""):
        """Display human-readable entity information"""
        # Handle both old and new entity data formats
        if isinstance(entity_data, str):
            print(f"❌ Error processing message: entity_data is a string instead of dict")
            return
        
        entity_id = entity_data.get("entityId", "unknown")
        
        # Entity type info with icons
        entity_type = entity_data.get("entityType", {})
        category = entity_type.get("category", "unknown")
        subcategory = entity_type.get("subcategory", "")
        specification = entity_type.get("specification", "")
        
        # Get appropriate icon for entity type
        type_icon = self._get_entity_icon(category, subcategory)
        
        print(f"{prefix}{type_icon} Entity: {entity_id[:8]}...")
        print(f"{prefix}   Type: {self._humanize_entity_type(category, subcategory, specification)}")
        
        # Callsign and unit name with military-style formatting
        if "callsign" in entity_data:
            print(f"{prefix}   📻 Callsign: {entity_data['callsign']}")
        if "unitName" in entity_data:
            print(f"{prefix}   🏷️  Unit: {entity_data['unitName']}")
        
        # Disposition with color coding
        if "disposition" in entity_data:
            disp = entity_data["disposition"]
            affiliation = disp.get('affiliation', 'unknown')
            confidence = disp.get('confidence', 1.0)
            disp_icon, disp_desc = self._get_disposition_info(affiliation)
            conf_desc = self._get_confidence_description(confidence)
            print(f"{prefix}   {disp_icon} Disposition: {disp_desc} ({conf_desc})")
        
        # Kinematics with human-readable formatting
        if "kinematics" in entity_data:
            kinematics = entity_data["kinematics"]
            pos = kinematics.get("position", {})
            vel = kinematics.get("velocity", {})
            
            # Position with coordinate analysis
            x, y, z = pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)
            coord_desc = self._analyze_coordinates(x, y, z, category)
            print(f"{prefix}   📍 Position: {coord_desc}")
            print(f"{prefix}      Coordinates: ({x:.1f}, {y:.1f}, {z:.1f})")
            
            # Velocity with movement analysis
            speed = vel.get('speed', 0)
            heading = vel.get('heading', 0)
            climb_rate = vel.get('climbRate', 0)
            
            speed_desc = self._get_speed_description(speed, category)
            heading_desc = self._get_heading_description(heading)
            
            print(f"{prefix}   🧭 Movement: {speed_desc}, heading {heading_desc}")
            if abs(climb_rate) > 0.1:
                climb_desc = "climbing" if climb_rate > 0 else "descending"
                print(f"{prefix}      ✈️  {climb_desc} at {abs(climb_rate):.1f} m/s")
        
        # Timestamps if available
        if "timestamp" in entity_data:
            timestamp = entity_data["timestamp"]
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age = (datetime.now(timezone.utc) - dt).total_seconds()
                age_desc = self._get_age_description(age)
                print(f"{prefix}   🕐 Data age: {age_desc}")
            except:
                print(f"{prefix}   🕐 Timestamp: {timestamp}")
    
    def _analyze_batch_composition(self, entities: list):
        """Analyze and display batch composition"""
        if not entities:
            return
        
        # Count by type
        type_counts = {}
        disposition_counts = {}
        
        for entity in entities:
            # Handle both dict entities and potential string entities
            if isinstance(entity, str):
                continue  # Skip string entities for now
            
            # Entity type - batch entities might have different structure
            entity_type = entity.get("type", entity.get("entityType", {}))
            if isinstance(entity_type, dict):
                category = entity_type.get("category", "unknown")
            else:
                category = "unknown"
            type_counts[category] = type_counts.get(category, 0) + 1
            
            # Disposition - batch entities have simpler disposition
            disposition = entity.get("disposition", "unknown")
            if isinstance(disposition, dict):
                affiliation = disposition.get("affiliation", "unknown")
            else:
                affiliation = disposition
            disposition_counts[affiliation] = disposition_counts.get(affiliation, 0) + 1
        
        # Display composition
        if type_counts:
            print("   📊 Entity Types:")
            for entity_type, count in sorted(type_counts.items()):
                icon = self._get_entity_icon(entity_type, "")
                percentage = (count / len(entities)) * 100
                print(f"      {icon} {entity_type}: {count} ({percentage:.0f}%)")
        
        if disposition_counts:
            print("   🎯 Force Distribution:")
            for disposition, count in sorted(disposition_counts.items()):
                icon, desc = self._get_disposition_info(disposition)
                percentage = (count / len(entities)) * 100
                print(f"      {icon} {desc}: {count} ({percentage:.0f}%)")
    
    def _analyze_movement(self, kinematics: Dict[str, Any]):
        """Analyze movement patterns"""
        vel = kinematics.get("velocity", {})
        speed = vel.get("speed", 0)
        heading = vel.get("heading", 0)
        climb_rate = vel.get("climbRate", 0)
        
        # Movement analysis
        movement_type = "stationary"
        if speed > 0.1:
            if speed < 5:
                movement_type = "slow movement"
            elif speed < 20:
                movement_type = "moderate speed"
            elif speed < 50:
                movement_type = "fast movement"
            else:
                movement_type = "high speed"
        
        print(f"   🏃 Movement Analysis: {movement_type}")
        
        # Direction analysis
        if speed > 0.1:
            direction = self._get_cardinal_direction(heading)
            print(f"   🧭 Heading: {direction} ({heading:.0f}°)")
        
        # Altitude change
        if abs(climb_rate) > 0.5:
            alt_change = "climbing rapidly" if climb_rate > 5 else "climbing"
            if climb_rate < 0:
                alt_change = "descending rapidly" if climb_rate < -5 else "descending"
            print(f"   ⬆️  Altitude: {alt_change} ({climb_rate:+.1f} m/s)")
    
    def _get_entity_icon(self, category: str, subcategory: str) -> str:
        """Get appropriate icon for entity type"""
        icons = {
            "AIR": "✈️",
            "GROUND": "🚗",
            "NAVAL": "🚢",
            "INFANTRY": "🚶",
            "VEHICLE": "🚗",
            "AIRCRAFT": "✈️",
            "HELICOPTER": "🚁",
            "FIGHTER": "🛩️",
            "BOMBER": "✈️",
            "TANK": "🏆",
            "UNKNOWN": "❓"
        }
        
        return icons.get(subcategory.upper(), icons.get(category.upper(), "🔹"))
    
    def _humanize_entity_type(self, category: str, subcategory: str, specification: str) -> str:
        """Create human-readable entity type description"""
        parts = []
        
        if specification:
            parts.append(specification.replace("_", " ").title())
        if subcategory and subcategory != category:
            parts.append(subcategory.replace("_", " ").title())
        if category:
            parts.append(category.replace("_", " ").title())
        
        if not parts:
            return "Unknown Entity"
        
        return " ".join(parts)
    
    def _get_disposition_info(self, affiliation: str) -> tuple:
        """Get disposition icon and description"""
        dispositions = {
            "FRIENDLY": ("🟢", "Friendly"),
            "HOSTILE": ("🔴", "Hostile"),
            "NEUTRAL": ("🟡", "Neutral"),
            "UNKNOWN": ("⚪", "Unknown"),
            "F": ("🟢", "Friendly"),
            "H": ("🔴", "Hostile"),
            "N": ("🟡", "Neutral"),
            "U": ("⚪", "Unknown")
        }
        
        return dispositions.get(affiliation.upper(), ("❓", affiliation))
    
    def _get_confidence_description(self, confidence: float) -> str:
        """Get confidence level description"""
        if confidence >= 0.9:
            return "High confidence"
        elif confidence >= 0.7:
            return "Medium confidence"
        elif confidence >= 0.5:
            return "Low confidence"
        else:
            return "Very low confidence"
    
    def _analyze_coordinates(self, x: float, y: float, z: float, category: str) -> str:
        """Analyze coordinates for human description"""
        # Distance from origin
        distance = (x**2 + z**2)**0.5
        
        # Quadrant
        if x >= 0 and z >= 0:
            quadrant = "northeast"
        elif x < 0 and z >= 0:
            quadrant = "northwest"
        elif x < 0 and z < 0:
            quadrant = "southwest"
        else:
            quadrant = "southeast"
        
        # Altitude description
        if category.upper() == "AIR":
            if y < 100:
                alt_desc = "low altitude"
            elif y < 500:
                alt_desc = "medium altitude"
            else:
                alt_desc = "high altitude"
        else:
            if y < 10:
                alt_desc = "ground level"
            elif y < 50:
                alt_desc = "elevated"
            else:
                alt_desc = "high elevation"
        
        return f"{distance:.0f}m {quadrant}, {alt_desc}"
    
    def _get_speed_description(self, speed: float, category: str) -> str:
        """Get human-readable speed description"""
        if speed < 0.1:
            return "stationary"
        
        # Different speed scales for different entity types
        if category.upper() == "AIR":
            if speed < 50:
                return f"slow for aircraft ({speed:.0f} m/s)"
            elif speed < 150:
                return f"cruising speed ({speed:.0f} m/s)"
            else:
                return f"high speed ({speed:.0f} m/s)"
        elif category.upper() == "INFANTRY":
            if speed < 2:
                return f"walking pace ({speed:.1f} m/s)"
            elif speed < 5:
                return f"running ({speed:.1f} m/s)"
            else:
                return f"sprinting ({speed:.1f} m/s)"
        else:  # GROUND vehicles
            if speed < 10:
                return f"slow ({speed:.0f} m/s)"
            elif speed < 30:
                return f"moderate speed ({speed:.0f} m/s)"
            else:
                return f"fast ({speed:.0f} m/s)"
    
    def _get_heading_description(self, heading: float) -> str:
        """Get cardinal direction from heading"""
        # Normalize heading to 0-360
        heading = heading % 360
        
        directions = [
            (0, "north"), (45, "northeast"), (90, "east"), (135, "southeast"),
            (180, "south"), (225, "southwest"), (270, "west"), (315, "northwest")
        ]
        
        # Find closest direction
        min_diff = float('inf')
        best_direction = "north"
        
        for angle, direction in directions:
            diff = min(abs(heading - angle), 360 - abs(heading - angle))
            if diff < min_diff:
                min_diff = diff
                best_direction = direction
        
        return f"{best_direction} ({heading:.0f}°)"
    
    def _get_cardinal_direction(self, heading: float) -> str:
        """Get simple cardinal direction"""
        heading = heading % 360
        
        if heading < 22.5 or heading >= 337.5:
            return "north"
        elif heading < 67.5:
            return "northeast"
        elif heading < 112.5:
            return "east"
        elif heading < 157.5:
            return "southeast"
        elif heading < 202.5:
            return "south"
        elif heading < 247.5:
            return "southwest"
        elif heading < 292.5:
            return "west"
        else:
            return "northwest"
    
    def _humanize_despawn_reason(self, reason: str) -> str:
        """Convert despawn reason to human-readable format"""
        reasons = {
            "SIMULATION_ENDED": "Simulation ended",
            "MANUAL_CLEAR": "Manually cleared",
            "OUT_OF_BOUNDS": "Left operational area",
            "TIMEOUT": "Connection timeout",
            "DESTROYED": "Entity destroyed",
            "LANDED": "Aircraft landed",
            "MISSION_COMPLETE": "Mission completed"
        }
        
        return reasons.get(reason.upper(), reason.replace("_", " ").title())
    
    def _get_age_description(self, age_seconds: float) -> str:
        """Get human-readable age description"""
        if age_seconds < 1:
            return "just now"
        elif age_seconds < 60:
            return f"{age_seconds:.0f} seconds ago"
        elif age_seconds < 3600:
            minutes = age_seconds / 60
            return f"{minutes:.0f} minutes ago"
        else:
            hours = age_seconds / 3600
            return f"{hours:.1f} hours ago"
    
    def _display_periodic_stats(self):
        """Display periodic statistics"""
        if not self.stats["start_time"]:
            return
        
        uptime = time.time() - self.stats["start_time"]
        rate = self.stats["messages_received"] / uptime if uptime > 0 else 0
        
        print(f"\n📊 STATS: {self.stats['messages_received']} msgs | "
              f"{rate:.1f} msgs/s | {len(self.last_entities)} entities | "
              f"Uptime: {uptime:.0f}s")
    
    def _display_final_stats(self):
        """Display final statistics"""
        if not self.stats["start_time"]:
            return
        
        uptime = time.time() - self.stats["start_time"]
        rate = self.stats["messages_received"] / uptime if uptime > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 FINAL STATISTICS")
        print("=" * 60)
        print(f"Total Messages Received: {self.stats['messages_received']}")
        print(f"Average Rate: {rate:.2f} messages/second")
        print(f"Total Runtime: {uptime:.1f} seconds")
        print(f"Connection Attempts: {self.stats['connection_attempts']}")
        print(f"Connection Errors: {self.stats['connection_errors']}")
        print(f"Active Entities: {len(self.last_entities)}")
        
        if self.stats["messages_by_type"]:
            print("\nMessage Types:")
            for msg_type, count in sorted(self.stats["messages_by_type"].items()):
                percentage = (count / self.stats["messages_received"]) * 100
                print(f"  {msg_type}: {count} ({percentage:.1f}%)")
        
        if self.entity_count:
            print("\nEntity Types Seen:")
            for entity_type, count in sorted(self.entity_count.items()):
                print(f"  {entity_type}: {count}")
        
        print("\n✅ Listener stopped gracefully")

    def _display_compact_entity_info(self, entity_data: Dict[str, Any], prefix: str = ""):
        """Display compact entity information"""
        # Handle both old and new entity data formats
        if isinstance(entity_data, str):
            print(f"❌ Debug: entity_data is string: '{entity_data}'")
            return
        elif not isinstance(entity_data, dict):
            print(f"❌ Debug: entity_data is {type(entity_data)}: {entity_data}")
            return
        
        # Handle new compact format (flat structure)
        if "id" in entity_data and "d" in entity_data:
            entity_id = entity_data.get("id", "unknown")
            callsign = entity_data.get("n", "unknown")
            disposition = entity_data.get("d", "U")
            model = entity_data.get("m", "")
            
            # Get disposition info
            disp_icon, disp_desc = self._get_disposition_info(disposition)
            
            type_icon = "❓"  # New format doesn't include type info
            print(f"{prefix}   {type_icon} Entity: {entity_id[:8]}...")
            print(f"{prefix}   📻 Callsign: {callsign}")
            if model:
                print(f"{prefix}   🚗 Model: {model}")
            print(f"{prefix}   {disp_icon} Disposition: {disp_desc}")
            
            # Position if available
            if "p" in entity_data:
                pos = entity_data["p"]
                if isinstance(pos, list) and len(pos) >= 3:
                    x, y, z = pos[0], pos[1], pos[2]
                    distance = (x**2 + z**2)**0.5
                    print(f"{prefix}   📍 Position: ({x:.0f}, {y:.0f}, {z:.0f}) - {distance:.0f}m from origin")
            
            # Velocity if available
            if "v" in entity_data:
                vel = entity_data["v"]
                if isinstance(vel, list) and len(vel) >= 3:
                    speed, heading, climb_rate = vel[0], vel[1], vel[2]
                    print(f"{prefix}   🧭 Movement: {speed:.0f} m/s, heading {heading:.0f}°")
                    if abs(climb_rate) > 1:
                        climb_desc = "climbing" if climb_rate > 0 else "descending"
                        print(f"{prefix}      ✈  {climb_desc} at {abs(climb_rate):.0f} m/s")
            
            return
            
        # Handle old compact format (nested structure)
        entity_id = entity_data.get("id", entity_data.get("eId", "unknown"))
        
        # Entity type info with icons
        entity_type = entity_data.get("eT", {})
        category = entity_type.get("c", "unknown")
        subcategory = entity_type.get("s", "")
        specification = entity_type.get("sp", "")
        
        # Get appropriate icon for entity type
        type_icon = self._get_entity_icon(category, subcategory)
        
        print(f"{prefix}{type_icon} Entity: {entity_id[:8]}...")
        print(f"{prefix}   Type: {self._humanize_entity_type(category, subcategory, specification)}")
        
        # Callsign and unit name
        if "cs" in entity_data:
            print(f"{prefix}   📻 Callsign: {entity_data['cs']}")
        if "un" in entity_data:
            print(f"{prefix}   🏷️  Unit: {entity_data['un']}")
        
        # Disposition
        if "d" in entity_data:
            disp = entity_data["d"]
            affiliation = disp.get('a', 'unknown')
            confidence = disp.get('c', 1.0)
            disp_icon, disp_desc = self._get_disposition_info(affiliation)
            conf_desc = self._get_confidence_description(confidence)
            print(f"{prefix}   {disp_icon} Disposition: {disp_desc} ({conf_desc})")
        
        # Kinematics
        if "k" in entity_data:
            kinematics = entity_data["k"]
            pos = kinematics.get("p", {})
            vel = kinematics.get("v", {})
            
            # Position
            x, y, z = pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)
            coord_desc = self._analyze_coordinates(x, y, z, category)
            print(f"{prefix}   📍 Position: {coord_desc}")
            print(f"{prefix}      Coordinates: ({x:.1f}, {y:.1f}, {z:.1f})")
            
            # Velocity
            speed = vel.get('s', 0)
            heading = vel.get('h', 0)
            climb_rate = vel.get('cr', 0)
            
            speed_desc = self._get_speed_description(speed, category)
            heading_desc = self._get_heading_description(heading)
            
            print(f"{prefix}   🧭 Movement: {speed_desc}, heading {heading_desc}")
            if abs(climb_rate) > 0.1:
                climb_desc = "climbing" if climb_rate > 0 else "descending"
                print(f"{prefix}      ✈️  {climb_desc} at {abs(climb_rate):.1f} m/s")
        
        # Timestamps if available
        if "ts" in entity_data:
            timestamp = entity_data["ts"]
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age = (datetime.now(timezone.utc) - dt).total_seconds()
                age_desc = self._get_age_description(age)
                print(f"{prefix}   🕐 Data age: {age_desc}")
            except:
                print(f"{prefix}   🕐 Timestamp: {timestamp}")

    def _analyze_compact_movement(self, kinematics: Dict[str, Any]):
        """Analyze compact movement patterns"""
        vel = kinematics.get("v", {})
        speed = vel.get("s", 0)
        heading = vel.get("h", 0)
        climb_rate = vel.get("cr", 0)
        
        # Movement analysis
        movement_type = "stationary"
        if speed > 0.1:
            if speed < 5:
                movement_type = "slow movement"
            elif speed < 20:
                movement_type = "moderate speed"
            elif speed < 50:
                movement_type = "fast movement"
            else:
                movement_type = "high speed"
        
        print(f"   🏃 Movement Analysis: {movement_type}")
        
        # Direction analysis
        if speed > 0.1:
            direction = self._get_cardinal_direction(heading)
            print(f"   🧭 Heading: {direction} ({heading:.0f}°)")
        
        # Altitude change
        if abs(climb_rate) > 0.5:
            alt_change = "climbing rapidly" if climb_rate > 5 else "climbing"
            if climb_rate < 0:
                alt_change = "descending rapidly" if climb_rate < -5 else "descending"
            print(f"   ⬆️  Altitude: {alt_change} ({climb_rate:+.1f} m/s)")

    def _display_batch_entity_info(self, entity_data: Dict[str, Any], prefix: str = ""):
        """Display simplified batch entity information"""
        # Handle both old and new entity data formats
        if isinstance(entity_data, str):
            print(f"{prefix}❌ Error: entity_data is a string instead of dict")
            return
        
        entity_id = entity_data.get("entityId", "unknown")
        unit_name = entity_data.get("unitName", "")
        disposition = entity_data.get("disposition", "U")
        
        # Get disposition info
        disp_icon, disp_desc = self._get_disposition_info(disposition)
        
        print(f"{prefix}🔸 Entity: {entity_id[:12]}...")
        if unit_name:
            print(f"{prefix}   🏷️  Unit: {unit_name}")
        print(f"{prefix}   {disp_icon} Disposition: {disp_desc}")
        
        # Position if available
        if "position" in entity_data:
            pos = entity_data["position"]
            x, y, z = pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)
            distance = (x**2 + z**2)**0.5
            print(f"{prefix}   📍 Position: ({x:.0f}, {y:.0f}, {z:.0f}) - {distance:.0f}m from origin")
        
        # Velocity if available
        if "velocity" in entity_data:
            vel = entity_data["velocity"]
            speed = vel.get('speed', 0)
            heading = vel.get('heading', 0)
            print(f"{prefix}   🧭 Movement: {speed:.0f} m/s, heading {heading:.0f}°")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="TEDF Message Listener - Listen to battlespace simulator broadcasts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Display Modes:
  raw     - Show raw JSON messages
  pretty  - Show formatted, detailed messages
  compact - Show one-line summaries
  stats   - Show only periodic statistics

Examples:
  %(prog)s                                    # Listen with default settings
  %(prog)s -p 5556 -m compact                # Listen on port 5556, compact mode
  %(prog)s -a tcp://192.168.1.100 -f full   # Connect to remote host, show only full messages
  %(prog)s -m raw --no-timestamps            # Raw mode without timestamps
        """
    )
    
    parser.add_argument("-a", "--address", default="tcp://localhost",
                       help="ZMQ address to connect to (default: tcp://localhost)")
    parser.add_argument("-p", "--port", type=int, default=5555,
                       help="ZMQ port to connect to (default: 5555)")
    parser.add_argument("-m", "--mode", choices=["raw", "pretty", "compact", "stats"],
                       default="pretty", help="Display mode (default: pretty)")
    parser.add_argument("-f", "--filter", choices=["full", "compact", "batch", "despawn"],
                       help="Filter to show only specific message types")
    parser.add_argument("--no-timestamps", action="store_true",
                       help="Don't show timestamps")
    parser.add_argument("--stats-interval", type=int, default=10,
                       help="Statistics display interval in seconds (default: 10)")
    
    args = parser.parse_args()
    
    # Create and start listener
    listener = TEDFMessageListener(
        address=args.address,
        port=args.port,
        display_mode=args.mode,
        filter_type=args.filter
    )
    
    # Configure display settings
    listener.show_timestamps = not args.no_timestamps
    listener.show_stats_interval = args.stats_interval
    
    # Start listening
    try:
        success = listener.start_listening()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        listener.stop_listening()
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())