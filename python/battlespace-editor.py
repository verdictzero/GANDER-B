import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
from datetime import datetime
import os
from typing import Dict, List, Any
import copy

class BattlespaceEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Battlespace Entity Definition Editor")
        self.geometry("1200x800")

        # Initialize data structure
        self.data = self.get_default_data()
        self.current_file = None
        self.modified = False
        self.current_entity_index = None

        # Load Azure theme
        self.load_azure_theme()

        # Configure style
        self.style = ttk.Style()

        # Create GUI
        self.create_menu()
        self.create_main_interface()

        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_azure_theme(self):
        """Load the Azure ttk theme"""
        try:
            # Try to load the Azure theme
            theme_path = os.path.join(os.path.dirname(__file__), "Azure-ttk-theme-main", "azure.tcl")
            if os.path.exists(theme_path):
                self.tk.call("source", theme_path)
                
                # Load theme preference
                preferred_theme = self.load_theme_preference()
                self.tk.call("set_theme", preferred_theme)
                
                self.theme_loaded = True
                print(f"Azure {preferred_theme} theme loaded successfully")
            else:
                self.theme_loaded = False
                self.style.theme_use('clam')  # Fallback theme
                print(f"Azure theme not found at {theme_path}, using fallback theme")
        except Exception as e:
            self.theme_loaded = False
            self.style.theme_use('clam')  # Fallback theme
            print(f"Failed to load Azure theme: {e}, using fallback theme")
    
    def set_theme(self, theme_name: str):
        """Switch between light and dark themes"""
        if self.theme_loaded:
            try:
                self.tk.call("set_theme", theme_name)
                self.save_theme_preference(theme_name)
                print(f"Switched to {theme_name} theme")
            except Exception as e:
                print(f"Failed to switch theme: {e}")
        else:
            messagebox.showwarning("Theme Not Available", "Azure theme is not loaded")
    
    def load_theme_preference(self) -> str:
        """Load saved theme preference"""
        try:
            pref_file = os.path.join(os.path.dirname(__file__), ".theme_preference_editor")
            if os.path.exists(pref_file):
                with open(pref_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return "dark"  # Default theme
    
    def save_theme_preference(self, theme_name: str):
        """Save theme preference"""
        try:
            pref_file = os.path.join(os.path.dirname(__file__), ".theme_preference_editor")
            with open(pref_file, 'w') as f:
                f.write(theme_name)
        except Exception as e:
            print(f"Failed to save theme preference: {e}")

    def get_default_data(self):
        """Return default data structure"""
        return {
            "version": "1.0",
            "metadata": {
                "description": "Battlespace Entity Definitions and Disposition Colors",
                "lastModified": datetime.now().isoformat() + "Z",
                "author": "Battlespace Visualization System"
            },
            "dispositions": {
                "colors": {
                    "FRIENDLY": {
                        "primary": {"hex": "#00FF00", "rgb": [0, 255, 0], "rgba": [0, 255, 0, 255],
                                   "unity_color": {"r": 0.0, "g": 1.0, "b": 0.0, "a": 1.0}},
                        "secondary": {"hex": "#66FF66", "rgb": [102, 255, 102], "rgba": [102, 255, 102, 255],
                                     "unity_color": {"r": 0.4, "g": 1.0, "b": 0.4, "a": 1.0}},
                        "gizmo": {"hex": "#00CC00", "rgb": [0, 204, 0], "rgba": [0, 204, 0, 200],
                                 "unity_color": {"r": 0.0, "g": 0.8, "b": 0.0, "a": 0.78}}
                    },
                    "HOSTILE": {
                        "primary": {"hex": "#FF0000", "rgb": [255, 0, 0], "rgba": [255, 0, 0, 255],
                                   "unity_color": {"r": 1.0, "g": 0.0, "b": 0.0, "a": 1.0}},
                        "secondary": {"hex": "#FF6666", "rgb": [255, 102, 102], "rgba": [255, 102, 102, 255],
                                     "unity_color": {"r": 1.0, "g": 0.4, "b": 0.4, "a": 1.0}},
                        "gizmo": {"hex": "#CC0000", "rgb": [204, 0, 0], "rgba": [204, 0, 0, 200],
                                 "unity_color": {"r": 0.8, "g": 0.0, "b": 0.0, "a": 0.78}}
                    },
                    "NEUTRAL": {
                        "primary": {"hex": "#FFFF00", "rgb": [255, 255, 0], "rgba": [255, 255, 0, 255],
                                   "unity_color": {"r": 1.0, "g": 1.0, "b": 0.0, "a": 1.0}},
                        "secondary": {"hex": "#FFFF66", "rgb": [255, 255, 102], "rgba": [255, 255, 102, 255],
                                     "unity_color": {"r": 1.0, "g": 1.0, "b": 0.4, "a": 1.0}},
                        "gizmo": {"hex": "#CCCC00", "rgb": [204, 204, 0], "rgba": [204, 204, 0, 200],
                                 "unity_color": {"r": 0.8, "g": 0.8, "b": 0.0, "a": 0.78}}
                    },
                    "UNKNOWN": {
                        "primary": {"hex": "#FFFFFF", "rgb": [255, 255, 255], "rgba": [255, 255, 255, 255],
                                   "unity_color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}},
                        "secondary": {"hex": "#CCCCCC", "rgb": [204, 204, 204], "rgba": [204, 204, 204, 255],
                                     "unity_color": {"r": 0.8, "g": 0.8, "b": 0.8, "a": 1.0}},
                        "gizmo": {"hex": "#999999", "rgb": [153, 153, 153], "rgba": [153, 153, 153, 200],
                                 "unity_color": {"r": 0.6, "g": 0.6, "b": 0.6, "a": 0.78}}
                    }
                },
                "symbols": {
                    "FRIENDLY": "F",
                    "HOSTILE": "H",
                    "NEUTRAL": "N",
                    "UNKNOWN": "U"
                }
            },
            "entity_categories": {
                "AIR": {
                    "description": "Aerial vehicles and aircraft",
                    "default_altitude": 500.0,
                    "movement_layer": "air_space"
                },
                "GROUND": {
                    "description": "Ground-based vehicles and personnel",
                    "default_altitude": 0.0,
                    "movement_layer": "terrain_surface"
                },
                "NAVAL": {
                    "description": "Naval vessels and watercraft",
                    "default_altitude": 0.0,
                    "movement_layer": "water_surface"
                }
            },
            "entities": []
        }

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Entity", command=self.add_entity)
        edit_menu.add_command(label="Duplicate Entity", command=self.duplicate_entity)
        edit_menu.add_command(label="Delete Entity", command=self.delete_entity)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dark Theme", command=lambda: self.set_theme("dark"))
        view_menu.add_command(label="Light Theme", command=lambda: self.set_theme("light"))

        # Bind shortcuts
        self.bind('<Control-n>', lambda e: self.new_file())
        self.bind('<Control-o>', lambda e: self.open_file())
        self.bind('<Control-s>', lambda e: self.save_file())
        self.bind('<Control-Shift-S>', lambda e: self.save_file_as())

    def create_main_interface(self):
        """Create main interface with tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.create_metadata_tab()
        self.create_dispositions_tab()
        self.create_categories_tab()
        self.create_entities_tab()

        # Status bar
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_metadata_tab(self):
        """Create metadata editing tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Metadata")

        # Create form
        ttk.Label(frame, text="Version:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.version_var = tk.StringVar(value=self.data["version"])
        ttk.Entry(frame, textvariable=self.version_var, width=30).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.description_var = tk.StringVar(value=self.data["metadata"]["description"])
        ttk.Entry(frame, textvariable=self.description_var, width=50).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Author:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.author_var = tk.StringVar(value=self.data["metadata"]["author"])
        ttk.Entry(frame, textvariable=self.author_var, width=50).grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Last Modified:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.last_modified_label = ttk.Label(frame, text=self.data["metadata"]["lastModified"])
        self.last_modified_label.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)

        # Update button
        ttk.Button(frame, text="Update Metadata", command=self.update_metadata).grid(row=4, column=1, padx=10, pady=20)

    def create_dispositions_tab(self):
        """Create dispositions editing tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Dispositions")

        # Create main container with scrollbar
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create disposition editors
        self.disposition_vars = {}
        row = 0

        for disp_type in ["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"]:
            # Header
            header_frame = ttk.LabelFrame(scrollable_frame, text=disp_type, padding=10)
            header_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

            # Symbol
            ttk.Label(header_frame, text="Symbol:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
            symbol_var = tk.StringVar(value=self.data["dispositions"]["symbols"][disp_type])
            self.disposition_vars[f"{disp_type}_symbol"] = symbol_var
            ttk.Entry(header_frame, textvariable=symbol_var, width=5).grid(row=0, column=1, padx=5, pady=2)

            # Colors
            color_row = 1
            for color_type in ["primary", "secondary", "gizmo"]:
                ttk.Label(header_frame, text=f"{color_type.capitalize()} Color:").grid(row=color_row, column=0, sticky=tk.W, padx=5, pady=2)

                color_data = self.data["dispositions"]["colors"][disp_type][color_type]
                color_frame = ttk.Frame(header_frame)
                color_frame.grid(row=color_row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)

                # Color display
                color_label = tk.Label(color_frame, width=10, height=1, bg=color_data["hex"], relief=tk.RAISED)
                color_label.pack(side=tk.LEFT, padx=5)

                # Hex value
                hex_var = tk.StringVar(value=color_data["hex"])
                self.disposition_vars[f"{disp_type}_{color_type}_hex"] = hex_var
                ttk.Entry(color_frame, textvariable=hex_var, width=10).pack(side=tk.LEFT, padx=5)

                # Color picker button
                ttk.Button(color_frame, text="Choose",
                          command=lambda d=disp_type, c=color_type, l=color_label: self.choose_color(d, c, l)).pack(side=tk.LEFT)

                color_row += 1

            row += 1

        # Update button
        ttk.Button(scrollable_frame, text="Update Dispositions", command=self.update_dispositions).grid(row=row, column=0, columnspan=3, pady=20)

    def create_categories_tab(self):
        """Create categories editing tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Categories")

        # Categories list
        list_frame = ttk.Frame(frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)

        ttk.Label(list_frame, text="Categories:").pack()

        self.categories_listbox = tk.Listbox(list_frame, width=30, height=10)
        self.categories_listbox.pack(fill=tk.BOTH, expand=True)
        self.categories_listbox.bind('<<ListboxSelect>>', self.on_category_select)

        # Buttons
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_category).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_category).pack(side=tk.LEFT, padx=2)

        # Category editor
        editor_frame = ttk.LabelFrame(frame, text="Category Details", padding=10)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(editor_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.category_name_var = tk.StringVar()
        self.category_name_entry = ttk.Entry(editor_frame, textvariable=self.category_name_var, width=30)
        self.category_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(editor_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.category_desc_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.category_desc_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(editor_frame, text="Default Altitude:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.category_altitude_var = tk.DoubleVar()
        ttk.Entry(editor_frame, textvariable=self.category_altitude_var, width=15).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(editor_frame, text="Movement Layer:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.category_layer_var = tk.StringVar()
        layer_combo = ttk.Combobox(editor_frame, textvariable=self.category_layer_var, width=25)
        layer_combo['values'] = ('air_space', 'terrain_surface', 'water_surface', 'subsurface')
        layer_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Button(editor_frame, text="Update Category", command=self.update_category).grid(row=4, column=1, pady=20)

        # Load categories
        self.load_categories_list()

    def create_entities_tab(self):
        """Create entities editing tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Entities")

        # Create paned window
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Entity list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Entities:", font=('Arial', 10, 'bold')).pack(padx=5, pady=5)

        # Search box
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=5)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_entities)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Entity treeview
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.entity_tree = ttk.Treeview(tree_frame, columns=('category', 'subcategory'), show='tree headings')
        self.entity_tree.heading('#0', text='Name')
        self.entity_tree.heading('category', text='Category')
        self.entity_tree.heading('subcategory', text='Subcategory')
        self.entity_tree.column('#0', width=200)
        self.entity_tree.column('category', width=100)
        self.entity_tree.column('subcategory', width=100)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.entity_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.entity_tree.xview)
        self.entity_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.entity_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.entity_tree.bind('<<TreeviewSelect>>', self.on_entity_select)

        # Entity buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Add Entity", command=self.add_entity).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Duplicate", command=self.duplicate_entity).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_entity).pack(side=tk.LEFT, padx=2)

        # Right panel - Entity editor
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Create scrollable frame
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.entity_editor_frame = ttk.Frame(canvas)

        self.entity_editor_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.entity_editor_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.create_entity_editor()
        self.load_entities_list()

    def create_entity_editor(self):
        """Create entity editing form"""
        # Basic Info
        basic_frame = ttk.LabelFrame(self.entity_editor_frame, text="Basic Information", padding=10)
        basic_frame.pack(fill=tk.X, padx=10, pady=5)

        self.entity_vars = {}

        # ID
        ttk.Label(basic_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['id'] = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.entity_vars['id'], width=30).grid(row=0, column=1, padx=5, pady=2)

        # Name
        ttk.Label(basic_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['name'] = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.entity_vars['name'], width=30).grid(row=1, column=1, padx=5, pady=2)

        # Description
        ttk.Label(basic_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['description'] = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.entity_vars['description'], width=50).grid(row=2, column=1, padx=5, pady=2)

        # Category
        ttk.Label(basic_frame, text="Category:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['category'] = tk.StringVar()
        cat_combo = ttk.Combobox(basic_frame, textvariable=self.entity_vars['category'], width=20)
        cat_combo['values'] = list(self.data['entity_categories'].keys())
        cat_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        # Subcategory
        ttk.Label(basic_frame, text="Subcategory:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['subcategory'] = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.entity_vars['subcategory'], width=30).grid(row=4, column=1, padx=5, pady=2)

        # Specification
        ttk.Label(basic_frame, text="Specification:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['specification'] = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.entity_vars['specification'], width=30).grid(row=5, column=1, padx=5, pady=2)

        # NATO Symbol
        ttk.Label(basic_frame, text="NATO Symbol:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['nato_symbol'] = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.entity_vars['nato_symbol'], width=20).grid(row=6, column=1, sticky=tk.W, padx=5, pady=2)

        # Kinematics
        kinematics_frame = ttk.LabelFrame(self.entity_editor_frame, text="Kinematics", padding=10)
        kinematics_frame.pack(fill=tk.X, padx=10, pady=5)

        # Speed settings
        speed_row = 0
        for speed_type in ['minSpeed', 'maxSpeed', 'cruiseSpeed']:
            ttk.Label(kinematics_frame, text=f"{speed_type}:").grid(row=speed_row//3, column=(speed_row%3)*2, sticky=tk.W, padx=5, pady=2)
            self.entity_vars[speed_type] = tk.DoubleVar()
            ttk.Entry(kinematics_frame, textvariable=self.entity_vars[speed_type], width=10).grid(row=speed_row//3, column=(speed_row%3)*2+1, padx=5, pady=2)
            speed_row += 1

        # Movement settings
        move_row = 2
        for move_type in ['acceleration', 'deceleration', 'turnRate']:
            ttk.Label(kinematics_frame, text=f"{move_type}:").grid(row=move_row//3+1, column=(move_row%3)*2, sticky=tk.W, padx=5, pady=2)
            self.entity_vars[move_type] = tk.DoubleVar()
            ttk.Entry(kinematics_frame, textvariable=self.entity_vars[move_type], width=10).grid(row=move_row//3+1, column=(move_row%3)*2+1, padx=5, pady=2)
            move_row += 1

        # Movement type
        ttk.Label(kinematics_frame, text="Movement Type:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['movement_type'] = tk.StringVar()
        move_combo = ttk.Combobox(kinematics_frame, textvariable=self.entity_vars['movement_type'], width=20)
        move_combo['values'] = ('3D_FLIGHT', '3D_ROTORCRAFT', 'GROUND_TRACKED', 'GROUND_WHEELED', 'GROUND_FOOT', 'NAVAL_SURFACE', 'NAVAL_SUBSURFACE')
        move_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)

        # Disposition types
        disp_frame = ttk.LabelFrame(self.entity_editor_frame, text="Allowed Dispositions", padding=10)
        disp_frame.pack(fill=tk.X, padx=10, pady=5)

        self.disp_checkboxes = {}
        for i, disp in enumerate(['FRIENDLY', 'HOSTILE', 'NEUTRAL', 'UNKNOWN']):
            var = tk.BooleanVar(value=True)
            self.disp_checkboxes[disp] = var
            ttk.Checkbutton(disp_frame, text=disp, variable=var).grid(row=0, column=i, padx=10, pady=5)

        # Simulation parameters
        sim_frame = ttk.LabelFrame(self.entity_editor_frame, text="Simulation Parameters", padding=10)
        sim_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(sim_frame, text="Spawn Probability:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['spawn_probability'] = tk.DoubleVar()
        ttk.Entry(sim_frame, textvariable=self.entity_vars['spawn_probability'], width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(sim_frame, text="Max Concurrent:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['max_concurrent'] = tk.IntVar()
        ttk.Entry(sim_frame, textvariable=self.entity_vars['max_concurrent'], width=10).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(sim_frame, text="Heading Variance:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['default_heading_variance'] = tk.DoubleVar()
        ttk.Entry(sim_frame, textvariable=self.entity_vars['default_heading_variance'], width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(sim_frame, text="Patrol Behavior:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.entity_vars['patrol_behavior'] = tk.StringVar()
        patrol_combo = ttk.Combobox(sim_frame, textvariable=self.entity_vars['patrol_behavior'], width=20)
        patrol_combo['values'] = ('RANDOM_WAYPOINT', 'ROAD_FOLLOWING', 'AREA_SWEEP', 'TRANSPORT_ROUTE', 'PERIMETER_SCOUT', 'STATIC', 'PATROL_ROUTE')
        patrol_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)

        # Update button
        ttk.Button(self.entity_editor_frame, text="Update Entity", command=self.update_entity).pack(pady=20)

    def choose_color(self, disposition, color_type, label):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(initialcolor=self.data["dispositions"]["colors"][disposition][color_type]["hex"])
        if color[1]:  # If color was chosen
            hex_color = color[1]
            rgb = [int(color[0][0]), int(color[0][1]), int(color[0][2])]

            # Update display
            label.config(bg=hex_color)
            self.disposition_vars[f"{disposition}_{color_type}_hex"].set(hex_color)

            # Update data structure
            self.data["dispositions"]["colors"][disposition][color_type]["hex"] = hex_color
            self.data["dispositions"]["colors"][disposition][color_type]["rgb"] = rgb
            self.data["dispositions"]["colors"][disposition][color_type]["rgba"] = rgb + [255] if color_type != "gizmo" else rgb + [200]

            # Update unity color
            unity_color = {
                "r": rgb[0] / 255.0,
                "g": rgb[1] / 255.0,
                "b": rgb[2] / 255.0,
                "a": 1.0 if color_type != "gizmo" else 0.78
            }
            self.data["dispositions"]["colors"][disposition][color_type]["unity_color"] = unity_color

            self.set_modified(True)

    def update_metadata(self):
        """Update metadata from form"""
        self.data["version"] = self.version_var.get()
        self.data["metadata"]["description"] = self.description_var.get()
        self.data["metadata"]["author"] = self.author_var.get()
        self.data["metadata"]["lastModified"] = datetime.now().isoformat() + "Z"
        self.last_modified_label.config(text=self.data["metadata"]["lastModified"])
        self.set_modified(True)
        self.update_status("Metadata updated")

    def update_dispositions(self):
        """Update dispositions from form"""
        for disp_type in ["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"]:
            # Update symbol
            self.data["dispositions"]["symbols"][disp_type] = self.disposition_vars[f"{disp_type}_symbol"].get()

            # Colors are already updated by choose_color

        self.set_modified(True)
        self.update_status("Dispositions updated")

    def load_categories_list(self):
        """Load categories into listbox"""
        self.categories_listbox.delete(0, tk.END)
        for cat_name in self.data["entity_categories"]:
            self.categories_listbox.insert(tk.END, cat_name)

    def on_category_select(self, event):
        """Handle category selection"""
        selection = self.categories_listbox.curselection()
        if selection:
            cat_name = self.categories_listbox.get(selection[0])
            cat_data = self.data["entity_categories"][cat_name]

            self.category_name_var.set(cat_name)
            self.category_desc_var.set(cat_data["description"])
            self.category_altitude_var.set(cat_data["default_altitude"])
            self.category_layer_var.set(cat_data["movement_layer"])

    def add_category(self):
        """Add new category"""
        name = tk.simpledialog.askstring("New Category", "Enter category name:")
        if name and name not in self.data["entity_categories"]:
            self.data["entity_categories"][name] = {
                "description": "New category",
                "default_altitude": 0.0,
                "movement_layer": "terrain_surface"
            }
            self.load_categories_list()
            self.set_modified(True)

    def delete_category(self):
        """Delete selected category"""
        selection = self.categories_listbox.curselection()
        if selection:
            cat_name = self.categories_listbox.get(selection[0])
            if messagebox.askyesno("Delete Category", f"Delete category '{cat_name}'?"):
                del self.data["entity_categories"][cat_name]
                self.load_categories_list()
                self.set_modified(True)

    def update_category(self):
        """Update selected category"""
        selection = self.categories_listbox.curselection()
        if selection:
            old_name = self.categories_listbox.get(selection[0])
            new_name = self.category_name_var.get()

            if old_name != new_name:
                self.data["entity_categories"][new_name] = self.data["entity_categories"].pop(old_name)

            self.data["entity_categories"][new_name] = {
                "description": self.category_desc_var.get(),
                "default_altitude": self.category_altitude_var.get(),
                "movement_layer": self.category_layer_var.get()
            }

            self.load_categories_list()
            self.set_modified(True)
            self.update_status("Category updated")

    def load_entities_list(self):
        """Load entities into treeview"""
        # Clear tree
        for item in self.entity_tree.get_children():
            self.entity_tree.delete(item)

        # Add entities
        for i, entity in enumerate(self.data["entities"]):
            self.entity_tree.insert('', 'end', text=entity["name"],
                                   values=(entity["category"], entity["subcategory"]),
                                   tags=(str(i),))

    def filter_entities(self, *args):
        """Filter entities based on search"""
        search_term = self.search_var.get().lower()

        # Clear tree
        for item in self.entity_tree.get_children():
            self.entity_tree.delete(item)

        # Add filtered entities
        for i, entity in enumerate(self.data["entities"]):
            if (search_term in entity["name"].lower() or
                search_term in entity["description"].lower() or
                search_term in entity["category"].lower()):
                self.entity_tree.insert('', 'end', text=entity["name"],
                                       values=(entity["category"], entity["subcategory"]),
                                       tags=(str(i),))

    def on_entity_select(self, event):
        """Handle entity selection"""
        selection = self.entity_tree.selection()
        if selection:
            item = self.entity_tree.item(selection[0])
            self.current_entity_index = int(item['tags'][0])
            self.load_entity_data(self.current_entity_index)

    def load_entity_data(self, index):
        """Load entity data into editor"""
        entity = self.data["entities"][index]

        # Basic info
        self.entity_vars['id'].set(entity.get('id', ''))
        self.entity_vars['name'].set(entity.get('name', ''))
        self.entity_vars['description'].set(entity.get('description', ''))
        self.entity_vars['category'].set(entity.get('category', ''))
        self.entity_vars['subcategory'].set(entity.get('subcategory', ''))
        self.entity_vars['specification'].set(entity.get('specification', ''))
        self.entity_vars['nato_symbol'].set(entity.get('nato_symbol', ''))

        # Kinematics
        kin = entity.get('kinematics', {})
        for key in ['minSpeed', 'maxSpeed', 'cruiseSpeed', 'acceleration', 'deceleration', 'turnRate']:
            if key in kin:
                self.entity_vars[key].set(kin[key])
        self.entity_vars['movement_type'].set(kin.get('movement_type', ''))

        # Dispositions
        disp_types = entity.get('disposition_types', [])
        for disp, var in self.disp_checkboxes.items():
            var.set(disp in disp_types)

        # Simulation parameters
        sim = entity.get('simulation_parameters', {})
        self.entity_vars['spawn_probability'].set(sim.get('spawn_probability', 0.1))
        self.entity_vars['max_concurrent'].set(sim.get('max_concurrent', 10))
        self.entity_vars['default_heading_variance'].set(sim.get('default_heading_variance', 360.0))
        self.entity_vars['patrol_behavior'].set(sim.get('patrol_behavior', ''))

    def add_entity(self):
        """Add new entity"""
        entity = {
            "id": f"unit_type_{len(self.data['entities'])+1:03d}",
            "name": "New Entity",
            "description": "Description",
            "category": "GROUND",
            "subcategory": "VEHICLE",
            "specification": "GENERIC",
            "nato_symbol": "----------",
            "kinematics": {
                "minSpeed": 0.0,
                "maxSpeed": 50.0,
                "cruiseSpeed": 30.0,
                "acceleration": 5.0,
                "deceleration": 8.0,
                "turnRate": 30.0,
                "movement_type": "GROUND_WHEELED"
            },
            "disposition_types": ["FRIENDLY", "HOSTILE", "NEUTRAL", "UNKNOWN"],
            "simulation_parameters": {
                "spawn_probability": 0.1,
                "max_concurrent": 10,
                "default_heading_variance": 360.0,
                "patrol_behavior": "RANDOM_WAYPOINT"
            }
        }

        self.data["entities"].append(entity)
        self.load_entities_list()
        self.set_modified(True)

        # Select new entity
        self.entity_tree.selection_set(self.entity_tree.get_children()[-1])
        self.entity_tree.focus(self.entity_tree.get_children()[-1])

    def duplicate_entity(self):
        """Duplicate selected entity"""
        if self.current_entity_index is not None:
            entity = copy.deepcopy(self.data["entities"][self.current_entity_index])
            entity["id"] = f"{entity['id']}_copy"
            entity["name"] = f"{entity['name']} (Copy)"

            self.data["entities"].append(entity)
            self.load_entities_list()
            self.set_modified(True)

    def delete_entity(self):
        """Delete selected entity"""
        if self.current_entity_index is not None:
            entity = self.data["entities"][self.current_entity_index]
            if messagebox.askyesno("Delete Entity", f"Delete entity '{entity['name']}'?"):
                del self.data["entities"][self.current_entity_index]
                self.load_entities_list()
                self.current_entity_index = None
                self.set_modified(True)

    def update_entity(self):
        """Update current entity from form"""
        if self.current_entity_index is None:
            messagebox.showwarning("No Selection", "Please select an entity to update")
            return

        entity = self.data["entities"][self.current_entity_index]

        # Basic info
        entity['id'] = self.entity_vars['id'].get()
        entity['name'] = self.entity_vars['name'].get()
        entity['description'] = self.entity_vars['description'].get()
        entity['category'] = self.entity_vars['category'].get()
        entity['subcategory'] = self.entity_vars['subcategory'].get()
        entity['specification'] = self.entity_vars['specification'].get()
        entity['nato_symbol'] = self.entity_vars['nato_symbol'].get()

        # Kinematics
        entity['kinematics'] = {
            'minSpeed': self.entity_vars['minSpeed'].get(),
            'maxSpeed': self.entity_vars['maxSpeed'].get(),
            'cruiseSpeed': self.entity_vars['cruiseSpeed'].get(),
            'acceleration': self.entity_vars['acceleration'].get(),
            'deceleration': self.entity_vars['deceleration'].get(),
            'turnRate': self.entity_vars['turnRate'].get(),
            'movement_type': self.entity_vars['movement_type'].get()
        }

        # Add optional kinematics fields based on entity type
        if entity['category'] == 'AIR':
            entity['kinematics']['climbRate'] = 10.0
            entity['kinematics']['defaultAltitude'] = 500.0
            entity['kinematics']['minAltitude'] = 0.0
            entity['kinematics']['maxAltitude'] = 1000.0

        # Dispositions
        entity['disposition_types'] = [disp for disp, var in self.disp_checkboxes.items() if var.get()]

        # Simulation parameters
        entity['simulation_parameters'] = {
            'spawn_probability': self.entity_vars['spawn_probability'].get(),
            'max_concurrent': self.entity_vars['max_concurrent'].get(),
            'default_heading_variance': self.entity_vars['default_heading_variance'].get(),
            'patrol_behavior': self.entity_vars['patrol_behavior'].get()
        }

        self.load_entities_list()
        self.set_modified(True)
        self.update_status("Entity updated")

    def new_file(self):
        """Create new file"""
        if self.modified:
            if not messagebox.askyesno("New File", "Discard current changes?"):
                return

        self.data = self.get_default_data()
        self.current_file = None
        self.modified = False
        self.update_title()
        self.load_categories_list()
        self.load_entities_list()
        self.update_status("New file created")

    def open_file(self):
        """Open existing file"""
        if self.modified:
            if not messagebox.askyesno("Open File", "Discard current changes?"):
                return

        filename = filedialog.askopenfilename(
            title="Open Entity Definition File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    self.data = json.load(f)
                self.current_file = filename
                self.modified = False
                self.update_title()
                self.load_categories_list()
                self.load_entities_list()
                self.update_status(f"Opened: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def save_file(self):
        """Save current file"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        """Save file with new name"""
        filename = filedialog.asksaveasfilename(
            title="Save Entity Definition File",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            self.save_to_file(filename)
            self.current_file = filename

    def save_to_file(self, filename):
        """Save data to file"""
        try:
            # Update last modified
            self.data["metadata"]["lastModified"] = datetime.now().isoformat() + "Z"

            with open(filename, 'w') as f:
                json.dump(self.data, f, indent=2)

            self.modified = False
            self.update_title()
            self.update_status(f"Saved: {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def set_modified(self, value):
        """Set modified flag"""
        self.modified = value
        self.update_title()

    def update_title(self):
        """Update window title"""
        title = "Battlespace Entity Definition Editor"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.modified:
            title += " *"
        self.title(title)

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
        self.after(3000, lambda: self.status_bar.config(text="Ready"))

    def on_closing(self):
        """Handle window closing"""
        if self.modified:
            if not messagebox.askyesno("Exit", "You have unsaved changes. Exit anyway?"):
                return
        self.destroy()

if __name__ == "__main__":
    app = BattlespaceEditor()
    app.mainloop()
