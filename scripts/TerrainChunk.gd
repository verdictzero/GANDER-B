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
	
	for z in range(chunk_size + 1):
		for x in range(chunk_size + 1):
			var world_x = world_offset_x + x * vertex_spacing
			var world_z = world_offset_z + z * vertex_spacing
			
			var height = get_height_at_position(chunk_x * chunk_size + x, chunk_z * chunk_size + z)
			
			vertices.append(Vector3(x * vertex_spacing, height, z * vertex_spacing))
			
			var u = float(chunk_x * chunk_size + x) / float(heightmap_data.get_width() - 1)
			var v = float(chunk_z * chunk_size + z) / float(heightmap_data.get_height() - 1)
			uvs.append(Vector2(u, v))
			
			normals.append(calculate_normal(chunk_x * chunk_size + x, chunk_z * chunk_size + z))
	
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
	
	var material = StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = false
	material.albedo_color = Color(0.3, 0.5, 0.2)
	set_surface_override_material(0, material)

func get_height_at_position(x: int, z: int) -> float:
	if not heightmap_data:
		return 0.0
	
	x = clamp(x, 0, heightmap_data.get_width() - 1)
	z = clamp(z, 0, heightmap_data.get_height() - 1)
	
	var pixel = heightmap_data.get_pixel(x, z)
	
	# Handle different pixel formats (EXR might have float values > 1.0)
	var height_value = pixel.r
	if heightmap_data.get_format() == Image.FORMAT_RF or heightmap_data.get_format() == Image.FORMAT_RGF:
		# For float formats, normalize if values are > 1.0
		height_value = clamp(height_value, 0.0, 1.0)
	
	return height_value * height_scale

func calculate_normal(x: int, z: int) -> Vector3:
	var left = get_height_at_position(x - 1, z)
	var right = get_height_at_position(x + 1, z)
	var down = get_height_at_position(x, z - 1)
	var up = get_height_at_position(x, z + 1)
	
	var normal = Vector3(right - left, 2.0 * vertex_spacing, up - down).normalized()
	return normal
