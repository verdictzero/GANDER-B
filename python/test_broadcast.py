#!/usr/bin/env python3
"""
Test script for ZMQ broadcasting functionality
"""

import sys
import time
import importlib.util

# Import tedf-broadcaster using importlib
spec = importlib.util.spec_from_file_location("tedf_broadcaster", "tedf-broadcaster.py")
tedf_broadcaster_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tedf_broadcaster_module)
TEDFBroadcaster = tedf_broadcaster_module.TEDFBroadcaster
create_entity_data = tedf_broadcaster_module.create_entity_data

def test_broadcasting():
    """Test the broadcasting functionality"""
    print("Testing ZMQ Broadcasting...")
    
    # Create broadcaster
    broadcaster = TEDFBroadcaster(port=5555, update_rate=2.0)
    
    try:
        # Test starting broadcasting
        print("Starting broadcaster...")
        if broadcaster.start_broadcasting():
            print("✓ Broadcasting started successfully")
            
            # Create test entity
            test_entity = create_entity_data(
                entity_id="TEST-001",
                callsign="ALPHA-1",
                position=(1000.0, 100.0, -2000.0),
                velocity=(25.0, 90.0, 0.0),
                entity_type=("GROUND", "VEHICLE", "TRACKED_MBT"),
                disposition="FRIENDLY",
                model="M1A2_ABRAMS"
            )
            
            # Queue test message
            broadcaster.queue_full_message(test_entity)
            print("✓ Test message queued")
            
            # Let it broadcast briefly
            time.sleep(2)
            
            # Check stats
            stats = broadcaster.get_statistics()
            print(f"✓ Messages sent: {stats['messages_sent']}")
            
            # Test stopping
            broadcaster.stop_broadcasting()
            print("✓ Broadcasting stopped successfully")
            
            # Test restart
            print("Testing restart...")
            if broadcaster.start_broadcasting():
                print("✓ Broadcasting restarted successfully")
                broadcaster.stop_broadcasting()
                print("✓ Broadcasting stopped again")
            else:
                print("✗ Failed to restart broadcasting")
                return False
                
        else:
            print("✗ Failed to start broadcasting")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False
    finally:
        try:
            broadcaster.cleanup()
        except:
            pass
    
    print("✓ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_broadcasting()
    sys.exit(0 if success else 1)