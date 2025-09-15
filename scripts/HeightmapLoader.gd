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
	
	var image = load_heightmap_from_path(file_path)
	if image and not validate_square_heightmap(image):
		return null
	
	return image

func validate_square_heightmap(image: Image) -> bool:
	var size = image.get_size()
	if size.x != size.y:
		var error_msg = "Heightmap must be square. Current size: " + str(size.x) + "x" + str(size.y)
		push_error("[HeightmapLoader] " + error_msg)
		loading_failed.emit(error_msg)
		return false
	
	print("[HeightmapLoader] Square heightmap validated: ", size.x, "x", size.y)
	return true

func is_supported_format(path: String) -> bool:
	var extension = path.get_extension().to_lower()
	return extension in supported_extensions

func process_heightmap(image: Image) -> void:
	print("[HeightmapLoader] Processing heightmap. Original format: ", image.get_format())
	print("[HeightmapLoader] Image size: ", image.get_size())
	
	# Sample a few pixels to see the actual values
	if image.get_size().x > 0 and image.get_size().y > 0:
		var center_pixel = image.get_pixel(image.get_width() / 2, image.get_height() / 2)
		var corner_pixel = image.get_pixel(0, 0)
		print("[HeightmapLoader] Center pixel value: ", center_pixel)
		print("[HeightmapLoader] Corner pixel value: ", corner_pixel)
	
	# Handle different image formats, especially EXR which uses float formats
	if image.get_format() == Image.FORMAT_RH or image.get_format() == Image.FORMAT_RGH or image.get_format() == Image.FORMAT_RGBH:
		print("[HeightmapLoader] Converting from half float format")
		image.convert(Image.FORMAT_RF)
	elif image.get_format() == Image.FORMAT_RF or image.get_format() == Image.FORMAT_RGF or image.get_format() == Image.FORMAT_RGBF:
		print("[HeightmapLoader] Already in float format, keeping as-is")
	elif image.get_format() != Image.FORMAT_RGB8:
		print("[HeightmapLoader] Converting to RGB8 format")
		image.convert(Image.FORMAT_RGB8)
	
	print("[HeightmapLoader] Final format: ", image.get_format())
	
	# Sample again after conversion
	if image.get_size().x > 0 and image.get_size().y > 0:
		var center_pixel_after = image.get_pixel(image.get_width() / 2, image.get_height() / 2)
		print("[HeightmapLoader] Center pixel after conversion: ", center_pixel_after)

func create_test_heightmap(width: int, height: int) -> Image:
	# Create a larger, more interesting test heightmap
	var size = 512  # Fixed size for better terrain coverage
	var image = Image.create(size, size, false, Image.FORMAT_RGB8)
	
	print("[HeightmapLoader] Creating test heightmap: ", size, "x", size)
	
	for y in range(size):
		for x in range(size):
			# Create multiple layers of noise/patterns for interesting terrain
			var base_value = sin(x * 0.02) * cos(y * 0.02) * 0.3 + 0.3
			var detail_value = sin(x * 0.1) * sin(y * 0.1) * 0.2
			var noise_value = randf() * 0.1
			
			# Add some hills/mountains
			var center_x = size * 0.5
			var center_y = size * 0.5
			var distance_from_center = sqrt((x - center_x) * (x - center_x) + (y - center_y) * (y - center_y))
			var mountain_value = max(0, 0.5 - (distance_from_center / size) * 1.5)
			
			# Combine all values
			var final_value = base_value + detail_value + noise_value + mountain_value
			final_value = clamp(final_value, 0.0, 1.0)
			
			image.set_pixel(x, y, Color(final_value, final_value, final_value))
	
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
