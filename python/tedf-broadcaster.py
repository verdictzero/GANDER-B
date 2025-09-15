"""
TEDF Message Broadcaster
Generates and broadcasts TEDF messages via ZeroMQ for Unity consumption
"""

import json
import time
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import zmq
import logging
import socket
import psutil
import os
import signal
import subprocess
import socket


class MessageType(Enum):
    FULL = "full"
    COMPACT = "compact"
    BATCH = "batch"
    DESPAWN = "despawn"


class DispositionCode(Enum):
    FRIENDLY = "F"
    HOSTILE = "H"
    NEUTRAL = "N"
    UNKNOWN = "U"


@dataclass
class Position:
    x: float
    y: float
    z: float
    coordinate_system: str = "UNITY_WORLD"
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "coordinateSystem": self.coordinate_system
        }


@dataclass
class Velocity:
    speed: float
    heading: float
    climb_rate: float = 0.0
    
    def to_dict(self):
        return {
            "speed": self.speed,
            "heading": self.heading,
            "climbRate": self.climb_rate
        }


@dataclass
class Kinematics:
    position: Position
    velocity: Velocity
    
    def to_dict(self):
        return {
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict()
        }


@dataclass
class EntityType:
    category: str
    subcategory: str
    specification: str
    
    def to_dict(self):
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "specification": self.specification
        }


@dataclass
class Disposition:
    affiliation: str
    confidence: float = 1.0
    
    def to_dict(self):
        return {
            "affiliation": self.affiliation,
            "confidence": self.confidence
        }


@dataclass
class TEDFHeader:
    message_id: str
    version: str = "1.0"
    timestamp: str = None
    originator_id: str = "PYTHON-SIMULATOR-01"
    priority: int = 2
    ttl: int = 300
    message_type: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self):
        result = {
            "messageId": self.message_id,
            "version": self.version,
            "timestamp": self.timestamp,
            "originatorId": self.originator_id,
            "priority": self.priority,
            "ttl": self.ttl
        }
        if self.message_type:
            result["messageType"] = self.message_type
        return result


@dataclass
class TEDFEntity:
    entity_id: str
    unit_name: str
    callsign: str
    entity_type: EntityType
    disposition: Disposition
    kinematics: Kinematics
    model: str = ""
    reason: str = None
    
    def to_dict(self):
        result = {
            "entityId": self.entity_id,
            "unitName": self.unit_name,
            "callsign": self.callsign,
            "type": self.entity_type.to_dict(),
            "disposition": self.disposition.to_dict(),
            "kinematics": self.kinematics.to_dict()
        }
        if self.model:
            result["model"] = self.model
        if self.reason:
            result["reason"] = self.reason
        return result


