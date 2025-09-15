import json
import time
import uuid
import socket
import threading
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Union
from enum import Enum
import struct

class Disposition(Enum):
    FRIENDLY = "FRIENDLY"
    ENEMY = "ENEMY"
    HOSTILE = "HOSTILE"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"

class TrackQuality(Enum):
    FIRM = "FIRM"
    TENTATIVE = "TENTATIVE"
    WEAK = "WEAK"

# Data classes for TEDF messages
@dataclass
class TEDFHeader:
    message_id: str
    version: str = "1.0"
    timestamp: str = ""
    classification: str = "UNCLASSIFIED"
    originator_id: str = "SENSOR-DEFAULT"
    network_id: str = "TACNET-MAIN"
    priority: int = 3
    ttl: int = 300

@dataclass
class EntityType:
    category: str = "GROUND"
    subcategory: str = "VEHICLE"
    specification: str = "UNKNOWN"

@dataclass
class EntityDisposition:
    affiliation: str
    confidence: float = 0.5
    rules: List[str] = field(default_factory=lambda: ["SPEED_PROFILE", "MOVEMENT_PATTERN"])

@dataclass
class Position:
    x: float
    y: float
    z: float
    coordinate_system: str = "UNITY_WORLD"
    datum: str = "LOCAL_GRID"

@dataclass
class Velocity:
    speed: float
    heading: float
    climb_rate: float = 0.0

@dataclass
class Kinematics:
    position: Position
    velocity: Velocity

@dataclass
class Detection:
    sensor_type: str = "RADAR"
    detection_time: str = ""
    signal_strength: float = 0.5
    track_quality: str = "TENTATIVE"
    last_update: str = ""

@dataclass
class Entity:
    entity_id: str
    unit_name: str
    callsign: str
    type: EntityType
    disposition: EntityDisposition
    kinematics: Kinematics
    detection: Detection

@dataclass
class TEDFMessage:
    header: TEDFHeader
    entity: Entity

# Compact message classes
@dataclass
class CompactHeader:
    id: str = "TEDF-COMPACT"
    t: int = 0  # timestamp
    o: str = "S-DEFAULT"  # originator

@dataclass
class CompactEntity:
    id: str
    n: str  # name/callsign
    d: str  # disposition
    p: List[float]  # position [x, y, z]
    v: List[float]  # velocity [speed, heading, climb_rate]
    q: float  # quality/signal strength

@dataclass
class CompactMessage:
    h: CompactHeader
    e: CompactEntity

