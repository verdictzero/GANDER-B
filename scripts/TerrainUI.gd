class_name TerrainUI
extends Control

signal heightmap_selected(path: String)
signal test_heightmap_requested()
signal settings_changed(chunk_size: int, height_scale: float, chunks_per_side: int)

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