class TEDFBroadcaster:
    """Handles TEDF message generation and ZeroMQ broadcasting"""
    
    def __init__(self, port: int = 5555, update_rate: float = 2.0):
        self.port = port
        self.update_rate = update_rate
        self.is_broadcasting = False
        self.message_counter = 0
        
        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = None
        
        # Broadcasting thread
        self.broadcast_thread = None
        self.stop_event = threading.Event()
        
        # Message queues
        self.pending_full_messages = []
        self.pending_compact_messages = []
        self.pending_batch_messages = []
        self.pending_despawn_messages = []
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "full_messages_sent": 0,
            "compact_messages_sent": 0,
            "batch_messages_sent": 0,
            "despawn_messages_sent": 0,
            "errors": 0,
            "start_time": None,
            "last_message_time": None
        }
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def set_update_rate(self, rate: float):
        """Set broadcast update rate with validation"""
        if rate <= 0:
            self.logger.warning(f"Update rate must be positive, got {rate}. Using minimum 0.1")
            rate = 0.1
        
        old_rate = self.update_rate
        self.update_rate = rate
        self.logger.info(f"Broadcast update rate changed from {old_rate:.2f} to {rate:.2f}")
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
    
    def _find_processes_using_port(self, port: int) -> List[Dict[str, Any]]:
        """Find processes using the specified port"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
                try:
                    connections = proc.info['connections']
                    if connections:
                        for conn in connections:
                            if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                                processes.append({
                                    'pid': proc.info['pid'],
                                    'name': proc.info['name'],
                                    'cmdline': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else '',
                                    'connection': conn
                                })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            self.logger.warning(f"Error finding processes using port {port}: {e}")
        return processes
    
    def _cleanup_orphaned_zmq_processes(self, port: int) -> bool:
        """Clean up orphaned ZMQ processes on the specified port"""
        self.logger.info(f"Searching for orphaned processes on port {port}...")
        
        processes = self._find_processes_using_port(port)
        if not processes:
            self.logger.info(f"No processes found using port {port}")
            return True
        
        cleaned_count = 0
        for proc_info in processes:
            pid = proc_info['pid']
            name = proc_info['name']
            cmdline = proc_info['cmdline']
            
            # Check if it's likely a Python ZMQ process
            is_python_zmq = (
                'python' in name.lower() or 
                'python' in cmdline.lower() or
                'tedf' in cmdline.lower() or
                'battlespace' in cmdline.lower() or
                'zmq' in cmdline.lower()
            )
            
            if is_python_zmq:
                self.logger.warning(f"Found orphaned process: PID {pid}, Name: {name}, Command: {cmdline[:100]}...")
                try:
                    # Try graceful termination first
                    proc = psutil.Process(pid)
                    proc.terminate()
                    
                    # Wait up to 3 seconds for graceful termination
                    try:
                        proc.wait(timeout=3)
                        self.logger.info(f"Successfully terminated process {pid}")
                        cleaned_count += 1
                    except psutil.TimeoutExpired:
                        # Force kill if graceful termination failed
                        self.logger.warning(f"Process {pid} didn't terminate gracefully, forcing kill...")
                        proc.kill()
                        proc.wait(timeout=1)
                        self.logger.info(f"Force killed process {pid}")
                        cleaned_count += 1
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.logger.warning(f"Could not terminate process {pid}: {e}")
            else:
                self.logger.info(f"Process {pid} ({name}) is using port {port} but doesn't appear to be a ZMQ process")
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} orphaned process(es) on port {port}")
            # Give the system a moment to clean up
            time.sleep(1)
            return True
        
        return cleaned_count == 0
    
    def _force_release_zmq_port(self, port: int) -> bool:
        """Force release a ZMQ port using system commands"""
        try:
            # Try using lsof to find and kill processes
            try:
                result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    self.logger.info(f"Found PIDs using port {port}: {pids}")
                    
                    for pid in pids:
                        if pid.strip():
                            try:
                                # Try SIGTERM first
                                os.kill(int(pid), signal.SIGTERM)
                                time.sleep(0.5)
                                # Then SIGKILL if needed
                                try:
                                    os.kill(int(pid), signal.SIGKILL)
                                except ProcessLookupError:
                                    pass  # Process already terminated
                                self.logger.info(f"Killed process {pid}")
                            except (ValueError, ProcessLookupError, PermissionError) as e:
                                self.logger.warning(f"Could not kill process {pid}: {e}")
                    
                    time.sleep(1)
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.debug("lsof command not available or timed out")
            
            # Fallback: try netstat approach
            try:
                result = subprocess.run(['netstat', '-tlnp'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port} ' in line and 'LISTEN' in line:
                            parts = line.split()
                            if len(parts) > 6 and '/' in parts[6]:
                                pid = parts[6].split('/')[0]
                                try:
                                    os.kill(int(pid), signal.SIGKILL)
                                    self.logger.info(f"Killed process {pid} using netstat method")
                                    time.sleep(1)
                                    return True
                                except (ValueError, ProcessLookupError, PermissionError) as e:
                                    self.logger.warning(f"Could not kill process {pid}: {e}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.debug("netstat command not available or timed out")
        
        except Exception as e:
            self.logger.error(f"Error in force_release_zmq_port: {e}")
        
        return False
    
    def _attempt_port_recovery(self, port: int, max_attempts: int = 3) -> bool:
        """Attempt to recover a port through multiple cleanup strategies"""
        self.logger.info(f"Attempting to recover port {port}...")
        
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"Recovery attempt {attempt}/{max_attempts}")
            
            # Strategy 1: Check if port is actually available now
            if self._is_port_available(port):
                self.logger.info(f"Port {port} is now available")
                return True
            
            # Strategy 2: Clean up orphaned processes
            if self._cleanup_orphaned_zmq_processes(port):
                if self._is_port_available(port):
                    self.logger.info(f"Port {port} recovered after orphan cleanup")
                    return True
            
            # Strategy 3: Force release using system commands
            if self._force_release_zmq_port(port):
                if self._is_port_available(port):
                    self.logger.info(f"Port {port} recovered after force release")
                    return True
            
            # Strategy 4: Try a different ZMQ context
            if attempt < max_attempts:
                self.logger.info(f"Attempt {attempt} failed, waiting 2 seconds before next attempt...")
                time.sleep(2)
                
                # Recreate ZMQ context
                try:
                    old_context = self.context
                    self.context = zmq.Context()
                    old_context.term()
                    self.logger.info("Recreated ZMQ context")
                except Exception as e:
                    self.logger.warning(f"Error recreating ZMQ context: {e}")
        
        self.logger.error(f"Failed to recover port {port} after {max_attempts} attempts")
        return False
    
    def start_broadcasting(self) -> bool:
        """Start the ZeroMQ broadcaster"""
        if self.is_broadcasting:
            self.logger.warning("Broadcasting is already active")
            return False
        
        # Check if port is available, attempt recovery if not
        if not self._is_port_available(self.port):
            self.logger.warning(f"Port {self.port} is not available, attempting automatic recovery...")
            
            # Attempt to recover the port
            if not self._attempt_port_recovery(self.port):
                self.logger.error(f"Failed to recover port {self.port}. Manual intervention may be required.")
                return False
            
            self.logger.info(f"Successfully recovered port {self.port}")
        
        try:
            # Ensure any existing socket is properly closed first
            self.cleanup()
            
            # Add small delay to allow OS to clean up previous socket
            time.sleep(0.1)
            
            # Setup ZeroMQ publisher socket
            self.socket = self.context.socket(zmq.PUB)
            
            # Set socket options for better cleanup and reuse
            self.socket.setsockopt(zmq.SNDHWM, 1000)  # Limit send buffer
            self.socket.setsockopt(zmq.LINGER, 0)     # Don't wait for pending messages on close
            
            # Try to bind to the port
            bind_address = f"tcp://*:{self.port}"
            self.socket.bind(bind_address)
            
            # Start broadcasting thread
            self.stop_event.clear()
            self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self.broadcast_thread.start()
            
            self.is_broadcasting = True
            self.stats["start_time"] = time.time()
            
            self.logger.info(f"TEDF Broadcasting started on port {self.port}")
            return True
            
        except zmq.ZMQError as e:
            if e.errno == zmq.EADDRINUSE:
                self.logger.error(f"Port {self.port} is already in use by ZMQ. Try stopping any running instances or using a different port.")
            else:
                self.logger.error(f"ZMQ Error starting broadcasting: {e}")
            self._cleanup_failed_socket()
            return False
        except Exception as e:
            self.logger.error(f"Failed to start broadcasting: {e}")
            self._cleanup_failed_socket()
            return False
    
    def _cleanup_failed_socket(self):
        """Clean up socket after failed start"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def stop_broadcasting(self):
        """Stop the ZeroMQ broadcaster"""
        if not self.is_broadcasting:
            return
        
        self.is_broadcasting = False
        self.stop_event.set()
        
        # Wait for broadcast thread to finish
        if self.broadcast_thread and self.broadcast_thread.is_alive():
            self.broadcast_thread.join(timeout=5.0)
            if self.broadcast_thread.is_alive():
                self.logger.warning("Broadcast thread did not terminate gracefully")
        
        # Clean up socket with proper error handling
        if self.socket:
            try:
                self.socket.setsockopt(zmq.LINGER, 0)  # Don't wait for pending messages
                self.socket.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None
        
        # Clean up context
        if hasattr(self, 'context') and self.context:
            try:
                self.context.term()
            except Exception as e:
                self.logger.error(f"Error terminating context: {e}")
        
        self.logger.info("TEDF Broadcasting stopped")
    
    def _broadcast_loop(self):
        """Main broadcasting loop running in separate thread"""
        # Prevent division by zero for update_rate
        safe_update_rate = max(0.1, self.update_rate)
        while not self.stop_event.wait(1.0 / safe_update_rate):
            try:
                self._process_message_queues()
            except Exception as e:
                self.logger.error(f"Error in broadcast loop: {e}")
                self.stats["errors"] += 1
    
    def _process_message_queues(self):
        """Process all pending message queues"""
        # Process despawn messages first (highest priority)
        while self.pending_despawn_messages:
            message = self.pending_despawn_messages.pop(0)
            self._send_message(message, MessageType.DESPAWN)
        
        # Process full messages
        while self.pending_full_messages:
            message = self.pending_full_messages.pop(0)
            self._send_message(message, MessageType.FULL)
        
        # Process batch messages
        while self.pending_batch_messages:
            message = self.pending_batch_messages.pop(0)
            self._send_message(message, MessageType.BATCH)
        
        # Process compact messages
        while self.pending_compact_messages:
            message = self.pending_compact_messages.pop(0)
            self._send_message(message, MessageType.COMPACT)
    
    def _send_message(self, message: str, message_type: MessageType):
        """Send a message via ZeroMQ"""
        if not self.socket or not self.is_broadcasting:
            return
        
        try:
            self.socket.send_string(message, zmq.NOBLOCK)
            
            # Update statistics
            self.stats["messages_sent"] += 1
            self.stats["last_message_time"] = time.time()
            
            if message_type == MessageType.FULL:
                self.stats["full_messages_sent"] += 1
            elif message_type == MessageType.COMPACT:
                self.stats["compact_messages_sent"] += 1
            elif message_type == MessageType.BATCH:
                self.stats["batch_messages_sent"] += 1
            elif message_type == MessageType.DESPAWN:
                self.stats["despawn_messages_sent"] += 1
            
            self.message_counter += 1
            
        except zmq.Again:
            # Socket would block, message queue is full
            self.logger.warning("Message queue full, dropping message")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.stats["errors"] += 1
    
    def generate_full_message(self, entity_data: Dict[str, Any]) -> str:
        """Generate a full TEDF message"""
        try:
            # Create header
            header = TEDFHeader(
                message_id=f"SIM-{datetime.now().strftime('%Y-%m-%d')}-{self.message_counter:04d}-{uuid.uuid4().hex[:4].upper()}"
            )
            
            # Create entity
            position = Position(
                x=entity_data["position"]["x"],
                y=entity_data["position"]["y"],
                z=entity_data["position"]["z"]
            )
            
            velocity = Velocity(
                speed=entity_data["velocity"]["speed"],
                heading=entity_data["velocity"]["heading"],
                climb_rate=entity_data["velocity"].get("climb_rate", 0.0)
            )
            
            kinematics = Kinematics(position=position, velocity=velocity)
            
            entity_type = EntityType(
                category=entity_data["type"]["category"],
                subcategory=entity_data["type"]["subcategory"],
                specification=entity_data["type"]["specification"]
            )
            
            disposition = Disposition(
                affiliation=entity_data["disposition"]["affiliation"],
                confidence=entity_data["disposition"].get("confidence", 1.0)
            )
            
            entity = TEDFEntity(
                entity_id=entity_data["entity_id"],
                unit_name=entity_data["unit_name"],
                callsign=entity_data["callsign"],
                entity_type=entity_type,
                disposition=disposition,
                kinematics=kinematics,
                model=entity_data.get("model", "")
            )
            
            # Create full message
            full_message = {
                "header": header.to_dict(),
                "entity": entity.to_dict()
            }
            
            return json.dumps(full_message, separators=(',', ':'))
            
        except Exception as e:
            self.logger.error(f"Error generating full message: {e}")
            return None
    
    def generate_compact_message(self, entity_data: Dict[str, Any]) -> str:
        """Generate a compact TEDF message"""
        try:
            compact_message = {
                "h": {
                    "id": "TEDF-COMPACT",
                    "t": int(time.time() * 1000),  # Milliseconds
                    "o": "PYTHON-SIM-01"
                },
                "e": {
                    "id": entity_data["entity_id"],
                    "n": entity_data["callsign"],
                    "d": entity_data["disposition_code"],
                    "p": [
                        entity_data["position"]["x"],
                        entity_data["position"]["y"],
                        entity_data["position"]["z"]
                    ],
                    "v": [
                        entity_data["velocity"]["speed"],
                        entity_data["velocity"]["heading"],
                        entity_data["velocity"].get("climb_rate", 0.0)
                    ],
                    "m": entity_data.get("model", "")
                }
            }
            
            return json.dumps(compact_message, separators=(',', ':'))
            
        except Exception as e:
            self.logger.error(f"Error generating compact message: {e}")
            return None
    
    def generate_batch_message(self, entities_data: List[Dict[str, Any]]) -> str:
        """Generate a batch TEDF message"""
        try:
            batch_entities = []
            
            for entity_data in entities_data:
                batch_entity = {
                    "entityId": entity_data["entity_id"],
                    "unitName": entity_data["unit_name"],
                    "disposition": entity_data["disposition_code"],
                    "position": {
                        "x": entity_data["position"]["x"],
                        "y": entity_data["position"]["y"],
                        "z": entity_data["position"]["z"]
                    },
                    "velocity": {
                        "speed": entity_data["velocity"]["speed"],
                        "heading": entity_data["velocity"]["heading"]
                    },
                    "type": {
                        "category": entity_data["type"]["category"],
                        "subcategory": entity_data["type"]["subcategory"],
                        "specification": entity_data["type"]["specification"]
                    },
                    "model": entity_data.get("model", "")
                }
                batch_entities.append(batch_entity)
            
            batch_message = {
                "batch": {
                    "batchId": f"BATCH-{datetime.now().strftime('%Y-%m-%d')}-{self.message_counter:04d}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "entityCount": len(batch_entities),
                    "entities": batch_entities
                }
            }
            
            return json.dumps(batch_message, separators=(',', ':'))
            
        except Exception as e:
            self.logger.error(f"Error generating batch message: {e}")
            return None
    
    def generate_despawn_message(self, entity_id: str, reason: str = "BOUNDARY_EXCEEDED") -> str:
        """Generate a despawn TEDF message"""
        try:
            header = TEDFHeader(
                message_id=f"DESPAWN-{datetime.now().strftime('%Y-%m-%d')}-{self.message_counter:04d}",
                message_type="ENTITY_DESPAWN"
            )
            
            despawn_message = {
                "header": header.to_dict(),
                "entity": {
                    "entityId": entity_id,
                    "reason": reason
                }
            }
            
            return json.dumps(despawn_message, separators=(',', ':'))
            
        except Exception as e:
            self.logger.error(f"Error generating despawn message: {e}")
            return None
    
    def queue_full_message(self, entity_data: Dict[str, Any]):
        """Queue a full message for broadcasting"""
        if not self.is_broadcasting:  # Add safety check
            return
        message = self.generate_full_message(entity_data)
        if message:
            self.pending_full_messages.append(message)
    
    def queue_compact_message(self, entity_data: Dict[str, Any]):
        """Queue a compact message for broadcasting"""
        if not self.is_broadcasting:  # Add safety check
            return
        message = self.generate_compact_message(entity_data)
        if message:
            self.pending_compact_messages.append(message)
    
    def queue_batch_message(self, entities_data: List[Dict[str, Any]]):
        """Queue a batch message for broadcasting"""
        if not self.is_broadcasting:  # Add safety check
            return
        message = self.generate_batch_message(entities_data)
        if message:
            self.pending_batch_messages.append(message)
    
    def queue_despawn_message(self, entity_id: str, reason: str = "BOUNDARY_EXCEEDED"):
        """Queue a despawn message for broadcasting"""
        if not self.is_broadcasting:  # Add safety check
            return
        message = self.generate_despawn_message(entity_id, reason)
        if message:
            self.pending_despawn_messages.append(message)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get broadcasting statistics"""
        stats = self.stats.copy()
        
        if stats["start_time"]:
            uptime = time.time() - stats["start_time"]
            stats["uptime_seconds"] = uptime
            stats["messages_per_second"] = stats["messages_sent"] / max(uptime, 1)
        else:
            stats["uptime_seconds"] = 0
            stats["messages_per_second"] = 0
        
        stats["is_broadcasting"] = self.is_broadcasting
        stats["pending_messages"] = (
            len(self.pending_full_messages) +
            len(self.pending_compact_messages) +
            len(self.pending_batch_messages) +
            len(self.pending_despawn_messages)
        )
        
        return stats
    
    def reset_statistics(self):
        """Reset broadcasting statistics"""
        self.stats = {
            "messages_sent": 0,
            "full_messages_sent": 0,
            "compact_messages_sent": 0,
            "batch_messages_sent": 0,
            "despawn_messages_sent": 0,
            "errors": 0,
            "start_time": time.time() if self.is_broadcasting else None,
            "last_message_time": None
        }
        self.message_counter = 0
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.stop_broadcasting()
        except Exception as e:
            # Avoid raising exceptions in __del__
            if hasattr(self, 'logger'):
                self.logger.error(f"Error in __del__: {e}")
    
    def cleanup(self):
        """Explicit cleanup method for controlled shutdown"""
        self.stop_broadcasting()
        
        # Clean up socket if it exists
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Don't double-terminate context - stop_broadcasting() already handles it
        # Only create fresh context if it doesn't exist or is closed
        if not hasattr(self, 'context') or self.context.closed:
            self.context = zmq.Context()
        
        # Clear message queues
        self.pending_full_messages.clear()
        self.pending_compact_messages.clear()
        self.pending_batch_messages.clear()
        self.pending_despawn_messages.clear()


# Helper functions for easy message generation
def create_entity_data(entity_id: str, callsign: str, position: tuple, velocity: tuple,
                      entity_type: tuple, disposition: str, model: str = None) -> Dict[str, Any]:
    """Helper function to create entity data dictionary"""
    return {
        "entity_id": entity_id,
        "unit_name": callsign.split('-')[0] if '-' in callsign else callsign,
        "callsign": callsign,
        "position": {
            "x": position[0],
            "y": position[1],
            "z": position[2]
        },
        "velocity": {
            "speed": velocity[0],
            "heading": velocity[1],
            "climb_rate": velocity[2] if len(velocity) > 2 else 0.0
        },
        "type": {
            "category": entity_type[0],
            "subcategory": entity_type[1],
            "specification": entity_type[2]
        },
        "model": model if model else entity_type[2],
        "disposition": {
            "affiliation": disposition,
            "confidence": 1.0
        },
        "disposition_code": DispositionCode[disposition].value
    }


if __name__ == "__main__":
    # Test the broadcaster
    broadcaster = TEDFBroadcaster(port=5555, update_rate=2.0)
    
    try:
        if broadcaster.start_broadcasting():
            print("Broadcasting started. Sending test messages...")
            
            # Test entity data
            test_entity = create_entity_data(
                entity_id="TEST-001",
                callsign="ALPHA-1",
                position=(1000.0, 100.0, -2000.0),
                velocity=(25.0, 90.0, 0.0),
                entity_type=("GROUND", "VEHICLE", "TRACKED_MBT"),
                disposition="FRIENDLY",
                model="M1A2_ABRAMS"
            )
            
            # Send test messages
            broadcaster.queue_full_message(test_entity)
            
            try:
                time.sleep(5)  # Let it broadcast for 5 seconds
                
                # Print statistics
                stats = broadcaster.get_statistics()
                print(f"Statistics: {json.dumps(stats, indent=2)}")
                
            except KeyboardInterrupt:
                print("\nReceived interrupt signal")
            
        else:
            print("Failed to start broadcasting")
            
    finally:
        # Ensure proper cleanup
        try:
            broadcaster.cleanup()
            print("Broadcaster cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")