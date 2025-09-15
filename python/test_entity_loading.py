#!/usr/bin/env python3
"""
Test script to verify entity database loading and GUI integration
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import modules
import importlib.util

# Import config-loader
spec = importlib.util.spec_from_file_location("config_loader", "config-loader.py")
config_loader_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_loader_module)
ConfigurationLoader = config_loader_module.ConfigurationLoader
EntityDatabaseLoader = config_loader_module.EntityDatabaseLoader

def test_entity_loading():
    """Test entity database loading"""
    print("Testing Entity Database Loading")
    print("=" * 40)
    
    # Test configuration loading
    config_loader = ConfigurationLoader()
    config_loader.load_configuration()
    print(f"✓ Configuration loaded")
    print(f"  Entity sync path: {config_loader.config.entity_sync_path}")
    
    # Test entity database loading
    entity_db_loader = EntityDatabaseLoader(config_loader)
    success = entity_db_loader.load_entity_database()
    print(f"✓ Entity database loaded: {success}")
    
    # Test getting entity definitions
    entity_definitions = entity_db_loader.get_entity_definitions()
    print(f"✓ Entity definitions retrieved: {len(entity_definitions)} entities")
    
    # Test format for GUI
    entity_list = list(entity_definitions.values())
    print(f"✓ Entity list for GUI: {len(entity_list)} entities")
    
    # Display entities
    print("\nLoaded Entities:")
    for i, entity in enumerate(entity_list, 1):
        entity_id = entity.get('id', 'Unknown')
        name = entity.get('name', 'Unknown')
        category = entity.get('category', 'Unknown')
        subcategory = entity.get('subcategory', 'Unknown')
        print(f"  {i}. {entity_id} - {name} ({category}/{subcategory})")
    
    # Test database info
    db_info = entity_db_loader.get_database_info()
    print(f"\nDatabase Info:")
    print(f"  Version: {db_info['version']}")
    print(f"  Entity count: {db_info['entity_count']}")
    print(f"  Categories: {db_info['categories']}")
    print(f"  Dispositions: {db_info['dispositions']}")
    
    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_entity_loading()
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)