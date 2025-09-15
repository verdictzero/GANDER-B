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
var is_orthographic: bool = false
var is_wireframe: bool = false

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
		ui.top_down_view_requested.connect(_on_top_down_view_requested)
		ui.perspective_view_requested.connect(_on_perspective_view_requested)
		ui.wireframe_view_requested.connect(_on_wireframe_view_requested)
		ui.solid_view_requested.connect(_on_solid_view_requested)
		ui.bake_heightmap_requested.connect(_on_bake_heightmap_requested)
		ui.project_image_requested.connect(_on_project_image_requested)
	
	if heightmap_loader:
		heightmap_loader.heightmap_loaded.connect(_on_heightmap_loaded)
		heightmap_loader.loading_failed.connect(_on_loading_failed)

func _on_heightmap_selected(path: String) -> void:
	print("[MainController] User selected heightmap: ", path)
	log_activity("Loading heightmap: " + path.get_file())
	var result = heightmap_loader.load_heightmap_from_file_dialog(path)
	if not result:
		push_error("[MainController] Failed to load heightmap")
		log_activity("❌ Failed to load heightmap")

func _on_test_heightmap_requested() -> void:
	print("[MainController] Generating test heightmap...")
	log_activity("Generating test heightmap...")
	var test_image = heightmap_loader.create_test_heightmap(128, 128)
	if test_image:
		terrain_manager.load_heightmap_from_image(test_image)
		log_activity("✅ Test heightmap generated successfully")
	else:
		push_error("[MainController] Failed to create test heightmap")
		log_activity("❌ Failed to create test heightmap")

func _on_heightmap_loaded(image: Image) -> void:
	print("[MainController] Heightmap loaded signal received")
	if image:
		log_activity("✅ Heightmap loaded: " + str(image.get_size()))
		# Show thumbnail in UI
		if ui:
			ui.show_heightmap_preview(image)
		
		terrain_manager.load_heightmap_from_image(image)
		log_activity("🌄 Terrain generated successfully")
	else:
		push_error("[MainController] Received null image in heightmap_loaded signal")
		log_activity("❌ Failed to load heightmap image")
	
	print("[MainController] Terrain loaded - positioning camera for centered 512x512 terrain")
	
	# Terrain is now always centered at (0,0,0) and extends 512 units in each direction
	# Position camera to see the centered terrain
	var camera_x = 200  # Offset from center
	var camera_z = 200  # Offset from center  
	var camera_y = 100  # Height to see terrain
	
	camera_controller.position = Vector3(camera_x, camera_y, camera_z)
	# Look at terrain center (always at origin)
	var look_target = Vector3(0, 0, 0)
	camera_controller.look_at(look_target, Vector3.UP)
	
	print("[MainController] Positioned camera at: ", camera_controller.position)
	print("[MainController] Looking at terrain center: ", look_target)

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
	
	# Debug: Press T to teleport camera to terrain center
	if Input.is_action_just_pressed("ui_accept") or Input.is_key_pressed(KEY_T):
		teleport_to_terrain()

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

func teleport_to_terrain():
	if terrain_manager and terrain_manager.terrain_chunks.size() > 0:
		# Find a chunk with height variation
		var best_chunk = null
		var best_height_range = 0.0
		
		for chunk in terrain_manager.terrain_chunks:
			# This is a simple heuristic - we could add a height_range property to chunks
			# For now, just use any chunk that's not at origin
			if chunk.chunk_x > 0 or chunk.chunk_z > 0:
				best_chunk = chunk
				break
		
		if not best_chunk:
			best_chunk = terrain_manager.terrain_chunks[0]  # Fallback to first chunk
		
		# Position camera above the selected chunk
		var chunk_world_pos = best_chunk.position
		camera_controller.position = Vector3(
			chunk_world_pos.x + 16,  # Center of chunk + offset
			25,  # Height above terrain
			chunk_world_pos.z + 50   # Behind the chunk to look at it
		)
		camera_controller.look_at(Vector3(chunk_world_pos.x + 16, 0, chunk_world_pos.z + 16), Vector3.UP)
		
		print("[MainController] Teleported to terrain chunk at: ", chunk_world_pos)
		print("[MainController] Camera position: ", camera_controller.position)

func _on_top_down_view_requested() -> void:
	if not camera_3d:
		return
	
	# Switch to orthographic projection
	camera_3d.projection = Camera3D.PROJECTION_ORTHOGONAL
	is_orthographic = true
	
	# Position camera above terrain center (origin) looking down
	var camera_height = 400.0  # High enough to see all 512x512 terrain
	
	camera_controller.position = Vector3(0, camera_height, 0)
	camera_controller.rotation = Vector3(deg_to_rad(-90), 0, 0)  # Look straight down
	camera_rotation = Vector2.ZERO
	
	# Set orthographic size to fit 512x512 terrain with some padding
	camera_3d.size = 600.0
	
	log_activity("📷 Switched to orthographic top-down view")
	print("[MainController] Switched to orthographic top-down view")
	print("[MainController] Camera height: ", camera_height, " Size: ", camera_3d.size)

func _on_perspective_view_requested() -> void:
	if not camera_3d:
		return
	
	# Switch back to perspective projection
	camera_3d.projection = Camera3D.PROJECTION_PERSPECTIVE
	is_orthographic = false
	
	# Reset to perspective view position - terrain centered at origin
	camera_controller.position = Vector3(200, 100, 200)
	camera_controller.look_at(Vector3(0, 0, 0), Vector3.UP)
	
	camera_rotation = Vector2.ZERO
	
	log_activity("📷 Switched to perspective view")
	print("[MainController] Switched to perspective view")