class TEDFHandler:
    """Handler for creating and parsing TEDF messages"""
    
    DISPOSITION_TO_COMPACT = {
        Disposition.FRIENDLY: "F",
        Disposition.ENEMY: "H",
        Disposition.HOSTILE: "H",
        Disposition.NEUTRAL: "N",
        Disposition.UNKNOWN: "U"
    }
    
    COMPACT_TO_DISPOSITION = {
        "F": Disposition.FRIENDLY,
        "H": Disposition.ENEMY,
        "N": Disposition.NEUTRAL,
        "U": Disposition.UNKNOWN
    }
    
    def __init__(self):
        self.message_counter = 0
    
    def generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = int(time.time() * 1000)
        unique = str(uuid.uuid4())[:4].upper()
        return f"TEDF-{timestamp}-{unique}"
    
    def get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    def calculate_priority(self, disposition: Disposition) -> int:
        """Calculate message priority based on disposition"""
        priority_map = {
            Disposition.ENEMY: 1,
            Disposition.HOSTILE: 1,
            Disposition.UNKNOWN: 2,
            Disposition.NEUTRAL: 3,
            Disposition.FRIENDLY: 4
        }
        return priority_map.get(disposition, 3)
    
    def get_track_quality(self, signal_strength: float) -> TrackQuality:
        """Determine track quality from signal strength"""
        if signal_strength > 0.8:
            return TrackQuality.FIRM
        elif signal_strength > 0.5:
            return TrackQuality.TENTATIVE
        return TrackQuality.WEAK
    
    def generate_full_message(
        self,
        entity_id: str,
        unit_name: str,
        position: Tuple[float, float, float],
        speed: float,
        heading: float,
        disposition: Disposition,
        sensor_id: str = "SENSOR-DEFAULT",
        confidence: float = 0.75,
        signal_strength: float = 0.8,
        sensor_type: str = "RADAR"
    ) -> TEDFMessage:
        """Generate a full TEDF message"""
        
        timestamp = self.get_timestamp()
        
        header = TEDFHeader(
            message_id=self.generate_message_id(),
            timestamp=timestamp,
            originator_id=sensor_id,
            priority=self.calculate_priority(disposition)
        )
        
        entity = Entity(
            entity_id=entity_id,
            unit_name=unit_name,
            callsign=unit_name,
            type=EntityType(),
            disposition=EntityDisposition(
                affiliation=disposition.value,
                confidence=confidence
            ),
            kinematics=Kinematics(
                position=Position(x=position[0], y=position[1], z=position[2]),
                velocity=Velocity(speed=speed, heading=heading)
            ),
            detection=Detection(
                sensor_type=sensor_type,
                detection_time=timestamp,
                signal_strength=signal_strength,
                track_quality=self.get_track_quality(signal_strength).value,
                last_update=timestamp
            )
        )
        
        return TEDFMessage(header=header, entity=entity)
    
    def generate_compact_message(
        self,
        entity_id: str,
        callsign: str,
        position: Tuple[float, float, float],
        speed: float,
        heading: float,
        disposition: Disposition,
        sensor_id: str = "S-DEFAULT",
        signal_strength: float = 0.8
    ) -> CompactMessage:
        """Generate a compact TEDF message for high-frequency updates"""
        
        return CompactMessage(
            h=CompactHeader(
                t=int(time.time() * 1000),
                o=sensor_id
            ),
            e=CompactEntity(
                id=entity_id,
                n=callsign,
                d=self.DISPOSITION_TO_COMPACT[disposition],
                p=[position[0], position[1], position[2]],
                v=[speed, heading, 0.0],
                q=signal_strength
            )
        )
    
    def serialize_message(self, message: Union[TEDFMessage, CompactMessage]) -> str:
        """Serialize message to JSON string"""
        return json.dumps(self._message_to_dict(message), separators=(',', ':'))
    
    def _message_to_dict(self, obj) -> dict:
        """Convert dataclass to dictionary with proper field names"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_def in obj.__dataclass_fields__.items():
                value = getattr(obj, field_name)
                # Convert field names from snake_case to camelCase
                json_field_name = ''.join(word.capitalize() if i > 0 else word 
                                         for i, word in enumerate(field_name.split('_')))
                result[json_field_name] = self._message_to_dict(value)
            return result
        elif isinstance(obj, list):
            return [self._message_to_dict(item) for item in obj]
        elif isinstance(obj, Enum):
            return obj.value
        else:
            return obj
    
    def parse_message(self, json_str: str) -> Union[TEDFMessage, CompactMessage, None]:
        """Parse JSON string to appropriate message type"""
        try:
            data = json.loads(json_str)
            
            # Check message type
            if 'h' in data and 'e' in data:
                return self._parse_compact_message(data)
            elif 'header' in data and 'entity' in data:
                return self._parse_full_message(data)
            else:
                raise ValueError("Unknown message format")
                
        except Exception as e:
            print(f"Failed to parse message: {e}")
            return None
    
    def _parse_compact_message(self, data: dict) -> CompactMessage:
        """Parse compact message from dictionary"""
        header = CompactHeader(
            id=data['h']['id'],
            t=data['h']['t'],
            o=data['h']['o']
        )
        
        entity = CompactEntity(
            id=data['e']['id'],
            n=data['e']['n'],
            d=data['e']['d'],
            p=data['e']['p'],
            v=data['e']['v'],
            q=data['e']['q']
        )
        
        return CompactMessage(h=header, e=entity)
    
    def _parse_full_message(self, data: dict) -> TEDFMessage:
        """Parse full message from dictionary"""
        # Implementation would parse all fields - simplified for brevity
        # In production, use a proper JSON schema validator
        return TEDFMessage(
            header=TEDFHeader(
                message_id=data['header']['messageId'],
                version=data['header'].get('version', '1.0'),
                timestamp=data['header']['timestamp']
            ),
            entity=Entity(
                entity_id=data['entity']['entityId'],
                unit_name=data['entity']['unitName'],
                callsign=data['entity']['callsign'],
                type=EntityType(),
                disposition=EntityDisposition(
                    affiliation=data['entity']['disposition']['affiliation']
                ),
                kinematics=Kinematics(
                    position=Position(
                        x=data['entity']['kinematics']['position']['x'],
                        y=data['entity']['kinematics']['position']['y'],
                        z=data['entity']['kinematics']['position']['z']
                    ),
                    velocity=Velocity(
                        speed=data['entity']['kinematics']['velocity']['speed'],
                        heading=data['entity']['kinematics']['velocity']['heading']
                    )
                ),
                detection=Detection()
            )
        )
    
    def extract_entity_data(self, message: Union[TEDFMessage, CompactMessage]) -> dict:
        """Extract key entity data from any message type"""
        if isinstance(message, CompactMessage):
            return {
                'id': message.e.id,
                'name': message.e.n,
                'position': {'x': message.e.p[0], 'y': message.e.p[1], 'z': message.e.p[2]},
                'speed': message.e.v[0],
                'heading': message.e.v[1],
                'disposition': self.COMPACT_TO_DISPOSITION[message.e.d],
                'signal_strength': message.e.q
            }
        else:
            return {
                'id': message.entity.entity_id,
                'name': message.entity.unit_name,
                'position': {
                    'x': message.entity.kinematics.position.x,
                    'y': message.entity.kinematics.position.y,
                    'z': message.entity.kinematics.position.z
                },
                'speed': message.entity.kinematics.velocity.speed,
                'heading': message.entity.kinematics.velocity.heading,
                'disposition': Disposition(message.entity.disposition.affiliation),
                'signal_strength': message.entity.detection.signal_strength
            }

class TEDFNetworkSimulator:
    """Simulates network transmission of TEDF messages"""
    
    def __init__(self, handler: TEDFHandler):
        self.handler = handler
        self.multicast_group = '224.1.1.1'
        self.port = 5007
        self.running = False
        
    def broadcast_message(self, message: Union[TEDFMessage, CompactMessage]):
        """Broadcast message over multicast"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        json_data = self.handler.serialize_message(message)
        sock.sendto(json_data.encode('utf-8'), (self.multicast_group, self.port))
        sock.close()
        
        print(f"Broadcast message: {json_data[:100]}...")
    
    def receive_messages(self, callback):
        """Receive messages from multicast group"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.port))
        
        # Join multicast group
        mreq = struct.pack('4sl', socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        self.running = True
        while self.running:
            try:
                data, addr = sock.recvfrom(4096)
                message = self.handler.parse_message(data.decode('utf-8'))
                if message:
                    callback(message, addr)
            except Exception as e:
                print(f"Receive error: {e}")
        
        sock.close()

class EntityTracker:
    """Tracks and manages tactical entities"""
    
    def __init__(self):
        self.entities: Dict[str, dict] = {}
        self.handler = TEDFHandler()
        
    def update_entity(self, message: Union[TEDFMessage, CompactMessage]):
        """Update entity based on received message"""
        entity_data = self.handler.extract_entity_data(message)
        entity_id = entity_data['id']
        
        if entity_id not in self.entities:
            print(f"New entity detected: {entity_data['name']} ({entity_data['disposition'].value})")
        
        self.entities[entity_id] = {
            **entity_data,
            'last_update': time.time()
        }
    
    def get_entities_by_disposition(self, disposition: Disposition) -> List[dict]:
        """Get all entities with specific disposition"""
        return [e for e in self.entities.values() if e['disposition'] == disposition]
    
    def remove_stale_entities(self, max_age_seconds: float = 300):
        """Remove entities that haven't been updated recently"""
        current_time = time.time()
        stale_ids = [
            entity_id for entity_id, data in self.entities.items()
            if current_time - data['last_update'] > max_age_seconds
        ]
        
        for entity_id in stale_ids:
            print(f"Removing stale entity: {entity_id}")
            del self.entities[entity_id]

