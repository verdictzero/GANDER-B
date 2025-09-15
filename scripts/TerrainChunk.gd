class_name TerrainChunk
extends MeshInstance3D

var chunk_size: int = 32
var vertex_spacing: float = 1.0
var heightmap_data: Image
var chunk_x: int = 0
var chunk_z: int = 0
var height_scale: float = 10.0

func initialize(x: int, z: int, size: int, spacing: float, heightmap: Image, scale: float) -> void:
	chunk_x = x
	chunk_z = z
	chunk_size = size
	vertex_spacing = spacing
	heightmap_data = heightmap
	height_scale = scale
	
	print("[TerrainChunk] Initializing chunk (", x, ",", z, ") with heightmap format: ", heightmap.get_format())
	
	generate_mesh()

func generate_mesh() -> void:
	var array_mesh = ArrayMesh.new()
	var arrays = []
	arrays.resize(Mesh.ARRAY_MAX)
	
	var vertices = PackedVector3Array()
	var uvs = PackedVector2Array()
	var normals = PackedVector3Array()
	var indices = PackedInt32Array()
	
	var world_offset_x = chunk_x * chunk_size * vertex_spacing
	var world_offset_z = chunk_z * chunk_size * vertex_spacing
	
	var min_height = 999999.0
	var max_height = -999999.0
	
	for z in range(chunk_size + 1):
		for x in range(chunk_size + 1):
			var world_x = world_offset_x + x * vertex_spacing
			var world_z = world_offset_z + z * vertex_spacing
			
			# Calculate heightmap coordinates based on chunk position and vertex
			var heightmap_x = chunk_x * chunk_size + x
			var heightmap_z = chunk_z * chunk_size + z
			
			var height = get_height_at_position(heightmap_x, heightmap_z)
			min_height = min(min_height, height)
			max_height = max(max_height, height)
			
			vertices.append(Vector3(x * vertex_spacing, height, z * vertex_spacing))
			
			# UV coordinates should map across the entire heightmap
			var u = float(heightmap_x) / float(heightmap_data.get_width() - 1)
			var v = float(heightmap_z) / float(heightmap_data.get_height() - 1)
			uvs.append(Vector2(u, v))
			
			normals.append(calculate_normal(heightmap_x, heightmap_z))
	
	for z in range(chunk_size):
		for x in range(chunk_size):
			var top_left = z * (chunk_size + 1) + x
			var top_right = top_left + 1
			var bottom_left = (z + 1) * (chunk_size + 1) + x
			var bottom_right = bottom_left + 1
			
			indices.append(top_left)
			indices.append(top_right)
			indices.append(bottom_left)
			
			indices.append(top_right)
			indices.append(bottom_right)
			indices.append(bottom_left)
	
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_INDEX] = indices
	
	array_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh = array_mesh
	
	print("[TerrainChunk] Chunk (", chunk_x, ",", chunk_z, ") height range: ", min_height, " to ", max_height)
	
	# If we got all zeros, there might be an issue with the sampling
	if max_height == 0.0 and min_height == 0.0:
		print("[TerrainChunk] WARNING: Chunk has no height variation - all zeros detected")
	
	var material = StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = false
	material.albedo_color = Color(0.3, 0.5, 0.2)
	material.cull_mode = BaseMaterial3D.CULL_DISABLED  # Show both sides
	set_surface_override_material(0, material)

func get_height_at_position(x: int, z: int) -> float:
	if not heightmap_data:
		return 0.0
	
	var heightmap_width = heightmap_data.get_width()
	var heightmap_height = heightmap_data.get_height()
	
	# Map the chunk coordinates to heightmap coordinates proportionally
	# This ensures we sample the entire heightmap regardless of chunk count
	var total_vertices_per_side = 8 * 64  # chunks_per_side * chunk_size = 512
	var sample_x = int(float(x) / float(total_vertices_per_side) * heightmap_width)
	var sample_z = int(float(z) / float(total_vertices_per_side) * heightmap_height)
	
	sample_x = clamp(sample_x, 0, heightmap_width - 1)
	sample_z = clamp(sample_z, 0, heightmap_height - 1)
	
	var pixel = heightmap_data.get_pixel(sample_x, sample_z)
	var height_value = pixel.r
	
	# Debug output for first chunk
	if chunk_x == 0 and chunk_z == 0 and x < 5 and z < 5:
		print("[TerrainChunk] Chunk(", chunk_x, ",", chunk_z, ") coord(", x, ",", z, ") -> heightmap(", sample_x, ",", sample_z, ") = ", height_value)
	
	return height_value * height_scale

func calculate_normal(x: int, z: int) -> Vector3:
	var left = get_height_at_position(x - 1, z)
	var right = get_height_at_position(x + 1, z)
	var down = get_height_at_position(x, z - 1)
	var up = get_height_at_position(x, z + 1)
	
	var normal = Vector3(right - left, 2.0 * vertex_spacing, up - down).normalized()
	return normal
