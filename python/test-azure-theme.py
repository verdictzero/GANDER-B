#!/usr/bin/env python3
"""
Test script to demonstrate Azure theme in both applications
"""

import subprocess
import time
import sys

def test_editor():
    print("Testing Battlespace Editor with Azure theme...")
    print("=" * 50)
    print("Starting editor - it should open with Azure dark theme")
    print("You can switch between light/dark themes from View menu")
    print("Close the window when done to continue...\n")
    
    subprocess.run([sys.executable, "battlespace-editor.py"])
    print("\nEditor test completed.\n")

def test_simulator():
    print("Testing Battlespace Simulator with Azure theme...")
    print("=" * 50)
    print("Starting simulator - it should open with Azure dark theme")
    print("You can switch between light/dark themes from View menu")
    print("The three-pane layout should be styled with Azure theme")
    print("Close the window when done to continue...\n")
    
    subprocess.run([sys.executable, "run-simulator.py"])
    print("\nSimulator test completed.\n")

def main():
    print("Azure Theme Test for Battlespace Applications")
    print("=" * 50)
    print("\nThis script will test both applications with the Azure theme.")
    print("Each application will open in sequence.\n")
    
    response = input("Test Battlespace Editor first? (y/n): ")
    if response.lower() == 'y':
        test_editor()
    
    response = input("Test Battlespace Simulator? (y/n): ")
    if response.lower() == 'y':
        test_simulator()
    
    print("\nTheme test completed!")
    print("\nNote: Theme preferences are saved and will persist between runs.")
    print("Preference files created:")
    print("  - .theme_preference (for simulator)")
    print("  - .theme_preference_editor (for editor)")

if __name__ == "__main__":
    main()