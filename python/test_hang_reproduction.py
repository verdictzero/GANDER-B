#!/usr/bin/env python3
"""
Test script to reproduce the hanging issue in battlespace simulator
"""

import sys
import time
import threading
import importlib.util

# Import modules
spec = importlib.util.spec_from_file_location('tedf_broadcaster', 'tedf-broadcaster.py')
tedf_broadcaster_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tedf_broadcaster_module)
TEDFBroadcaster = tedf_broadcaster_module.TEDFBroadcaster
create_entity_data = tedf_broadcaster_module.create_entity_data

spec = importlib.util.spec_from_file_location('entity_simulator', 'entity-simulator.py')
entity_simulator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entity_simulator_module)
EntitySimulator = entity_simulator_module.EntitySimulator
TerrainBounds = entity_simulator_module.TerrainBounds

def simulate_main_update_loop(tedf_broadcaster, entity_simulator, stop_event):
    """Simulate the main simulator's update loop that queues messages"""
    print("Update thread started")
    last_update = 0
    
    while not stop_event.wait(0.1):
        try:
            current_time = time.time()
            
            # Simulate queuing messages like the main simulator does
            if current_time - last_update >= 1.0:  # Every second
                # Create a test entity to queue
                test_entity = create_entity_data(
                    entity_id="TEST-001",
                    callsign="ALPHA-1", 
                    position=(1000.0, 100.0, -2000.0),
                    velocity=(25.0, 90.0, 0.0),
                    entity_type=("GROUND", "VEHICLE", "TRACKED_MBT"),
                    disposition="FRIENDLY"
                )
                
                # This is where the race condition can occur
                tedf_broadcaster.queue_compact_message(test_entity)
                last_update = current_time
                
        except Exception as e:
            print(f"Error in update thread: {e}")
            break
    
    print("Update thread finished")

def test_race_condition_hanging():
    """Test the specific race condition that causes hanging"""
    print("Testing race condition that causes hanging...")
    
    # Setup like main simulator
    terrain_bounds = TerrainBounds()
    entity_simulator = EntitySimulator(terrain_bounds)
    tedf_broadcaster = TEDFBroadcaster(port=5558, update_rate=2.0)
    
    # Load entity definitions
    entity_definitions = {
        'test_entity': {
            'id': 'test_entity',
            'name': 'Test Entity',
            'category': 'GROUND',
            'subcategory': 'VEHICLE',
            'specification': 'TEST_VEHICLE',
            'kinematics': {'maxSpeed': 20.0, 'cruiseSpeed': 10.0},
            'simulation_parameters': {'spawn_probability': 1.0},
            'disposition_types': ['FRIENDLY']
        }
    }
    entity_simulator.load_entity_definitions(entity_definitions)
    
    try:
        for cycle in range(3):
            print(f"\n--- Cycle {cycle + 1}/3 ---")
            
            # Start systems like main simulator
            print("Starting broadcaster...")
            if not tedf_broadcaster.start_broadcasting():
                print("Failed to start broadcaster")
                return False
                
            print("Starting entity simulator...")
            if not entity_simulator.start_simulation():
                print("Failed to start entity simulator")
                return False
            
            # Start update thread that actively uses broadcaster
            stop_event = threading.Event()
            update_thread = threading.Thread(
                target=simulate_main_update_loop,
                args=(tedf_broadcaster, entity_simulator, stop_event),
                daemon=True
            )
            update_thread.start()
            
            # Let everything run for a bit
            time.sleep(1.0)
            
            # Now stop everything like main simulator does - this is where hanging occurs
            print("Stopping simulation (this might hang)...")
            
            # Set stop flag
            stop_event.set()
            
            # Stop entity simulator
            print("  Stopping entity simulator...")
            entity_simulator.stop_simulation()
            
            # Stop broadcaster with cleanup (this can hang due to race condition)
            print("  Calling broadcaster cleanup...")
            start_time = time.time()
            tedf_broadcaster.cleanup()  # This is the problematic call
            cleanup_time = time.time() - start_time
            print(f"  Cleanup took {cleanup_time:.2f} seconds")
            
            # Wait for update thread
            print("  Waiting for update thread...")
            update_thread.join(timeout=5.0)
            if update_thread.is_alive():
                print("  WARNING: Update thread did not terminate!")
            
            print(f"Cycle {cycle + 1} completed")
            
            # Small delay between cycles
            time.sleep(0.5)
        
        print("\n✓ All cycles completed without hanging")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            entity_simulator.stop_simulation()
            tedf_broadcaster.cleanup()
        except:
            pass

if __name__ == "__main__":
    print("Reproducing battlespace simulator hanging issue...")
    success = test_race_condition_hanging()
    if success:
        print("\nTest completed successfully")
    else:
        print("\nTest failed or encountered issues")
    sys.exit(0 if success else 1)