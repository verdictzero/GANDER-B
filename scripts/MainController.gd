extends Node3D

@export var camera_move_speed: float = 10.0
@export var camera_rotate_speed: float = 2.0
@export var camera_zoom_speed: float = 20.0

@onready var terrain_manager = $TerrainManager
@onready var heightmap_loader = $HeightmapLoader
var ui = null  # Will be created in _ready
@onready var camera_3d: Camera3D = $CameraController/Camera3D
@onready var camera_controller: Node3D = $CameraController
@onready var directional_light: DirectionalLight3D = $DirectionalLight3D

var camera_rotation: Vector2 = Vector2.ZERO
var mouse_captured: bool = false

func _ready() -> void:
	setup_scene()
	connect_signals()
	
	if heightmap_loader and heightmap_loader.has_method("create_test_heightmap"):
		heightmap_loader.create_test_heightmap(128, 128)
	else:
		push_error("[MainController] HeightmapLoader not ready")

func setup_scene() -> void:
	if not terrain_manager or not terrain_manager.has_method("load_heightmap_from_image"):
		var tm_script = load("res://scripts/TerrainManager.gd")
		terrain_manager.set_script(tm_script)
	
	if not heightmap_loader or not heightmap_loader.has_method("create_test_heightmap"):
		var hl_script = load("res://scripts/HeightmapLoader.gd")
		heightmap_loader.set_script(hl_script)
	
	# Try to find existing UI node first
	ui = get_node_or_null("UI")
	
	if not ui:
		print("[MainController] Creating UI...")
		var ui_scene = load("res://scenes/TerrainUI.tscn")
		if ui_scene:
			ui = ui_scene.instantiate()
			ui.name = "UI"
			add_child(ui)
			print("[MainController] UI created successfully")
		else:
			push_error("[MainController] Failed to load TerrainUI.tscn - UI will be unavailable")
	
	if not camera_controller:
		camera_controller = Node3D.new()
		camera_controller.name = "CameraController"
		add_child(camera_controller)
		camera_controller.position = Vector3(50, 30, 50)
		camera_controller.rotation.x = deg_to_rad(-30)
	
	if not camera_3d:
		camera_3d = Camera3D.new()
		camera_3d.name = "Camera3D"
		camera_controller.add_child(camera_3d)
		camera_3d.fov = 60
		camera_3d.near = 0.1
		camera_3d.far = 1000
	
	if not directional_light:
		directional_light = DirectionalLight3D.new()
		directional_light.name = "DirectionalLight3D"
		add_child(directional_light)
		directional_light.rotation = Vector3(deg_to_rad(-45), deg_to_rad(-45), 0)
		directional_light.light_energy = 1.0
		directional_light.shadow_enabled = true

func connect_signals() -> void:
	if ui:
		ui.heightmap_selected.connect(_on_heightmap_selected)
		ui.test_heightmap_requested.connect(_on_test_heightmap_requested)
		ui.settings_changed.connect(_on_settings_changed)
	
	if heightmap_loader:
		heightmap_loader.heightmap_loaded.connect(_on_heightmap_loaded)
		heightmap_loader.loading_failed.connect(_on_loading_failed)

func _on_heightmap_selected(path: String) -> void:
	print("[MainController] User selected heightmap: ", path)
	var result = heightmap_loader.load_heightmap_from_file_dialog(path)
	if not result:
		push_error("[MainController] Failed to load heightmap")

func _on_test_heightmap_requested() -> void:
	print("[MainController] Generating test heightmap...")
	var test_image = heightmap_loader.create_test_heightmap(128, 128)
	if test_image:
		terrain_manager.load_heightmap_from_image(test_image)
	else:
		push_error("[MainController] Failed to create test heightmap")

func _on_heightmap_loaded(image: Image) -> void:
	print("[MainController] Heightmap loaded signal received")
	if image:
		terrain_manager.load_heightmap_from_image(image)
	else:
		push_error("[MainController] Received null image in heightmap_loaded signal")
	
	var terrain_size = terrain_manager.get_terrain_size()
	camera_controller.position = Vector3(
		terrain_size.x * 0.5,
		30,
		terrain_size.y * 0.5 + terrain_size.y * 0.3
	)

func _on_loading_failed(error_message: String) -> void:
	push_error(error_message)
	if ui:
		ui.update_status("Error: " + error_message)

func _on_settings_changed(chunk_size: int, height_scale: float, chunks_per_side: int) -> void:
	if terrain_manager:
		terrain_manager.chunk_size = chunk_size
		terrain_manager.height_scale = height_scale
		terrain_manager.chunks_per_side = chunks_per_side
		
		if terrain_manager.heightmap_image:
			terrain_manager.generate_terrain()

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			mouse_captured = event.pressed
			if mouse_captured:
				Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			else:
				Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	
	elif event is InputEventMouseMotion and mouse_captured:
		camera_rotation.x -= event.relative.x * camera_rotate_speed * 0.01
		camera_rotation.y -= event.relative.y * camera_rotate_speed * 0.01
		camera_rotation.y = clamp(camera_rotation.y, -1.4, 1.4)
		
		camera_controller.rotation.y = camera_rotation.x
		camera_controller.rotation.x = camera_rotation.y

func _process(delta: float) -> void:
	handle_camera_movement(delta)

func handle_camera_movement(delta: float) -> void:
	if not camera_controller:
		return
	
	var input_vector = Vector3.ZERO
	
	if Input.is_action_pressed("ui_up"):
		input_vector.z -= 1
	if Input.is_action_pressed("ui_down"):
		input_vector.z += 1
	if Input.is_action_pressed("ui_left"):
		input_vector.x -= 1
	if Input.is_action_pressed("ui_right"):
		input_vector.x += 1
	if Input.is_key_pressed(KEY_Q):
		input_vector.y -= 1
	if Input.is_key_pressed(KEY_E):
		input_vector.y += 1
	
	if input_vector.length() > 0:
		input_vector = input_vector.normalized()
		var movement = camera_controller.transform.basis * input_vector
		movement.y = input_vector.y
		
		var speed = camera_move_speed
		if Input.is_key_pressed(KEY_SHIFT):
			speed *= 2.0
		
		camera_controller.position += movement * speed * delta
