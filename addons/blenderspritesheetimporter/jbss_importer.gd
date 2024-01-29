@tool
extends EditorImportPlugin

enum Presets { DEFAULT }

# Turn this to true in case you want details about the import process
var verbose : bool = false

func _get_importer_name():
	return "OddMode.blenderspritesheet"
	
func _get_visible_name():
	return "Blender Sprite Sheet"
	
func _get_recognized_extensions():
	return ["jbss"]
	
func _get_save_extension():
	return "tres"
	
func _get_resource_type():
	return "SpriteFrames"

func _get_preset_count():
	return Presets.size()

func _get_priority():
	return 1.0

func _get_import_order():
	return 1.0

func _get_preset_name(preset_index):
	match preset_index:
		Presets.DEFAULT:
			return "Default"
		_:
			return "Unknown"
			
func _get_import_options(path, preset_index):
	return []			

func _get_option_visibility(path, option_name, options):
	return false

func debug_print(str):
	if verbose:
		print(str)

func import_animation_frames(animation_path : String, animation_name : String, animation : SpriteFrames, subfolder_data : Variant):
	
	var frames : Array = []
	var frames_normal : Array = []
	var dir = DirAccess.open(animation_path)
	
	if dir:
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if not dir.current_is_dir():
				if not file_name.contains(".import"):
					if file_name.contains("normal"):
						frames_normal.append(file_name)
					else:
						frames.append(file_name)
			
			file_name = dir.get_next()
				
	if frames.size() > 0:
		frames.sort()
		animation.add_animation(animation_name)
		animation.set_animation_speed(animation_name, subfolder_data[animation_name]["fps"])
		animation.set_animation_loop(animation_name, subfolder_data[animation_name]["loop"])
		
		for frame_file in frames:
			debug_print("Adding frame: " + animation_path + "/" + frame_file)
			animation.add_frame(animation_name, load(animation_path + "/" + frame_file))

	if frames_normal.size() > 0:
		frames_normal.sort()
		animation_name += "_normal"
		animation.add_animation(animation_name)
		animation.set_animation_speed(animation_name, subfolder_data[animation_name]["fps"])
		animation.set_animation_loop(animation_name, subfolder_data[animation_name]["loop"])
		
		for frame_file in frames_normal:
			debug_print("Adding frame: " + animation_path + "/" + frame_file)
			animation.add_frame(animation_name, load(animation_path + "/" + frame_file))
	
func import_folder(path : String, animation_name : String, animation : SpriteFrames, subfolder_data : Variant):
	var animation_folder = path + "/" + animation_name
	var dir = DirAccess.open(animation_folder)
	if dir:
		dir.list_dir_begin()
		var file_name = dir.get_next()
		while file_name != "":
			if dir.current_is_dir():
				debug_print("Processing animation: " + animation_name + "_" + file_name)
				import_animation_frames(animation_folder + "/" + file_name, animation_name + "_" + file_name, animation, subfolder_data)
			else:
				debug_print("Ignoring file: " + file_name)
			
			file_name = dir.get_next()
			
	else:
		push_error("An error occurred when trying to access " + animation_folder)


func _import(source_file, save_path, options, r_platform_variants, r_gen_files):
	
	var file = FileAccess.open(source_file, FileAccess.READ)
	if file == null:
		return FileAccess.get_open_error()
	file.close()

	var json = JSON.new()
	var error = json.parse(file.get_file_as_string(source_file))
	if error != OK:
		push_error("JSON Parse Error: ", json.get_error_message(), " in ", source_file, " at line ", json.get_error_line())
		return ERR_PARSE_ERROR
	
	var data_received = json.data


	var output : SpriteFrames = SpriteFrames.new()
	output.remove_animation("default")
	
	var subfolders = data_received.keys()
	if subfolders.size() == 0:
		# Empty file?
		return ERR_PARSE_ERROR
	
	var import_root = file.get_path().get_base_dir()
	for i in subfolders:
		import_folder(import_root, i, output, data_received[i])

	return ResourceSaver.save(output, "%s.%s" % [save_path, _get_save_extension()])
