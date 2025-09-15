"""
GUI Components for Battlespace Simulator
Tkinter-based interface with tabs for entity management and simulation control
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from _tkinter import TclError
import json
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging


class EntityDetailFrame(ttk.Frame):
    """Frame showing detailed entity information"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_entity = None
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        self.title_label = ttk.Label(self, text="Entity Details", font=("Arial", 12, "bold"))
        self.title_label.pack(pady=5)
        
        # Instruction label for when no entity is selected
        self.instruction_label = ttk.Label(self, text="← Select an entity from the list to view detailed information", 
                                         font=("Arial", 10), foreground="gray")
        self.instruction_label.pack(pady=20)
        
        # Scrollable frame for entity details
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Entity info labels
        self.info_labels = {}
        self.create_info_display()
    
    def create_info_display(self):
        """Create labels for entity information display"""
        fields = [
            ("Entity ID:", "entity_id"),
            ("Callsign:", "callsign"),
            ("Unit Name:", "unit_name"),
            ("", "separator1"),
            ("Category:", "category"),
            ("Subcategory:", "subcategory"),
            ("Specification:", "specification"),
            ("Disposition:", "disposition"),
            ("", "separator2"),
            ("Position X:", "pos_x"),
            ("Position Y:", "pos_y"),
            ("Position Z:", "pos_z"),
            ("", "separator3"),
            ("Speed:", "speed"),
            ("Heading:", "heading"),
            ("Climb Rate:", "climb_rate"),
            ("", "separator4"),
            ("Last Update:", "last_update"),
            ("Active Time:", "active_time")
        ]
        
        for i, (label_text, field_key) in enumerate(fields):
            if label_text == "":  # Separator
                separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
                separator.grid(row=i, column=0, columnspan=2, sticky="ew", padx=5, pady=8)
                continue
                
            label = ttk.Label(self.scrollable_frame, text=label_text, font=("Arial", 9, "bold"))
            label.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            value_label = ttk.Label(self.scrollable_frame, text="--", font=("Arial", 9))
            value_label.grid(row=i, column=1, sticky="w", padx=10, pady=2)
            
            self.info_labels[field_key] = value_label
    
    def update_entity_info(self, entity_data: Dict[str, Any]):
        """Update displayed entity information"""
        self.current_entity = entity_data
        
        # Hide instruction label and show entity details
        self.instruction_label.pack_forget()
        
        # Update title with entity callsign
        entity_callsign = entity_data.get("callsign", "Unknown")
        self.title_label.config(text=f"Entity Details - {entity_callsign}")
        
        # Update basic info
        self.info_labels["entity_id"].config(text=entity_data.get("entity_id", "--"))
        self.info_labels["callsign"].config(text=entity_data.get("callsign", "--"))
        self.info_labels["unit_name"].config(text=entity_data.get("unit_name", "--"))
        
        # Type information
        entity_type = entity_data.get("type", {})
        self.info_labels["category"].config(text=entity_type.get("category", "--"))
        self.info_labels["subcategory"].config(text=entity_type.get("subcategory", "--"))
        self.info_labels["specification"].config(text=entity_type.get("specification", "--"))
        
        # Disposition
        disposition = entity_data.get("disposition", {})
        disp_text = disposition.get("affiliation", "--")
        self.info_labels["disposition"].config(text=disp_text)
        
        # Position
        position = entity_data.get("position", {})
        self.info_labels["pos_x"].config(text=f"{position.get('x', 0):.2f} m")
        self.info_labels["pos_y"].config(text=f"{position.get('y', 0):.2f} m")
        self.info_labels["pos_z"].config(text=f"{position.get('z', 0):.2f} m")
        
        # Velocity
        velocity = entity_data.get("velocity", {})
        self.info_labels["speed"].config(text=f"{velocity.get('speed', 0):.2f} m/s")
        self.info_labels["heading"].config(text=f"{velocity.get('heading', 0):.1f}°")
        self.info_labels["climb_rate"].config(text=f"{velocity.get('climb_rate', 0):.2f} m/s")
        
        # Timing info
        self.info_labels["last_update"].config(text=datetime.now().strftime("%H:%M:%S"))
        
        # Calculate active time (placeholder)
        self.info_labels["active_time"].config(text="--")
    
    def clear_info(self):
        """Clear all displayed information"""
        # Reset title
        self.title_label.config(text="Entity Details")
        
        # Show instruction label
        self.instruction_label.pack(pady=20, after=self.title_label)
        
        # Clear all info labels
        for label in self.info_labels.values():
            label.config(text="--")
        self.current_entity = None