# Example usage
def main():
    # Create handler and tracker
    handler = TEDFHandler()
    tracker = EntityTracker()
    
    # Example 1: Generate and parse full message
    print("=== Full Message Example ===")
    full_msg = handler.generate_full_message(
        entity_id="TRK-2024-1001",
        unit_name="ALPHA-TANK-01",
        position=(1500.5, 105.2, -2200.8),
        speed=12.5,
        heading=135.0,
        disposition=Disposition.UNKNOWN,
        sensor_id="RADAR-NORTH-01",
        confidence=0.72,
        signal_strength=0.85
    )
    
    full_json = handler.serialize_message(full_msg)
    print(f"Full message JSON:\n{json.dumps(json.loads(full_json), indent=2)}\n")
    
    # Example 2: Generate and parse compact message
    print("=== Compact Message Example ===")
    compact_msg = handler.generate_compact_message(
        entity_id="TRK-2024-1001",
        callsign="ALPHA-1",
        position=(1500.5, 105.2, -2200.8),
        speed=12.5,
        heading=135.0,
        disposition=Disposition.UNKNOWN,
        signal_strength=0.85
    )
    
    compact_json = handler.serialize_message(compact_msg)
    print(f"Compact message JSON:\n{compact_json}\n")
    
    # Parse the message
    parsed = handler.parse_message(compact_json)
    if parsed:
        entity_data = handler.extract_entity_data(parsed)
        print(f"Parsed entity data:\n{json.dumps(entity_data, default=str, indent=2)}\n")
    
    # Example 3: Simulate entity tracking
    print("=== Entity Tracking Example ===")
    
    # Simulate receiving multiple messages
    entities = [
        ("TRK-2024-2001", "FRIENDLY-APC-01", (1000, 100, -1500), 20, 90, Disposition.FRIENDLY),
        ("TRK-2024-2002", "ENEMY-TANK-01", (2500, 105, -1200), 15, 270, Disposition.ENEMY),
        ("TRK-2024-2003", "UNKNOWN-VEH-01", (1800, 102, -1800), 25, 45, Disposition.UNKNOWN),
    ]
    
    for entity_data in entities:
        msg = handler.generate_compact_message(*entity_data)
        tracker.update_entity(msg)
    
    # Display tracked entities
    print(f"Total tracked entities: {len(tracker.entities)}")
    for disposition in Disposition:
        entities = tracker.get_entities_by_disposition(disposition)
        if entities:
            print(f"\n{disposition.value} entities ({len(entities)}):")
            for entity in entities:
                print(f"  - {entity['name']} at ({entity['position']['x']:.1f}, "
                      f"{entity['position']['y']:.1f}, {entity['position']['z']:.1f})")
    
    # Example 4: Batch processing
    print("\n=== Batch Processing Example ===")
    
    batch_messages = []
    for i in range(5):
        msg = handler.generate_compact_message(
            entity_id=f"TRK-2024-300{i}",
            callsign=f"CONVOY-{i+1}",
            position=(1000 + i*50, 100, -2000),
            speed=25.0,
            heading=90.0,
            disposition=Disposition.FRIENDLY
        )
        batch_messages.append(handler.serialize_message(msg))
    
    batch_json = json.dumps({
        "batch": {
            "batchId": f"BATCH-{int(time.time())}",
            "timestamp": handler.get_timestamp(),
            "entityCount": len(batch_messages),
            "messages": batch_messages
        }
    })
    
    print(f"Batch message with {len(batch_messages)} entities")
    print(f"Total size: {len(batch_json)} bytes")

if __name__ == "__main__":
    main()