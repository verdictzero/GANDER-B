#!/usr/bin/env python3
"""
Test script to verify GUI integration with entity database
"""

def mock_update_imported_entities_list(entity_types):
    """Mock the GUI method to verify data format"""
    print("Mock GUI - Update Imported Entities List")
    print("=" * 40)
    
    print(f"Received {len(entity_types)} entities:")
    
    for entity in entity_types:
        # Format: "ID - Name (Category/Subcategory)"
        display_text = f"{entity.get('id', 'Unknown')} - {entity.get('name', 'Unknown')} ({entity.get('category', 'Unknown')}/{entity.get('subcategory', 'Unknown')})"
        print(f"  {display_text}")
    
    print(f"\nEntity count label would show: '{len(entity_types)} entity types loaded'")
    return True

def test_gui_integration():
    """Test GUI integration"""
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
    
    # Load entities
    config_loader = ConfigurationLoader()
    config_loader.load_configuration()
    
    entity_db_loader = EntityDatabaseLoader(config_loader)
    entity_db_loader.load_entity_database()
    
    # Get entities in GUI format
    entity_definitions = entity_db_loader.get_entity_definitions()
    entity_list = list(entity_definitions.values())
    
    # Test GUI integration
    mock_update_imported_entities_list(entity_list)
    
    print("\n✓ GUI integration test passed!")

if __name__ == "__main__":
    test_gui_integration()