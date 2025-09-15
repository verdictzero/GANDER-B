class_name TerrainManager
extends Node3D

@export var chunk_size: int = 32
@export var vertex_spacing: float = 1.0
@export var height_scale: float = 10.0
@export var chunks_per_side: int = 4

var heightmap_image: Image
var terrain_chunks: Array[TerrainChunk] = []
var chunk_scene = preload("res://scripts/TerrainChunk.gd")

func load_heightmap(path: String) -> bool:
	heightmap_image = Image.new()
	var error = heightmap_image.load(path)
	
	if error != OK:
		push_error("Failed to load heightmap: " + path)
		return false
	
	clear_terrain()
	generate_terrain()
	return true

func load_heightmap_from_image(image: Image) -> void:
	print("[TerrainManager] Loading heightmap from image. Size: ", image.get_size())
	heightmap_image = image
	clear_terrain()
	generate_terrain()

func clear_terrain() -> void:
	for chunk in terrain_chunks:
		if chunk:
			chunk.queue_free()
	terrain_chunks.clear()

func generate_terrain() -> void:
	if not heightmap_image:
		push_error("[TerrainManager] No heightmap loaded")
		return
	
	print("[TerrainManager] Generating terrain...")
	print("  Heightmap size: ", heightmap_image.get_size())
	print("  Chunk size: ", chunk_size)
	print("  Chunks per side: ", chunks_per_side)
	
	var total_chunks_x = ceili(float(heightmap_image.get_width()) / float(chunk_size))
	var total_chunks_z = ceili(float(heightmap_image.get_height()) / float(chunk_size))
	
	total_chunks_x = min(total_chunks_x, chunks_per_side)
	total_chunks_z = min(total_chunks_z, chunks_per_side)
	
	print("  Creating ", total_chunks_x, "x", total_chunks_z, " chunks")
	
	for z in range(total_chunks_z):
		for x in range(total_chunks_x):
			var chunk = TerrainChunk.new()
			add_child(chunk)
			
			chunk.initialize(x, z, chunk_size, vertex_spacing, heightmap_image, height_scale)
			chunk.position = Vector3(
				x * chunk_size * vertex_spacing,
				0,
				z * chunk_size * vertex_spacing
			)
			
			terrain_chunks.append(chunk)
	
	print("[TerrainManager] Terrain generation complete. Created ", terrain_chunks.size(), " chunks")

func get_terrain_size() -> Vector2:
	if not heightmap_image:
		return Vector2.ZERO
	
	return Vector2(
		heightmap_image.get_width() * vertex_spacing,
		heightmap_image.get_height() * vertex_spacing
	)

func get_height_at_world_position(world_pos: Vector3) -> float:
	if not heightmap_image:
		return 0.0
	
	var x = int(world_pos.x / vertex_spacing)
	var z = int(world_pos.z / vertex_spacing)
	
	x = clamp(x, 0, heightmap_image.get_width() - 1)
	z = clamp(z, 0, heightmap_image.get_height() - 1)
	
	var pixel = heightmap_image.get_pixel(x, z)
	return pixel.r * height_scale