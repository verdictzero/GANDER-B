class_name TerrainUI
extends Control

signal heightmap_selected(path: String)
signal test_heightmap_requested()
signal settings_changed(chunk_size: int, height_scale: float, chunks_per_side: int)
signal top_down_view_requested()
signal perspective_view_requested()
signal wireframe_view_requested()
signal solid_view_requested()
signal bake_heightmap_requested()

@onready var file_dialog: FileDialog = $FileDialog
@onready var control_panel: Panel = $ControlPanel
@onready var load_button: Button = $ControlPanel/VBoxContainer/LoadButton
@onready var test_button: Button = $ControlPanel/VBoxContainer/TestButton
@onready var status_label: Label = $ControlPanel/VBoxContainer/StatusLabel
@onready var chunk_size_slider: HSlider = $ControlPanel/VBoxContainer/ChunkSizeContainer/ChunkSizeSlider
@onready var chunk_size_label: Label = $ControlPanel/VBoxContainer/ChunkSizeContainer/ChunkSizeLabel
@onready var height_scale_slider: HSlider = $ControlPanel/VBoxContainer/HeightScaleContainer/HeightScaleSlider
@onready var height_scale_label: Label = $ControlPanel/VBoxContainer/HeightScaleContainer/HeightScaleLabel
@onready var chunks_slider: HSlider = $ControlPanel/VBoxContainer/ChunksContainer/ChunksSlider
@onready var chunks_label: Label = $ControlPanel/VBoxContainer/ChunksContainer/ChunksLabel
@onready var heightmap_preview: TextureRect = $ControlPanel/VBoxContainer/HeightmapPreview
@onready var top_down_button: Button = $ControlPanel/VBoxContainer/ViewContainer/TopDownButton
@onready var perspective_button: Button = $ControlPanel/VBoxContainer/ViewContainer/PerspectiveButton
@onready var wireframe_button: Button = $ControlPanel/VBoxContainer/RenderContainer/WireframeButton
@onready var solid_button: Button = $ControlPanel/VBoxContainer/RenderContainer/SolidButton
@onready var bake_button: Button = $ControlPanel/VBoxContainer/BakeButton

func _ready() -> void:
	setup_ui()
	connect_signals()

func setup_ui() -> void:
	if not file_dialog:
		file_dialog = FileDialog.new()
		add_child(file_dialog)
	
	file_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	file_dialog.add_filter("*.png", "PNG Images")
	file_dialog.add_filter("*.jpg", "JPEG Images")
	file_dialog.add_filter("*.jpeg", "JPEG Images")
	file_dialog.add_filter("*.bmp", "BMP Images")
	file_dialog.add_filter("*.exr", "EXR Images")
	file_dialog.add_filter("*.tga", "TGA Images")
	file_dialog.size = Vector2(800, 600)
	file_dialog.position = Vector2(100, 100)
	
	if control_panel:
		control_panel.position = Vector2(10, 10)
		control_panel.size = Vector2(300, 400)
	
	if chunk_size_slider:
		chunk_size_slider.min_value = 8
		chunk_size_slider.max_value = 64
		chunk_size_slider.value = 32
		chunk_size_slider.step = 8
		update_chunk_size_label(32)
	
	if height_scale_slider:
		height_scale_slider.min_value = 1
		height_scale_slider.max_value = 50
		height_scale_slider.value = 10
		height_scale_slider.step = 1
		update_height_scale_label(10)
	
	if chunks_slider:
		chunks_slider.min_value = 1
		chunks_slider.max_value = 10
		chunks_slider.value = 4
		chunks_slider.step = 1
		update_chunks_label(4)
	
	update_status("Ready to load heightmap")

func connect_signals() -> void:
	if load_button:
		load_button.pressed.connect(_on_load_button_pressed)
	
	if test_button:
		test_button.pressed.connect(_on_test_button_pressed)
	
	if file_dialog:
		file_dialog.file_selected.connect(_on_file_selected)
	
	if chunk_size_slider:
		chunk_size_slider.value_changed.connect(_on_chunk_size_changed)
	
	if height_scale_slider:
		height_scale_slider.value_changed.connect(_on_height_scale_changed)
	
	if chunks_slider:
		chunks_slider.value_changed.connect(_on_chunks_changed)
	
	if top_down_button:
		top_down_button.pressed.connect(_on_top_down_button_pressed)
	
	if perspective_button:
		perspective_button.pressed.connect(_on_perspective_button_pressed)
	
	if wireframe_button:
		wireframe_button.pressed.connect(_on_wireframe_button_pressed)
	
	if solid_button:
		solid_button.pressed.connect(_on_solid_button_pressed)
	
	if bake_button:
		bake_button.pressed.connect(_on_bake_button_pressed)

func _on_load_button_pressed() -> void:
	file_dialog.popup()

func _on_test_button_pressed() -> void:
	test_heightmap_requested.emit()
	update_status("Generated test heightmap")

func _on_file_selected(path: String) -> void:
	heightmap_selected.emit(path)
	update_status("Loaded: " + path.get_file())

func _on_chunk_size_changed(value: float) -> void:
	var chunk_size = int(value)
	update_chunk_size_label(chunk_size)
	emit_settings_changed()

func _on_height_scale_changed(value: float) -> void:
	update_height_scale_label(value)
	emit_settings_changed()

func _on_chunks_changed(value: float) -> void:
	var chunks = int(value)
	update_chunks_label(chunks)
	emit_settings_changed()

func emit_settings_changed() -> void:
	if chunk_size_slider and height_scale_slider and chunks_slider:
		settings_changed.emit(
			int(chunk_size_slider.value),
			height_scale_slider.value,
			int(chunks_slider.value)
		)

func update_chunk_size_label(value: int) -> void:
	if chunk_size_label:
		chunk_size_label.text = str(value)

func update_height_scale_label(value: float) -> void:
	if height_scale_label:
		height_scale_label.text = str(value)

func update_chunks_label(value: int) -> void:
	if chunks_label:
		chunks_label.text = str(value) + "x" + str(value)

func update_status(message: String) -> void:
	if status_label:
		status_label.text = message

func _on_top_down_button_pressed() -> void:
	top_down_view_requested.emit()

func _on_perspective_button_pressed() -> void:
	perspective_view_requested.emit()

func _on_wireframe_button_pressed() -> void:
	wireframe_view_requested.emit()

func _on_solid_button_pressed() -> void:
	solid_view_requested.emit()

func _on_bake_button_pressed() -> void:
	bake_heightmap_requested.emit()
	update_status("Baking heightmap...")

func show_heightmap_preview(image: Image) -> void:
	if heightmap_preview and image:
		# Create a scaled down version for thumbnail
		var thumbnail_size = 256
		var preview_image = image.duplicate()
		
		# Scale the image to fit thumbnail while maintaining aspect ratio
		var original_size = preview_image.get_size()
		var scale_factor = min(float(thumbnail_size) / original_size.x, float(thumbnail_size) / original_size.y)
		var new_width = int(original_size.x * scale_factor)
		var new_height = int(original_size.y * scale_factor)
		
		preview_image.resize(new_width, new_height, Image.INTERPOLATE_LANCZOS)
		
		# Create texture from image
		var texture = ImageTexture.create_from_image(preview_image)
		heightmap_preview.texture = texture
		
		print("[TerrainUI] Updated heightmap preview: ", new_width, "x", new_height)