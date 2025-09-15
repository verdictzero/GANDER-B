class_name TerrainManager
extends Node3D

@export var chunk_size: int = 64
@export var vertex_spacing: float = 1.0
@export var height_scale: float = 10.0
@export var chunks_per_side: int = 8  # 8x8 chunks of 64x64 units = 512x512 total

# Fixed terrain dimensions - always 512x512 units centered at origin
const TERRAIN_SIZE: float = 512.0

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
	print("[TerrainManager] Clearing existing terrain...")
	for chunk in terrain_chunks:
		if chunk:
			chunk.queue_free()
	terrain_chunks.clear()
	
	# Also remove any orphaned chunk nodes
	for child in get_children():
		if child is TerrainChunk:
			child.queue_free()
	
	print("[TerrainManager] Terrain cleared")

func generate_terrain() -> void:
	if not heightmap_image:
		push_error("[TerrainManager] No heightmap loaded")
		return
	
	print("[TerrainManager] Generating terrain...")
	print("  Heightmap size: ", heightmap_image.get_size())
	print("  Fixed terrain size: ", TERRAIN_SIZE, "x", TERRAIN_SIZE, " units")
	print("  Chunk size: ", chunk_size)
	print("  Chunks per side: ", chunks_per_side)
	
	# Calculate vertex spacing to fit exactly in 512x512 area
	# With 8x8 chunks of 64 vertices each, we get vertex_spacing = 1.0
	vertex_spacing = TERRAIN_SIZE / (chunks_per_side * chunk_size)
	
	print("  Calculated vertex spacing: ", vertex_spacing)
	print("  Creating ", chunks_per_side, "x", chunks_per_side, " chunks")
	
	# Calculate offset to center terrain at origin
	var terrain_offset = -TERRAIN_SIZE * 0.5
	
	for z in range(chunks_per_side):
		for x in range(chunks_per_side):
			var chunk = TerrainChunk.new()
			add_child(chunk)
			
			chunk.initialize(x, z, chunk_size, vertex_spacing, heightmap_image, height_scale)
			
			# Position chunks centered at origin
			var chunk_world_x = terrain_offset + (x * chunk_size * vertex_spacing)
			var chunk_world_z = terrain_offset + (z * chunk_size * vertex_spacing)
			chunk.position = Vector3(chunk_world_x, 0, chunk_world_z)
			
			if x < 3 and z < 3:  # Only print first few for brevity
				print("  Chunk (", x, ",", z, ") positioned at: ", chunk.position)
			
			terrain_chunks.append(chunk)
	
	print("[TerrainManager] Terrain generation complete. Created ", terrain_chunks.size(), " chunks")
	print("[TerrainManager] Terrain bounds: ", terrain_offset, " to ", -terrain_offset, " (centered at origin)")

func get_terrain_size() -> Vector2:
	# Always return fixed terrain size
	return Vector2(TERRAIN_SIZE, TERRAIN_SIZE)

func get_height_at_world_position(world_pos: Vector3) -> float:
	if not heightmap_image:
		return 0.0
	
	var x = int(world_pos.x / vertex_spacing)
	var z = int(world_pos.z / vertex_spacing)
	
	x = clamp(x, 0, heightmap_image.get_width() - 1)
	z = clamp(z, 0, heightmap_image.get_height() - 1)
	
	var pixel = heightmap_image.get_pixel(x, z)
	return pixel.r * height_scale