class EntitySummaryFrame(ttk.Frame):
    """Frame showing summary list of entities"""
    
    def __init__(self, parent, on_entity_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_entity_select = on_entity_select
        self.entities_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title_label = ttk.Label(self, text="Entity List", font=("Arial", 12, "bold"))
        title_label.pack(pady=5)
        
        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", self.apply_filter)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=20)
        filter_entry.pack(side="left", padx=5)
        
        # Disposition filter
        ttk.Label(filter_frame, text="Disposition:").pack(side="left", padx=(10, 0))
        self.disposition_var = tk.StringVar(value="All")
        disposition_combo = ttk.Combobox(filter_frame, textvariable=self.disposition_var, 
                                       values=["All", "FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"],
                                       width=10, state="readonly")
        disposition_combo.pack(side="left", padx=5)
        disposition_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        
        # Entity list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview for entity list
        columns = ("ID", "Callsign", "Type", "Model", "Disposition", "Position", "Speed")
        self.entity_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        # Configure columns
        self.entity_tree.heading("ID", text="ID")
        self.entity_tree.heading("Callsign", text="Callsign")
        self.entity_tree.heading("Type", text="Type")
        self.entity_tree.heading("Model", text="Model")
        self.entity_tree.heading("Disposition", text="Disposition")
        self.entity_tree.heading("Position", text="Position")
        self.entity_tree.heading("Speed", text="Speed")
        
        self.entity_tree.column("ID", width=80)
        self.entity_tree.column("Callsign", width=80)
        self.entity_tree.column("Type", width=100)
        self.entity_tree.column("Model", width=120)
        self.entity_tree.column("Disposition", width=80)
        self.entity_tree.column("Position", width=120)
        self.entity_tree.column("Speed", width=60)
        
        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.entity_tree.yview)
        self.entity_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.entity_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Bind selection events
        self.entity_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.entity_tree.bind("<Double-1>", self.on_double_click)
        
        # Configure selection colors (adjusted for Azure theme)
        self.entity_tree.tag_configure('selected', background='#007acc')
        self.entity_tree.tag_configure('friendly', foreground='#00cc00')
        self.entity_tree.tag_configure('hostile', foreground='#ff4444')
        self.entity_tree.tag_configure('neutral', foreground='#ffaa00')
        self.entity_tree.tag_configure('unknown', foreground='#999999')
        
        # Status label
        self.status_label = ttk.Label(self, text="No entities")
        self.status_label.pack(pady=2)
    
    def on_tree_select(self, event):
        """Handle entity selection in tree"""
        selection = self.entity_tree.selection()
        if selection and self.on_entity_select:
            item = selection[0]
            entity_id = self.entity_tree.item(item, "values")[0]
            if entity_id in self.entities_data:
                # Call the selection callback
                self.on_entity_select(self.entities_data[entity_id])
    
    def on_double_click(self, event):
        """Handle double-click on entity - could be used for additional actions"""
        selection = self.entity_tree.selection()
        if selection:
            item = selection[0]
            entity_id = self.entity_tree.item(item, "values")[0]
            if entity_id in self.entities_data:
                # For now, just ensure the entity details are showing
                # In the future, this could open a more detailed popup or perform other actions
                pass
    
    def update_entities(self, entities: Dict[str, Dict[str, Any]]):
        """Update entity list"""
        self.entities_data = entities
        self.apply_filter()
    
    def apply_filter(self, *args):
        """Apply filters to entity list"""
        # Clear existing items
        for item in self.entity_tree.get_children():
            self.entity_tree.delete(item)
        
        filter_text = self.filter_var.get().lower()
        disposition_filter = self.disposition_var.get()
        
        filtered_count = 0
        
        for entity_id, entity_data in self.entities_data.items():
            # Apply text filter
            if filter_text:
                searchable_text = f"{entity_id} {entity_data.get('callsign', '')} {entity_data.get('unit_name', '')}".lower()
                if filter_text not in searchable_text:
                    continue
            
            # Apply disposition filter
            entity_disposition = entity_data.get("disposition", {}).get("affiliation", "UNKNOWN")
            if disposition_filter != "All" and entity_disposition != disposition_filter:
                continue
            
            # Add to tree
            entity_type = entity_data.get("type", {})
            type_text = f"{entity_type.get('category', '')}/{entity_type.get('subcategory', '')}"
            velocity = entity_data.get("velocity", {})
            speed = velocity.get("speed", 0)
            
            # Format position
            position = entity_data.get("position", {})
            pos_text = f"({position.get('x', 0):.0f}, {position.get('y', 0):.0f}, {position.get('z', 0):.0f})"
            
            # Determine color tag based on disposition
            color_tag = entity_disposition.lower() if entity_disposition.lower() in ['friendly', 'hostile', 'neutral', 'unknown'] else 'unknown'
            
            # Get model from entity data
            model = entity_data.get("model", entity_data.get("type", {}).get("specification", ""))
            
            item = self.entity_tree.insert("", "end", values=(
                entity_id,
                entity_data.get("callsign", ""),
                type_text,
                model,
                entity_disposition,
                pos_text,
                f"{speed:.1f}"
            ), tags=(color_tag,))
            
            filtered_count += 1
        
        # Update status
        total_count = len(self.entities_data)
        if filtered_count == total_count:
            self.status_label.config(text=f"{total_count} entities")
        else:
            self.status_label.config(text=f"{filtered_count}/{total_count} entities")


