#!/usr/bin/env python3
"""
Version Manager for Clusterfuck Python Components
Provides centralized version information from VERSION.json
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class VersionManager:
    """Manages version information for the Clusterfuck project"""
    
    _instance = None
    _version_info: Dict[str, Any] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VersionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_version_info()
            self._initialized = True
    
    def _load_version_info(self):
        """Load version information from VERSION.json"""
        try:
            # Try multiple paths to find VERSION.json
            possible_paths = [
                Path(__file__).parent.parent / "VERSION.json",  # From python/ directory
                Path(__file__).parent / "VERSION.json",         # Same directory
                Path.cwd() / "VERSION.json",                    # Current working directory
                Path.cwd().parent / "VERSION.json"              # Parent directory
            ]
            
            version_file = None
            for path in possible_paths:
                if path.exists():
                    version_file = path
                    break
            
            if version_file:
                with open(version_file, 'r') as f:
                    self._version_info = json.load(f)
                print(f"[VersionManager] Loaded version info from: {version_file}")
            else:
                print("[VersionManager] VERSION.json not found, using defaults")
                self._version_info = self._get_default_version_info()
                
        except Exception as e:
            print(f"[VersionManager] Error loading version info: {e}")
            self._version_info = self._get_default_version_info()
    
    def _get_default_version_info(self) -> Dict[str, Any]:
        """Return default version information"""
        return {
            "version": "1.2.1",
            "build_date": "2025.01.08",
            "build_name": "Unknown Build",
            "components": {
                "python": {"version": "1.2.1"}
            }
        }
    
    @property
    def version(self) -> str:
        """Get the current version"""
        return self._version_info.get("version", "1.2.1")
    
    @property
    def build_date(self) -> str:
        """Get the build date"""
        return self._version_info.get("build_date", "2025.01.08")
    
    @property
    def build_name(self) -> str:
        """Get the build name"""
        return self._version_info.get("build_name", "Unknown Build")
    
    @property
    def full_version_string(self) -> str:
        """Get the full version string for display"""
        return f"v{self.version} - {self.build_name} (Built: {self.build_date})"
    
    @property
    def short_version_string(self) -> str:
        """Get the short version string"""
        return f"v{self.version}"
    
    def get_component_version(self, component: str) -> str:
        """Get version for a specific component"""
        components = self._version_info.get("components", {})
        if component in components:
            return components[component].get("version", self.version)
        return self.version
    
    def get_changelog(self, version: Optional[str] = None) -> List[str]:
        """Get changelog for a specific version (current if not specified)"""
        version = version or self.version
        changelog = self._version_info.get("changelog", {})
        
        if version in changelog:
            return changelog[version].get("changes", [])
        return []
    
    def get_dependencies(self, component: str = "python") -> Dict[str, str]:
        """Get dependencies for a component"""
        deps = self._version_info.get("dependencies", {})
        if component == "python":
            return deps.get("python_packages", {})
        elif component == "unity":
            return deps.get("unity_packages", {})
        return {}
    
    def check_python_version(self) -> bool:
        """Check if current Python version meets requirements"""
        import sys
        components = self._version_info.get("components", {})
        python_comp = components.get("python", {})
        min_version = python_comp.get("min_python_version", "3.8")
        
        # Convert version strings to tuples for comparison
        min_version_tuple = tuple(map(int, min_version.split('.')))
        current_version_tuple = sys.version_info[:2]
        
        return current_version_tuple >= min_version_tuple
    
    def reload(self):
        """Force reload of version information"""
        self._initialized = False
        self._load_version_info()
        self._initialized = True
    
    def print_version_info(self):
        """Print formatted version information"""
        print("\n" + "="*60)
        print(f"Clusterfuck Python Components - {self.full_version_string}")
        print("="*60)
        print(f"Version: {self.version}")
        print(f"Build Date: {self.build_date}")
        print(f"Build Name: {self.build_name}")
        
        if self.get_changelog():
            print("\nRecent Changes:")
            for change in self.get_changelog():
                print(f"  • {change}")
        
        deps = self.get_dependencies()
        if deps:
            print("\nDependencies:")
            for package, version in deps.items():
                print(f"  • {package}: {version}")
        
        print("="*60 + "\n")


# Singleton instance
version_manager = VersionManager()

# Convenience functions
def get_version() -> str:
    """Get the current version"""
    return version_manager.version

def get_full_version_string() -> str:
    """Get the full version string"""
    return version_manager.full_version_string

def print_version_banner():
    """Print a version banner for console applications"""
    width = 70
    print("\n" + "╔" + "═"*(width-2) + "╗")
    print("║" + f"Clusterfuck {version_manager.short_version_string}".center(width-2) + "║")
    print("║" + f"{version_manager.build_name}".center(width-2) + "║")
    print("║" + f"Built: {version_manager.build_date}".center(width-2) + "║")
    print("╚" + "═"*(width-2) + "╝\n")


if __name__ == "__main__":
    # Test the version manager
    version_manager.print_version_info()
    print_version_banner()
    
    print(f"Python version supported: {version_manager.check_python_version()}")
    print(f"Component version (python): {version_manager.get_component_version('python')}")
    print(f"Component version (unity): {version_manager.get_component_version('unity')}")