func _on_wireframe_view_requested() -> void:
	is_wireframe = true
	apply_wireframe_to_terrain()
	log_activity("🔲 Switched to wireframe view")
	print("[MainController] Switched to wireframe view")

func _on_solid_view_requested() -> void:
	is_wireframe = false
	apply_wireframe_to_terrain()
	log_activity("🟩 Switched to solid view")
	print("[MainController] Switched to solid view")

func apply_wireframe_to_terrain() -> void:
	if not terrain_manager:
		return
	
	for chunk in terrain_manager.terrain_chunks:
		if chunk and chunk.get_surface_override_material_count() > 0:
			var material = chunk.get_surface_override_material(0) as StandardMaterial3D
			if material:
				if is_wireframe:
					material.flags_use_point_size = true
					material.flags_wireframe = true
					material.albedo_color = Color.WHITE
				else:
					material.flags_wireframe = false
					material.albedo_color = Color(0.3, 0.5, 0.2)

func _on_bake_heightmap_requested() -> void:
	if not terrain_manager or not camera_3d:
		push_error("[MainController] Cannot bake - terrain or camera not ready")
		return
	
	print("[MainController] Starting heightmap bake...")
	
	# Switch to top-down orthographic view for baking
	var was_ortho = is_orthographic
	if not is_orthographic:
		_on_top_down_view_requested()
	
	# Wait a frame for camera to update, then capture
	await get_tree().process_frame
	
	# Create viewport for baking
	var bake_size = 1024
	var viewport = SubViewport.new()
	viewport.size = Vector2i(bake_size, bake_size)
	viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	
	# Create camera for baking
	var bake_camera = Camera3D.new()
	bake_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	
	# Position camera same as current top-down view - terrain centered at origin
	bake_camera.position = Vector3(0, 400, 0)
	bake_camera.rotation = Vector3(deg_to_rad(-90), 0, 0)
	bake_camera.size = 600.0
	
	# Add viewport and camera to scene temporarily
	add_child(viewport)
	viewport.add_child(bake_camera)
	
	# Copy terrain to viewport (simplified - just render the same terrain)
	# In a more complex setup, you'd clone the terrain nodes
	
	# Render and capture
	viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	await get_tree().process_frame
	await get_tree().process_frame
	
	# Get the rendered image
	var image = viewport.get_texture().get_image()
	
	# Save the baked heightmap
	var timestamp = Time.get_unix_time_from_system()
	var filename = "baked_heightmap_" + str(timestamp) + ".png"
	var save_path = "user://" + filename
	
	var error = image.save_png(save_path)
	
	# Cleanup
	viewport.queue_free()
	
	if error == OK:
		print("[MainController] Heightmap baked successfully: ", save_path)
		if ui:
			ui.update_status("Heightmap baked: " + filename)
	else:
		push_error("[MainController] Failed to save baked heightmap")
		if ui:
			ui.update_status("Baking failed")
	
	# Restore previous camera state if needed
	if not was_ortho:
		_on_perspective_view_requested()

func _on_project_image_requested(image_path: String) -> void:
	if not terrain_manager or not camera_3d:
		push_error("[MainController] Cannot project image - terrain or camera not ready")
		log_activity("❌ Cannot project image - terrain not ready")
		return
	
	log_activity("Loading projection image: " + image_path.get_file())
	
	# Load the image to project
	var projection_image = Image.new()
	var error = projection_image.load(image_path)
	
	if error != OK:
		push_error("[MainController] Failed to load projection image: " + image_path)
		log_activity("❌ Failed to load projection image")
		return
	
	# Validate 1:1 aspect ratio
	var image_size = projection_image.get_size()
	if image_size.x != image_size.y:
		push_error("[MainController] Image must have 1:1 aspect ratio (square). Current: " + str(image_size.x) + "x" + str(image_size.y))
		log_activity("❌ Image must be square (1:1 aspect ratio). Current: " + str(image_size.x) + "x" + str(image_size.y))
		if ui:
			ui.update_status("Error: Image must be square (1:1 aspect ratio)")
		return
	
	log_activity("✅ Square image loaded (" + str(image_size.x) + "x" + str(image_size.y) + "), starting projection...")
	
	# Switch to top-down orthographic view for projection
	var was_ortho = is_orthographic
	if not is_orthographic:
		_on_top_down_view_requested()
		log_activity("📷 Switched to orthographic view")
	
	await get_tree().process_frame
	
	log_activity("🎨 Applying image projection to terrain...")
	
	# Apply the image to all terrain chunks
	# Since the UV coordinates in TerrainChunk already map properly to the full terrain,
	# we can use the same material for all chunks
	var projection_material = StandardMaterial3D.new()
	var image_texture = ImageTexture.create_from_image(projection_image)
	projection_material.albedo_texture = image_texture
	projection_material.flags_transparent = false
	projection_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	
	# Apply to all chunks - the UV coordinates should already be correctly mapped
	for chunk in terrain_manager.terrain_chunks:
		if chunk:
			chunk.set_surface_override_material(0, projection_material)
	
	log_activity("✅ Image projected onto terrain successfully")
	
	# Update UI status
	if ui:
		ui.update_status("Image projected: " + image_path.get_file())
	
	# Restore previous camera state if needed
	if not was_ortho:
		await get_tree().create_timer(2.0).timeout  # Give user time to see result
		_on_perspective_view_requested()
		log_activity("📷 Returned to perspective view")

func log_activity(message: String) -> void:
	if ui:
		ui.log_activity(message)