class SimulationControlFrame(ttk.Frame):
    """Frame for simulation control and setup"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.callbacks = {}
        self.setup_ui()
    
    def setup_ui(self):
        # Create main control buttons (always visible)
        self.create_main_controls()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Setup Tab
        self.setup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.setup_tab, text="Setup")
        self.create_setup_tab()
        
        # Manual Boundary Tab
        self.boundary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.boundary_tab, text="Manual Boundary")
        self.create_boundary_tab()
        
        # Control Tab
        self.control_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.control_tab, text="Control")
        self.create_control_tab()
        
        # Statistics Tab
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text="Statistics")
        self.create_stats_tab()
    
    def create_main_controls(self):
        """Create main control buttons that are always visible"""
        # Main control frame at the top
        main_control_frame = ttk.LabelFrame(self, text="Simulation Control", padding=10)
        main_control_frame.pack(fill="x", padx=5, pady=5)
        
        # Create custom styles for the buttons
        self.setup_button_styles()
        
        # Button container
        button_container = ttk.Frame(main_control_frame)
        button_container.pack(pady=5)
        
        # Create Start button with custom style
        self.start_button = ttk.Button(button_container, 
                                     text="Start Simulation",
                                     command=self.start_simulation,
                                     style="Start.TButton")
        self.start_button.pack(side="left", padx=10)
        
        # Create Stop button with custom style
        self.stop_button = ttk.Button(button_container,
                                    text="Stop Simulation", 
                                    command=self.stop_simulation,
                                    style="Stop.TButton",
                                    state="disabled")
        self.stop_button.pack(side="left", padx=10)
        
        # Clear entities button with neutral style
        clear_button = ttk.Button(button_container,
                                text="Clear All Entities",
                                command=self.clear_entities,
                                style="Clear.TButton")
        clear_button.pack(side="left", padx=10)
        
        # Status indicator
        self.status_frame = ttk.Frame(main_control_frame)
        self.status_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(self.status_frame, text="Status:", font=("Arial", 10, "bold")).pack(side="left")
        self.status_indicator = ttk.Label(self.status_frame,
                                        text="● STOPPED",
                                        font=("Arial", 10, "bold"),
                                        foreground="#B71C1C")  # Red for stopped
        self.status_indicator.pack(side="left", padx=(5, 0))
    
    def setup_button_styles(self):
        """Setup custom button styles that work with ttk themes"""
        try:
            style = ttk.Style()
            
            # Start button - muted green background
            style.configure("Start.TButton",
                          font=("Arial", 11, "bold"),
                          padding=(20, 8),
                          background="#90EE90",  # Light green background
                          foreground="#2E7D32",  # Dark green text
                          borderwidth=1,
                          relief="raised")
            style.map("Start.TButton",
                     background=[('disabled', '#E0E0E0'),    # Gray when disabled
                               ('active', '#A5D6A7'),       # Slightly darker green on hover
                               ('!active', '#90EE90')],     # Normal light green
                     foreground=[('disabled', '#A0A0A0'),    # Gray text when disabled
                               ('active', '#1B5E20'),       # Darker green text on hover
                               ('!active', '#2E7D32')])     # Normal dark green text
            
            # Stop button - muted red background
            style.configure("Stop.TButton",
                          font=("Arial", 11, "bold"),
                          padding=(20, 8),
                          background="#FFB3B3",  # Light red background
                          foreground="#B71C1C",  # Dark red text
                          borderwidth=1,
                          relief="raised")
            style.map("Stop.TButton",
                     background=[('disabled', '#E0E0E0'),    # Gray when disabled
                               ('active', '#FFCDD2'),       # Slightly darker red on hover
                               ('!active', '#FFB3B3')],     # Normal light red
                     foreground=[('disabled', '#A0A0A0'),    # Gray text when disabled
                               ('active', '#8D1C1C'),       # Darker red text on hover
                               ('!active', '#B71C1C')])     # Normal dark red text
            
            # Clear button - neutral gray
            style.configure("Clear.TButton",
                          font=("Arial", 10),
                          padding=(15, 6),
                          background="#E0E0E0",  # Light gray background
                          foreground="#424242",  # Dark gray text
                          borderwidth=1,
                          relief="raised")
            style.map("Clear.TButton",
                     background=[('disabled', '#F5F5F5'),    # Lighter gray when disabled
                               ('active', '#BDBDBD'),       # Darker gray on hover
                               ('!active', '#E0E0E0')],     # Normal light gray
                     foreground=[('disabled', '#A0A0A0'),    # Gray text when disabled
                               ('active', '#212121'),       # Darker text on hover
                               ('!active', '#424242')])     # Normal dark gray text
            
        except Exception as e:
            # Fallback if styling fails - just use default ttk buttons
            logging.warning(f"Could not setup custom button styles: {e}")
    
    def create_setup_tab(self):
        """Create setup configuration tab"""
        # Terrain Data Configuration
        terrain_frame = ttk.LabelFrame(self.setup_tab, text="Terrain Data Configuration", padding=10)
        terrain_frame.pack(fill="x", padx=5, pady=5)
        
        # Terrain path
        path_frame = ttk.Frame(terrain_frame)
        path_frame.pack(fill="x", pady=2)
        
        # Label and entry on one row
        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill="x", pady=2)
        
        ttk.Label(path_input_frame, text="Terrain Boundaries File:").pack(side="left")
        self.terrain_path_var = tk.StringVar()
        terrain_entry = ttk.Entry(path_input_frame, textvariable=self.terrain_path_var, width=40)
        terrain_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Buttons on a separate row for better responsiveness
        path_button_frame = ttk.Frame(path_frame)
        path_button_frame.pack(fill="x", pady=2)
        
        ttk.Button(path_button_frame, text="Browse", 
                  command=self.browse_terrain_path).pack(side="left", padx=2)
        ttk.Button(path_button_frame, text="Refresh", 
                  command=self.refresh_terrain_data).pack(side="left", padx=2)
        ttk.Button(path_button_frame, text="Load", 
                  command=self.load_terrain_data).pack(side="left", padx=2)
        
        # Terrain info display
        self.terrain_info_var = tk.StringVar(value="No terrain data loaded")
        terrain_info_label = ttk.Label(terrain_frame, textvariable=self.terrain_info_var)
        terrain_info_label.pack(pady=5)
        
        # Entity Database Configuration
        entity_frame = ttk.LabelFrame(self.setup_tab, text="Entity Database Configuration", padding=10)
        entity_frame.pack(fill="x", padx=5, pady=5)
        
        # Entity database path
        db_path_frame = ttk.Frame(entity_frame)
        db_path_frame.pack(fill="x", pady=2)
        
        # Label and entry on one row
        db_input_frame = ttk.Frame(db_path_frame)
        db_input_frame.pack(fill="x", pady=2)
        
        ttk.Label(db_input_frame, text="Entity Database Path:").pack(side="left")
        self.entity_db_path_var = tk.StringVar()
        db_entry = ttk.Entry(db_input_frame, textvariable=self.entity_db_path_var, width=40)
        db_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Buttons on a separate row for better responsiveness
        db_button_frame = ttk.Frame(db_path_frame)
        db_button_frame.pack(fill="x", pady=2)
        
        ttk.Button(db_button_frame, text="Browse", 
                  command=self.browse_entity_db_path).pack(side="left", padx=2)
        ttk.Button(db_button_frame, text="Refresh", 
                  command=self.refresh_entity_database).pack(side="left", padx=2)
        ttk.Button(db_button_frame, text="Reload", 
                  command=self.reload_entity_database).pack(side="left", padx=2)
        
        # Entity database info
        self.entity_db_info_var = tk.StringVar(value="No entity database loaded")
        db_info_label = ttk.Label(entity_frame, textvariable=self.entity_db_info_var)
        db_info_label.pack(pady=5)
        
        # Imported entities list
        entities_list_frame = ttk.LabelFrame(self.setup_tab, text="Imported Entity Types", padding=10)
        entities_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create scrollable listbox for entities
        list_container = ttk.Frame(entities_list_frame)
        list_container.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.imported_entities_listbox = tk.Listbox(list_container, 
                                                    yscrollcommand=scrollbar.set,
                                                    height=10)
        self.imported_entities_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.imported_entities_listbox.yview)
        
        # Entity count label
        self.entity_count_label = ttk.Label(entities_list_frame, text="0 entity types loaded")
        self.entity_count_label.pack(pady=5)
    
    def create_boundary_tab(self):
        """Create manual boundary configuration tab"""
        # Use imported terrain data checkbox
        self.use_imported_var = tk.BooleanVar(value=True)
        use_imported_check = ttk.Checkbutton(self.boundary_tab, 
                                           text="Use imported terrain data",
                                           variable=self.use_imported_var,
                                           command=self.toggle_manual_boundaries)
        use_imported_check.pack(pady=10)
        
        # Manual boundary frame
        self.manual_frame = ttk.LabelFrame(self.boundary_tab, text="Manual Boundaries", 
                                         padding=10)
        self.manual_frame.pack(fill="x", padx=5, pady=5)
        
        # Boundary input fields
        boundary_fields = [
            ("X Min:", "x_min"),
            ("X Max:", "x_max"),
            ("Z Min:", "z_min"),
            ("Z Max:", "z_max"),
            ("Y Min (Altitude):", "y_min"),
            ("Y Max (Altitude):", "y_max")
        ]
        
        self.boundary_vars = {}
        for i, (label_text, var_name) in enumerate(boundary_fields):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(self.manual_frame, text=label_text).grid(row=row, column=col, 
                                                              sticky="w", padx=5, pady=2)
            
            var = tk.DoubleVar()
            entry = ttk.Entry(self.manual_frame, textvariable=var, width=15)
            entry.grid(row=row, column=col+1, padx=5, pady=2)
            
            self.boundary_vars[var_name] = var
        
        # Apply button
        ttk.Button(self.manual_frame, text="Apply Boundaries", 
                  command=self.apply_manual_boundaries).grid(row=3, column=0, 
                                                           columnspan=4, pady=10)
        
        # Initialize state
        self.toggle_manual_boundaries()
    
    def create_control_tab(self):
        """Create simulation control tab"""
        
        # Manual spawn controls frame
        spawn_frame = ttk.LabelFrame(self.control_tab, text="Manual Entity Spawn", padding=10)
        spawn_frame.pack(fill="x", padx=5, pady=5)
        
        # Entity type selection
        type_frame = ttk.Frame(spawn_frame)
        type_frame.pack(fill="x", pady=5)
        
        ttk.Label(type_frame, text="Entity Type:").pack(side="left", padx=5)
        self.entity_type_var = tk.StringVar()
        self.entity_type_combo = ttk.Combobox(type_frame, textvariable=self.entity_type_var, 
                                            width=30, state="readonly")
        self.entity_type_combo.pack(side="left", padx=5)
        
        ttk.Label(type_frame, text="Disposition:").pack(side="left", padx=5)
        self.disposition_var = tk.StringVar(value="FRIENDLY")
        disposition_combo = ttk.Combobox(type_frame, textvariable=self.disposition_var,
                                       values=["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"],
                                       width=15, state="readonly")
        disposition_combo.pack(side="left", padx=5)
        
        # Spawn buttons
        spawn_button_frame = ttk.Frame(spawn_frame)
        spawn_button_frame.pack(pady=5)
        
        ttk.Button(spawn_button_frame, text="Spawn 1x", 
                  command=lambda: self.spawn_entities(1)).pack(side="left", padx=5)
        
        ttk.Button(spawn_button_frame, text="Spawn 10x", 
                  command=lambda: self.spawn_entities(10)).pack(side="left", padx=5)
        
        # Custom spawn count
        ttk.Label(spawn_button_frame, text="Count:").pack(side="left", padx=5)
        self.spawn_count_var = tk.IntVar(value=1)
        spawn_count_spin = ttk.Spinbox(spawn_button_frame, from_=1, to=100,
                                     textvariable=self.spawn_count_var, width=8)
        spawn_count_spin.pack(side="left", padx=2)
        
        ttk.Button(spawn_button_frame, text="Spawn Custom", 
                  command=self.spawn_custom).pack(side="left", padx=5)
        
        # Random spawn controls frame
        random_spawn_frame = ttk.LabelFrame(self.control_tab, text="Random Entity Spawn", padding=10)
        random_spawn_frame.pack(fill="x", padx=5, pady=5)
        
        # Random spawn buttons
        random_button_frame = ttk.Frame(random_spawn_frame)
        random_button_frame.pack(pady=5)
        
        ttk.Button(random_button_frame, text="Spawn 1x Random", 
                  command=lambda: self.spawn_random_entities(1)).pack(side="left", padx=5)
        
        ttk.Button(random_button_frame, text="Spawn 10x Random", 
                  command=lambda: self.spawn_random_entities(10)).pack(side="left", padx=5)
        
        # Random spawn info label
        info_label = ttk.Label(random_spawn_frame, 
                             text="Spawns random entity types based on configured probabilities",
                             font=("Arial", 8), foreground="gray")
        info_label.pack(pady=2)
        
        # Simulation parameters
        params_frame = ttk.LabelFrame(self.control_tab, text="Simulation Parameters", padding=10)
        params_frame.pack(fill="x", padx=5, pady=5)
        
        # Max entities
        ttk.Label(params_frame, text="Max Entities:").grid(row=0, column=0, sticky="w", padx=5)
        self.max_entities_var = tk.IntVar(value=20)
        max_entities_spin = ttk.Spinbox(params_frame, from_=1, to=1000, 
                                      textvariable=self.max_entities_var, width=10)
        max_entities_spin.grid(row=0, column=1, padx=5, pady=2)
        
        # Spawn rate
        ttk.Label(params_frame, text="Spawn Rate (/min):").grid(row=0, column=2, sticky="w", padx=5)
        self.spawn_rate_var = tk.DoubleVar(value=1.0)
        spawn_rate_spin = ttk.Spinbox(params_frame, from_=0.1, to=100.0, increment=0.5,
                                    textvariable=self.spawn_rate_var, width=10)
        spawn_rate_spin.grid(row=0, column=3, padx=5, pady=2)
        
        # Update rate
        ttk.Label(params_frame, text="Update Rate (Hz):").grid(row=1, column=0, sticky="w", padx=5)
        self.update_rate_var = tk.DoubleVar(value=30.0)
        update_rate_spin = ttk.Spinbox(params_frame, from_=1.0, to=60.0, increment=1.0,
                                     textvariable=self.update_rate_var, width=10)
        update_rate_spin.grid(row=1, column=1, padx=5, pady=2)
        
        # Speed multiplier
        ttk.Label(params_frame, text="Speed Multiplier:").grid(row=1, column=2, sticky="w", padx=5)
        self.speed_multiplier_var = tk.DoubleVar(value=0.1)
        speed_multiplier_spin = ttk.Spinbox(params_frame, from_=0.01, to=10.0, increment=0.1,
                                          textvariable=self.speed_multiplier_var, width=10,
                                          format="%.2f")
        speed_multiplier_spin.grid(row=1, column=3, padx=5, pady=2)
        
        # Bind speed multiplier change event
        self.speed_multiplier_var.trace_add("write", self.on_speed_multiplier_changed)
        
        # Network settings
        network_frame = ttk.LabelFrame(self.control_tab, text="Network Settings", padding=10)
        network_frame.pack(fill="x", padx=5, pady=5)
        
        # Primary network settings (Row 0)
        ttk.Label(network_frame, text="ZMQ Address:").grid(row=0, column=0, sticky="w", padx=5)
        self.zmq_address_var = tk.StringVar(value="tcp://localhost")
        address_entry = ttk.Entry(network_frame, textvariable=self.zmq_address_var, width=15)
        address_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(network_frame, text="ZMQ Port:").grid(row=0, column=2, sticky="w", padx=5)
        self.zmq_port_var = tk.IntVar(value=5555)
        port_spin = ttk.Spinbox(network_frame, from_=1024, to=65535, 
                              textvariable=self.zmq_port_var, width=10)
        port_spin.grid(row=0, column=3, padx=5, pady=2)
        
        # Protocol and interface settings (Row 1)
        ttk.Label(network_frame, text="Protocol:").grid(row=1, column=0, sticky="w", padx=5)
        self.zmq_protocol_var = tk.StringVar(value="tcp")
        protocol_combo = ttk.Combobox(network_frame, textvariable=self.zmq_protocol_var, 
                                    values=["tcp", "ipc", "inproc"], width=8, state="readonly")
        protocol_combo.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(network_frame, text="Bind Interface:").grid(row=1, column=2, sticky="w", padx=5)
        self.zmq_bind_interface_var = tk.StringVar(value="*")
        interface_entry = ttk.Entry(network_frame, textvariable=self.zmq_bind_interface_var, width=10)
        interface_entry.grid(row=1, column=3, padx=5, pady=2)
        
        # Broadcast settings (Row 2)
        ttk.Label(network_frame, text="Broadcast Enabled:").grid(row=2, column=0, sticky="w", padx=5)
        self.broadcast_enabled_var = tk.BooleanVar(value=True)
        broadcast_check = ttk.Checkbutton(network_frame, variable=self.broadcast_enabled_var)
        broadcast_check.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(network_frame, text="Broadcast Rate (Hz):").grid(row=2, column=2, sticky="w", padx=5)
        self.broadcast_rate_var = tk.DoubleVar(value=2.0)
        broadcast_spin = ttk.Spinbox(network_frame, from_=0.1, to=10.0, increment=0.1,
                                   textvariable=self.broadcast_rate_var, width=10)
        broadcast_spin.grid(row=2, column=3, padx=5, pady=2)
        
        # Advanced network settings in a collapsible frame
        self.advanced_network_frame = ttk.LabelFrame(self.control_tab, text="Advanced Network Settings", padding=10)
        self.advanced_network_frame.pack(fill="x", padx=5, pady=5)
        
        # Show/hide advanced settings button
        self.show_advanced_var = tk.BooleanVar(value=False)
        self.advanced_toggle_btn = ttk.Button(self.advanced_network_frame, text="Show Advanced Settings",
                                            command=self.toggle_advanced_network)
        self.advanced_toggle_btn.pack(pady=5)
        
        # Advanced settings container (initially hidden)
        self.advanced_settings_frame = ttk.Frame(self.advanced_network_frame)
        
        # Connection settings
        connection_frame = ttk.LabelFrame(self.advanced_settings_frame, text="Connection Settings", padding=5)
        connection_frame.pack(fill="x", pady=5)
        
        ttk.Label(connection_frame, text="Connection Timeout (ms):").grid(row=0, column=0, sticky="w", padx=5)
        self.connection_timeout_var = tk.IntVar(value=5000)
        timeout_spin = ttk.Spinbox(connection_frame, from_=1000, to=30000, increment=1000,
                                 textvariable=self.connection_timeout_var, width=10)
        timeout_spin.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(connection_frame, text="Retry Count:").grid(row=0, column=2, sticky="w", padx=5)
        self.retry_count_var = tk.IntVar(value=3)
        retry_spin = ttk.Spinbox(connection_frame, from_=0, to=10,
                               textvariable=self.retry_count_var, width=10)
        retry_spin.grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(connection_frame, text="Queue Size:").grid(row=1, column=0, sticky="w", padx=5)
        self.queue_size_var = tk.IntVar(value=1000)
        queue_spin = ttk.Spinbox(connection_frame, from_=100, to=10000, increment=100,
                               textvariable=self.queue_size_var, width=10)
        queue_spin.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(connection_frame, text="Heartbeat Interval (s):").grid(row=1, column=2, sticky="w", padx=5)
        self.heartbeat_interval_var = tk.DoubleVar(value=10.0)
        heartbeat_spin = ttk.Spinbox(connection_frame, from_=1.0, to=60.0, increment=1.0,
                                   textvariable=self.heartbeat_interval_var, width=10)
        heartbeat_spin.grid(row=1, column=3, padx=5, pady=2)
        
        # Security settings
        security_frame = ttk.LabelFrame(self.advanced_settings_frame, text="Security Settings", padding=5)
        security_frame.pack(fill="x", pady=5)
        
        ttk.Label(security_frame, text="Enable Authentication:").grid(row=0, column=0, sticky="w", padx=5)
        self.enable_auth_var = tk.BooleanVar(value=False)
        auth_check = ttk.Checkbutton(security_frame, variable=self.enable_auth_var,
                                   command=self.toggle_auth_controls)
        auth_check.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(security_frame, text="Auth Key:").grid(row=0, column=2, sticky="w", padx=5)
        self.auth_key_var = tk.StringVar(value="")
        self.auth_key_entry = ttk.Entry(security_frame, textvariable=self.auth_key_var, 
                                      width=20, show="*", state="disabled")
        self.auth_key_entry.grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(security_frame, text="Enable Encryption:").grid(row=1, column=0, sticky="w", padx=5)
        self.enable_encryption_var = tk.BooleanVar(value=False)
        encryption_check = ttk.Checkbutton(security_frame, variable=self.enable_encryption_var,
                                         command=self.toggle_encryption_controls)
        encryption_check.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(security_frame, text="Encryption Key:").grid(row=1, column=2, sticky="w", padx=5)
        self.encryption_key_var = tk.StringVar(value="")
        self.encryption_key_entry = ttk.Entry(security_frame, textvariable=self.encryption_key_var,
                                            width=20, show="*", state="disabled")
        self.encryption_key_entry.grid(row=1, column=3, padx=5, pady=2)
    
    def create_stats_tab(self):
        """Create statistics display tab"""
        # Statistics display
        stats_frame = ttk.LabelFrame(self.stats_tab, text="Simulation Statistics", padding=10)
        stats_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Statistics text area
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, width=50)
        self.stats_text.pack(fill="both", expand=True)
        
        # Refresh button
        ttk.Button(stats_frame, text="Refresh Statistics", 
                  command=self.refresh_statistics).pack(pady=5)
    
    def set_callback(self, event_name: str, callback: Callable):
        """Set callback for events"""
        self.callbacks[event_name] = callback
    
    def _call_callback(self, event_name: str, *args, **kwargs):
        """Call registered callback if exists"""
        if event_name in self.callbacks:
            self.callbacks[event_name](*args, **kwargs)
    
    def browse_terrain_path(self):
        """Browse for terrain boundaries file"""
        filename = filedialog.askopenfilename(
            title="Select Terrain Boundaries File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="terrain_boundaries.json"
        )
        if filename:
            self.terrain_path_var.set(filename)
    
    def browse_entity_db_path(self):
        """Browse for entity database file"""
        filename = filedialog.askopenfilename(
            title="Select Entity Database File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.entity_db_path_var.set(filename)
    
    def load_terrain_data(self):
        """Load terrain data"""
        self._call_callback("load_terrain", self.terrain_path_var.get())
    
    def refresh_terrain_data(self):
        """Refresh terrain data from current path"""
        if self.terrain_path_var.get():
            self._call_callback("load_terrain", self.terrain_path_var.get())
        else:
            messagebox.showwarning("No Path", "Please specify a terrain sync path first.")
    
    def reload_entity_database(self):
        """Reload entity database"""
        self._call_callback("reload_entities", self.entity_db_path_var.get())
    
    def refresh_entity_database(self):
        """Refresh entity database from current path"""
        if self.entity_db_path_var.get():
            self._call_callback("reload_entities", self.entity_db_path_var.get())
        else:
            # Try to reload with default path (None will use config path)
            self._call_callback("reload_entities", None)
    
    def toggle_manual_boundaries(self):
        """Toggle manual boundary controls"""
        if self.use_imported_var.get():
            # Disable manual controls
            for widget in self.manual_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.config(state="disabled")
        else:
            # Enable manual controls
            for widget in self.manual_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.config(state="normal")
    
    def apply_manual_boundaries(self):
        """Apply manual boundary settings"""
        if not self.use_imported_var.get():
            boundaries = {
                "min_x": self.boundary_vars["x_min"].get(),
                "max_x": self.boundary_vars["x_max"].get(),
                "min_z": self.boundary_vars["z_min"].get(),
                "max_z": self.boundary_vars["z_max"].get(),
                "min_y": self.boundary_vars["y_min"].get(),
                "max_y": self.boundary_vars["y_max"].get()
            }
            self._call_callback("set_manual_boundaries", boundaries)
    
    def start_simulation(self):
        """Start simulation"""
        params = self.get_simulation_params()
        self._call_callback("start_simulation", params)
        
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
    
    def stop_simulation(self):
        """Stop simulation"""
        self._call_callback("stop_simulation")
        
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def clear_entities(self):
        """Clear all entities"""
        self._call_callback("clear_entities")
    
    def on_speed_multiplier_changed(self, *args):
        """Handle speed multiplier change"""
        try:
            multiplier_str = self.speed_multiplier_var.get()
            if multiplier_str == "" or multiplier_str == ".":
                return  # Ignore empty or incomplete input
            multiplier = float(multiplier_str)
            self._call_callback("speed_multiplier_changed", multiplier)
        except (ValueError, TclError):
            # Ignore invalid input, don't crash
            pass
    
    def refresh_statistics(self):
        """Refresh statistics display"""
        self._call_callback("refresh_statistics")
    
    def update_terrain_info(self, info_text: str):
        """Update terrain information display"""
        self.terrain_info_var.set(info_text)
    
    def update_entity_db_info(self, info_text: str):
        """Update entity database information display"""
        self.entity_db_info_var.set(info_text)
    
    def update_imported_entities_list(self, entity_types: List[Dict[str, Any]]):
        """Update the imported entities list display"""
        # Clear current list
        self.imported_entities_listbox.delete(0, tk.END)
        
        # Add entity types to list
        for entity in entity_types:
            # Format: "ID - Name (Category/Subcategory)"
            display_text = f"{entity.get('id', 'Unknown')} - {entity.get('name', 'Unknown')} ({entity.get('category', 'Unknown')}/{entity.get('subcategory', 'Unknown')})"
            self.imported_entities_listbox.insert(tk.END, display_text)
        
        # Update count label
        count = len(entity_types)
        self.entity_count_label.config(text=f"{count} entity types loaded")
    
    def update_statistics(self, stats_text: str):
        """Update statistics display"""
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def get_simulation_params(self) -> Dict[str, Any]:
        """Get current simulation parameters"""
        return {
            "max_entities": self.max_entities_var.get(),
            "spawn_rate": self.spawn_rate_var.get(),
            "update_rate": self.update_rate_var.get(),
            "zmq_port": self.zmq_port_var.get(),
            "zmq_address": self.zmq_address_var.get(),
            "zmq_protocol": self.zmq_protocol_var.get(),
            "zmq_bind_interface": self.zmq_bind_interface_var.get(),
            "zmq_connection_timeout": self.connection_timeout_var.get(),
            "zmq_max_queue_size": self.queue_size_var.get(),
            "broadcast_enabled": self.broadcast_enabled_var.get(),
            "broadcast_rate": self.broadcast_rate_var.get(),
            "connection_retry_count": self.retry_count_var.get(),
            "heartbeat_interval": self.heartbeat_interval_var.get(),
            "enable_authentication": self.enable_auth_var.get(),
            "auth_key": self.auth_key_var.get(),
            "enable_encryption": self.enable_encryption_var.get(),
            "encryption_key": self.encryption_key_var.get(),
            "use_imported_terrain": self.use_imported_var.get(),
            "manual_boundaries": {
                key: var.get() for key, var in self.boundary_vars.items()
            } if not self.use_imported_var.get() else None
        }
    
    def toggle_advanced_network(self):
        """Toggle visibility of advanced network settings"""
        if self.show_advanced_var.get():
            self.advanced_settings_frame.pack(fill="x", pady=5)
            self.advanced_toggle_btn.config(text="Hide Advanced Settings")
            self.show_advanced_var.set(False)  # Reset for next toggle
        else:
            self.advanced_settings_frame.pack_forget()
            self.advanced_toggle_btn.config(text="Show Advanced Settings")
            self.show_advanced_var.set(True)  # Set for next toggle
    
    def toggle_auth_controls(self):
        """Enable/disable authentication controls"""
        if self.enable_auth_var.get():
            self.auth_key_entry.config(state="normal")
        else:
            self.auth_key_entry.config(state="disabled")
            self.auth_key_var.set("")
    
    def toggle_encryption_controls(self):
        """Enable/disable encryption controls"""
        if self.enable_encryption_var.get():
            self.encryption_key_entry.config(state="normal")
        else:
            self.encryption_key_entry.config(state="disabled")
            self.encryption_key_var.set("")
    
    def populate_entity_types(self, entity_types: List[Dict[str, Any]]):
        """Populate the entity type dropdown with available types"""
        if hasattr(self, 'entity_type_combo'):
            # Format entity types for display
            entity_names = []
            for entity in entity_types:
                name = entity.get('displayName', entity.get('name', 'Unknown'))
                category = entity.get('category', 'Unknown')
                entity_names.append(f"{name} ({category})")
            
            self.entity_type_combo['values'] = entity_names
            if entity_names:
                self.entity_type_combo.current(0)
    
    def spawn_entities(self, count: int):
        """Spawn specified number of entities"""
        if not hasattr(self, 'entity_type_combo') or not self.entity_type_var.get():
            messagebox.showwarning("No Entity Type", "Please select an entity type to spawn")
            return
        
        # Get selected entity type and disposition
        entity_type = self.entity_type_var.get()
        disposition = self.disposition_var.get()
        
        # Call the callback to actually spawn entities
        self._call_callback("spawn_entities", entity_type, disposition, count)
    
    def spawn_custom(self):
        """Spawn custom number of entities"""
        count = self.spawn_count_var.get()
        if count < 1:
            messagebox.showwarning("Invalid Count", "Spawn count must be at least 1")
            return
        
        self.spawn_entities(count)
    
    def spawn_random_entities(self, count: int):
        """Spawn random entities"""
        if count < 1:
            messagebox.showwarning("Invalid Count", "Spawn count must be at least 1")
            return
        
        try:
            self._call_callback("spawn_random_entities", count)
        except Exception as e:
            messagebox.showerror("Spawn Error", f"Failed to spawn random entities: {e}")
    
    def set_callback(self, event_name: str, callback: Callable):
        """Set callback for control events"""
        self.callbacks[event_name] = callback
    
    def _call_callback(self, event_name: str, *args, **kwargs):
        """Call registered callback if exists"""
        if event_name in self.callbacks:
            try:
                return self.callbacks[event_name](*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in callback {event_name}: {e}")
                messagebox.showerror("Error", f"Error in {event_name}: {str(e)}")
    
    def start_simulation(self):
        """Start simulation callback"""
        # Get current simulation parameters from the GUI
        params = self.get_simulation_params()
        self._call_callback("start_simulation", params)
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        # Update status indicator
        if hasattr(self, 'status_indicator'):
            self.status_indicator.config(text="● RUNNING", foreground="#2E7D32")  # Green for running
    
    def stop_simulation(self):
        """Stop simulation callback"""
        self._call_callback("stop_simulation")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        # Update status indicator
        if hasattr(self, 'status_indicator'):
            self.status_indicator.config(text="● STOPPED", foreground="#B71C1C")  # Red for stopped
    
    def clear_entities(self):
        """Clear all entities callback"""
        if messagebox.askyesno("Clear Entities", "Are you sure you want to clear all entities?"):
            self._call_callback("clear_entities")


class BattlespaceSimulatorGUI:
    """Main GUI application for the battlespace simulator"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Battlespace Simulator")
        self.root.geometry("1200x800")
        
        # Load Azure theme
        self.load_azure_theme()
        
        # Data
        self.entities_data = {}
        self.selected_entity = None
        
        # Callbacks for main application
        self.callbacks = {}
        
        self.setup_ui()
        self.setup_menu()
        
        # Auto-refresh timer
        self.auto_refresh_timer = None
        self.auto_refresh_interval = 5000  # 5 seconds
        self.start_auto_refresh()
    
    def load_azure_theme(self):
        """Load the Azure ttk theme"""
        try:
            # Try to load the Azure theme
            import os
            theme_path = os.path.join(os.path.dirname(__file__), "Azure-ttk-theme-main", "azure.tcl")
            if os.path.exists(theme_path):
                self.root.tk.call("source", theme_path)
                
                # Load theme preference
                preferred_theme = self.load_theme_preference()
                self.root.tk.call("set_theme", preferred_theme)
                self._current_theme = preferred_theme  # Track current theme
                
                self.theme_loaded = True
                logging.info(f"Azure {preferred_theme} theme loaded successfully")
            else:
                self.theme_loaded = False
                self._current_theme = "dark"  # Default theme
                logging.warning(f"Azure theme not found at {theme_path}")
        except Exception as e:
            self.theme_loaded = False
            self._current_theme = "dark"  # Default theme
            logging.error(f"Failed to load Azure theme: {e}")
    
    def set_theme(self, theme_name: str):
        """Switch between light and dark themes"""
        if self.theme_loaded:
            try:
                self.root.tk.call("set_theme", theme_name)
                self.save_theme_preference(theme_name)
                self._current_theme = theme_name  # Track current theme
                logging.info(f"Switched to {theme_name} theme")
                self.update_status(f"Theme changed to {theme_name}")
            except Exception as e:
                logging.error(f"Failed to switch theme: {e}")
        else:
            messagebox.showwarning("Theme Not Available", "Azure theme is not loaded")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        current = getattr(self, '_current_theme', 'dark')
        new_theme = 'light' if current == 'dark' else 'dark'
        self.set_theme(new_theme)
    
    def load_theme_preference(self) -> str:
        """Load saved theme preference"""
        try:
            import os
            pref_file = os.path.join(os.path.dirname(__file__), ".theme_preference")
            if os.path.exists(pref_file):
                with open(pref_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return "dark"  # Default theme
    
    def save_theme_preference(self, theme_name: str):
        """Save theme preference"""
        try:
            import os
            pref_file = os.path.join(os.path.dirname(__file__), ".theme_preference")
            with open(pref_file, 'w') as f:
                f.write(theme_name)
        except Exception as e:
            logging.error(f"Failed to save theme preference: {e}")
    
    def setup_ui(self):
        """Setup main UI layout with vertical scrolling and horizontal responsiveness"""
        # Create outer frame for the scrollable container
        outer_frame = ttk.Frame(self.root)
        outer_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas and vertical scrollbar only
        canvas = tk.Canvas(outer_frame, highlightthickness=0)
        scrollbar_v = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame inside canvas
        self.scrollable_frame = ttk.Frame(canvas)
        
        # Configure canvas scrolling
        def _configure_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        def _configure_canvas_width(event=None):
            # Make the scrollable frame width match the canvas width for horizontal responsiveness
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_frame.bind("<Configure>", _configure_scrollregion)
        canvas.bind("<Configure>", _configure_canvas_width)
        
        # Create window in canvas and store reference for width configuration
        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_v.set)
        
        # Pack scrollbar and canvas (no horizontal scrollbar)
        scrollbar_v.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Create main paned window inside the scrollable frame
        main_paned = ttk.PanedWindow(self.scrollable_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill="both", expand=True)
        
        # Left pane - Entity List
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Left pane - just the entity summary list
        self.summary_frame = EntitySummaryFrame(left_frame, 
                                              on_entity_select=self.on_entity_selected)
        self.summary_frame.pack(fill="both", expand=True)
        
        # Center pane - Simulation Control
        self.control_frame = SimulationControlFrame(main_paned)
        main_paned.add(self.control_frame, weight=1)
        
        # Right pane - Entity Details
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Right pane - detailed view
        self.detail_frame = EntityDetailFrame(right_frame)
        self.detail_frame.pack(fill="both", expand=True)
        
        # Status bar (outside the scrollable area)
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Configuration", command=self.load_configuration)
        file_menu.add_command(label="Save Configuration", command=self.save_configuration)
        file_menu.add_separator()
        file_menu.add_command(label="Export Statistics", command=self.export_statistics)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Entities", command=self.refresh_entities)
        view_menu.add_command(label="Clear Selection", command=self.clear_selection)
        view_menu.add_separator()
        view_menu.add_command(label="Dark Theme", command=lambda: self.set_theme("dark"))
        view_menu.add_command(label="Light Theme", command=lambda: self.set_theme("light"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def set_callback(self, event_name: str, callback: Callable):
        """Set callback for main application events"""
        self.callbacks[event_name] = callback
        # Also set on control frame for relevant events
        self.control_frame.set_callback(event_name, callback)
    
    def _call_callback(self, event_name: str, *args, **kwargs):
        """Call registered callback if exists"""
        if event_name in self.callbacks:
            try:
                return self.callbacks[event_name](*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in callback {event_name}: {e}")
                messagebox.showerror("Error", f"Error in {event_name}: {str(e)}")
    
    def on_entity_selected(self, entity_data: Dict[str, Any]):
        """Handle entity selection"""
        self.selected_entity = entity_data
        self.detail_frame.update_entity_info(entity_data)
    
    def update_entities(self, entities: Dict[str, Dict[str, Any]]):
        """Update entity data"""
        self.entities_data = entities
        self.summary_frame.update_entities(entities)
        
        # Update selected entity if it still exists
        if self.selected_entity:
            entity_id = self.selected_entity.get("entity_id")
            if entity_id and entity_id in entities:
                self.detail_frame.update_entity_info(entities[entity_id])
            else:
                self.clear_selection()
    
    def clear_selection(self):
        """Clear current entity selection"""
        self.selected_entity = None
        self.detail_frame.clear_info()
    
    def refresh_entities(self):
        """Refresh entity display"""
        self._call_callback("refresh_entities")
    
    def start_auto_refresh(self):
        """Start automatic entity refresh"""
        self.refresh_entities()
        self.auto_refresh_timer = self.root.after(self.auto_refresh_interval, 
                                                 self.start_auto_refresh)
    
    def stop_auto_refresh(self):
        """Stop automatic entity refresh"""
        if self.auto_refresh_timer:
            try:
                self.root.after_cancel(self.auto_refresh_timer)
            except Exception as e:
                logging.error(f"Error canceling auto refresh timer: {e}")
            finally:
                self.auto_refresh_timer = None
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_var.set(message)
    
    # Helper properties to access simulation parameters from control frame
    @property
    def max_entities_var(self):
        return self.control_frame.max_entities_var
    
    @property
    def spawn_rate_var(self):
        return self.control_frame.spawn_rate_var
    
    @property
    def update_rate_var(self):
        return self.control_frame.update_rate_var
    
    @property
    def broadcast_rate_var(self):
        return self.control_frame.broadcast_rate_var
    
    @property
    def port_var(self):
        return self.control_frame.zmq_port_var
    
    @property
    def current_theme(self):
        """Get current theme"""
        return getattr(self, '_current_theme', 'dark')
    
    @property
    def auto_scroll_var(self):
        """Get auto scroll variable"""
        return getattr(self.summary_frame, 'auto_scroll_var', tk.BooleanVar(value=True))
    
    def update_entity_info(self, info_text: str):
        """Update entity information display"""
        if hasattr(self.control_frame, 'update_entity_db_info'):
            self.control_frame.update_entity_db_info(info_text)
    
    def update_terrain_info(self, info_text: str):
        """Update terrain information display"""
        if hasattr(self.control_frame, 'update_terrain_info'):
            self.control_frame.update_terrain_info(info_text)
    
    def load_configuration(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self._call_callback("load_config", filename)
    
    def save_configuration(self):
        """Save configuration to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self._call_callback("save_config", filename)
    
    def export_statistics(self):
        """Export statistics to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Statistics",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self._call_callback("export_stats", filename)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Battlespace Simulator v1.0

A Python-based entity simulator for 3D battlespace visualization.
Generates TEDF-compliant messages for Unity consumption via ZeroMQ.

Features:
• Entity simulation with realistic movement patterns
• TEDF message broadcasting
• Terrain boundary integration
• Real-time entity tracking and visualization

Built with Python, tkinter, and ZeroMQ."""
        
        messagebox.showinfo("About Battlespace Simulator", about_text)
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()
    
    def destroy(self):
        """Clean up and destroy the GUI"""
        try:
            self.stop_auto_refresh()
        except Exception as e:
            logging.error(f"Error stopping auto refresh: {e}")
        
        try:
            if hasattr(self, 'root') and self.root:
                # Check if root still exists before trying to destroy
                try:
                    self.root.winfo_exists()  # This will raise error if already destroyed
                    self.root.quit()  # Stop mainloop first
                    self.root.destroy()
                except tk.TclError:
                    # GUI already destroyed, this is fine
                    pass
        except Exception as e:
            logging.error(f"Error destroying GUI: {e}")