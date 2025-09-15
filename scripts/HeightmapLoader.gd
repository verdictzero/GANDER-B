class_name HeightmapLoader
extends Node

signal heightmap_loaded(image: Image)
signal loading_failed(error_message: String)

var supported_extensions: Array[String] = ["png", "jpg", "jpeg", "bmp", "exr", "tga"]

func load_heightmap_from_path(path: String) -> Image:
	print("[HeightmapLoader] Attempting to load: ", path)
	var image = Image.new()
	var error = image.load(path)
	
	if error != OK:
		var error_msg = "Failed to load image from path: " + path + " (Error code: " + str(error) + ")"
		push_error("[HeightmapLoader] " + error_msg)
		loading_failed.emit(error_msg)
		return null
	
	print("[HeightmapLoader] Image loaded successfully. Size: ", image.get_size(), " Format: ", image.get_format())
	process_heightmap(image)
	heightmap_loaded.emit(image)
	return image

func load_heightmap_from_file_dialog(file_path: String) -> Image:
	if not is_supported_format(file_path):
		loading_failed.emit("Unsupported file format. Supported formats: " + ", ".join(supported_extensions))
		return null
	
	return load_heightmap_from_path(file_path)

func is_supported_format(path: String) -> bool:
	var extension = path.get_extension().to_lower()
	return extension in supported_extensions

func process_heightmap(image: Image) -> void:
	print("[HeightmapLoader] Processing heightmap. Original format: ", image.get_format())
	
	# Handle different image formats, especially EXR which uses float formats
	if image.get_format() == Image.FORMAT_RH or image.get_format() == Image.FORMAT_RGH or image.get_format() == Image.FORMAT_RGBH:
		print("[HeightmapLoader] Converting from half float format")
		image.convert(Image.FORMAT_RF)
	elif image.get_format() != Image.FORMAT_RF and image.get_format() != Image.FORMAT_RGB8:
		print("[HeightmapLoader] Converting to RGB8 format")
		image.convert(Image.FORMAT_RGB8)
	
	print("[HeightmapLoader] Final format: ", image.get_format())

func create_test_heightmap(width: int, height: int) -> Image:
	var image = Image.create(width, height, false, Image.FORMAT_RGB8)
	
	for y in range(height):
		for x in range(width):
			var value = sin(x * 0.1) * 0.5 + 0.5
			value *= sin(y * 0.1) * 0.5 + 0.5
			
			var noise_value = randf() * 0.1
			value = clamp(value + noise_value, 0.0, 1.0)
			
			image.set_pixel(x, y, Color(value, value, value))
	
	heightmap_loaded.emit(image)
	return image

func create_flat_heightmap(width: int, height: int, height_value: float = 0.5) -> Image:
	var image = Image.create(width, height, false, Image.FORMAT_RGB8)
	var color = Color(height_value, height_value, height_value)
	
	for y in range(height):
		for x in range(width):
			image.set_pixel(x, y, color)
	
	heightmap_loaded.emit(image)
	return image
