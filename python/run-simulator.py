#!/usr/bin/env python3
"""
Simple launcher script for the Battlespace Simulator
Provides command-line options and dependency checking
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Try to import version manager
try:
    from version_manager import version_manager
    HAS_VERSION_MANAGER = True
except ImportError:
    HAS_VERSION_MANAGER = False


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = {
        'zmq': 'pyzmq',
        'tkinter': 'tkinter (should be included with Python)'
    }
    
    missing_packages = []
    
    for module, package in required_packages.items():
        try:
            if module == 'zmq':
                import zmq
            elif module == 'tkinter':
                import tkinter
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required dependencies:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nTo install missing dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def install_dependencies():
    """Install dependencies from requirements.txt"""
    try:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False


def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(
        description="Battlespace Simulator Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_simulator.py                    # Run with GUI
  python run_simulator.py --check-deps      # Check dependencies only
  python run_simulator.py --install-deps    # Install dependencies
  python run_simulator.py --headless        # Run without GUI (future feature)

For more information, see the documentation in BattlespaceVisualizationSystemRequirements_v0w4.md
        """
    )
    
    parser.add_argument(
        "--check-deps", 
        action="store_true",
        help="Check dependencies and exit"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true", 
        help="Install dependencies from requirements.txt"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without GUI (command-line only) - Not yet implemented"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    if HAS_VERSION_MANAGER:
        print(f"Battlespace Simulator Launcher - {version_manager.short_version_string}")
    else:
        print("Battlespace Simulator Launcher v1.0")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies if requested
    if args.install_deps:
        if install_dependencies():
            print("Dependencies installation complete!")
        else:
            print("Failed to install dependencies")
            return 1
    
    # Check dependencies
    if not check_dependencies():
        if args.check_deps:
            return 1
        
        print("\nWould you like to install missing dependencies? (y/n): ", end="")
        response = input().lower().strip()
        
        if response in ['y', 'yes']:
            if not install_dependencies():
                return 1
        else:
            print("Cannot continue without required dependencies")
            return 1
    
    # Just check dependencies and exit
    if args.check_deps:
        print("All dependencies are satisfied!")
        return 0
    
    # Check if main simulator file exists
    simulator_file = Path(__file__).parent / "battlespace-simulator.py"
    if not simulator_file.exists():
        print(f"Error: Main simulator file not found: {simulator_file}")
        return 1
    
    print("Starting Battlespace Simulator...")
    print(f"Log level: {args.log_level}")
    
    if args.headless:
        print("Error: Headless mode not yet implemented")
        return 1
    
    # Set up environment
    if args.log_level:
        os.environ['BATTLESPACE_LOG_LEVEL'] = args.log_level
    
    if args.config:
        os.environ['BATTLESPACE_CONFIG'] = args.config
    
    # Import and run the main simulator
    try:
        # Add current directory to Python path
        current_dir = str(Path(__file__).parent)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Import the main simulator using importlib for hyphenated filename
        import importlib.util
        spec = importlib.util.spec_from_file_location("battlespace_simulator", "battlespace-simulator.py")
        battlespace_simulator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(battlespace_simulator_module)
        BattlespaceSimulator = battlespace_simulator_module.BattlespaceSimulator
        
        # Create and run simulator
        simulator = BattlespaceSimulator()
        return 0 if simulator.run() else 1
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        return 0
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all simulator files are present in the current directory")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())