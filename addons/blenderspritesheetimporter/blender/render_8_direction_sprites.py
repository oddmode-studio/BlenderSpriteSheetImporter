import bpy
import os
import math
import json

######################################################################################
# Script parameters, change to suit your needs before running
# PLEASE NOTE: remember to select the model in the Outliner before running the script!

OUTPUT_FOLDER = '/home/massimiliano/projects/godot/tss/assets/images/monk'

# Values used by Godot when importing:
DEFAULT_LOOP = True # if True, all animations will be marked as Looping in Godot
DEFAULT_FPS = 20    # this will be the animation speed applied to animations 

# Dimension of each rendered frame (height and width)
OUTPUT_W = 128
OUTPUT_H = 128

# Choose the directions to render
RENDERED_DIRECTIONS = [ "N", "NE", "E", "SE", "S", "SW", "W", "NW" ] 

# Choose the animations to render - these names should match NLA tracks
RENDERED_ANIMATIONS = [ "idle", "walk" ]

# Choose how many frames to skip per animation: 1 to render every frame
RENDER_EVERY_X_FRAMES = 3

# In case we're skipping frames and last frame would not be exported,
# setting this to True will force rendering the last frame. This can
# be useful to smooth looping animations
FORCE_RENDER_LAST_FRAME = False

# Create normal textures?
PROCESS_NORMALS = True
######################################################################################


def render_image(i, counter, animation_folder, normal_file_output):

    s=bpy.context.scene
    s.frame_current = i

    render_file_path = (
                        animation_folder
                        + "/"
                        + str(counter).zfill(3)
                        )
    
    s.render.filepath = render_file_path
    
    if PROCESS_NORMALS:
        normal_file_output.base_path = animation_folder + "/"
        normal_file_output.file_slots[0].path = ("normal_" 
                            + str(counter).zfill(3) + "_###")

    bpy.ops.render.render( #{'dict': "override"},
                          #'INVOKE_DEFAULT',  
                          False,            # undo support
                          animation=False, 
                          write_still=True
                         )    
    
def render8directions_selected_objects(path):
    # path fixing
    path = os.path.abspath(path)

    # get list of selected objects
    selected_list = bpy.context.selected_objects

    # deselect all in scene
    bpy.ops.object.select_all(action='TOGGLE')

    s=bpy.context.scene

    s.render.resolution_x = OUTPUT_W 
    s.render.resolution_y = OUTPUT_H

    # I left this in as in some of my models, I needed to translate the "root" object but
    # the animations were on the armature which I selected.
    # 
    # obRoot = bpy.context.scene.objects["root"]

    s.use_nodes = True
    s.view_layers["ViewLayer"].use_pass_normal = True
    s.view_layers["ViewLayer"].use_pass_diffuse_color = True

    nodes = bpy.context.scene.node_tree.nodes
    links = bpy.context.scene.node_tree.links

    # Clear default nodes
    for n in nodes:
        nodes.remove(n)

    # Create input render layer node
    render_layers = nodes.new('CompositorNodeRLayers')
    normal_file_output = None

    if PROCESS_NORMALS:
        # generation of normals output

        # Create normal output nodes
        scale_node = nodes.new(type="CompositorNodeMixRGB")
        scale_node.blend_type = 'MULTIPLY'
        # scale_node.use_alpha = True
        scale_node.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
        links.new(render_layers.outputs['Normal'], scale_node.inputs[1])

        bias_node = nodes.new(type="CompositorNodeMixRGB")
        bias_node.blend_type = 'ADD'
        # bias_node.use_alpha = True
        bias_node.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
        links.new(scale_node.outputs[0], bias_node.inputs[1])

        normal_file_output = nodes.new(type="CompositorNodeOutputFile")
        normal_file_output.label = 'Normal Output'
        normal_file_output.file_slots[0].use_node_format = True
        normal_file_output.format.file_format = "JPEG"
        links.new(bias_node.outputs[0], normal_file_output.inputs[0])

    # loop all initial selected objects (which will likely just be one obect.. I haven't tried setting up multiple yet)
    for o in selected_list:
        
        # select the object
        bpy.context.scene.objects[o.name].select_set(True)

        scn = bpy.context.scene
        camera = bpy.context.scene.objects["Camera"]
        # calculate the rotation radius
        camera_distance = math.sqrt(camera.location.x * camera.location.x + camera.location.y * camera.location.y)
        
        
        stored_actions = []
        output_data = {}
        
        # loop through the actions
        for a in bpy.data.actions:
            #assign the action
            bpy.context.active_object.animation_data.action = bpy.data.actions.get(a.name)
            
            #dynamically set the last frame to render based on action
            scn.frame_end = int(bpy.context.active_object.animation_data.action.frame_range[1])
            
            #set which actions you want to render.  Make sure to use the exact name of the action!
            if (a.name in RENDERED_ANIMATIONS):
            
                output_data[a.name] = {}
                    
                #create folder for animation
                action_folder = os.path.join(path, a.name)
                if not os.path.exists(action_folder):
                    os.makedirs(action_folder)
                
                #loop through all 8 directions
                for angle in range(0, 360, 45):
                    if angle == 0:
                        angleDir = "W"
                    if angle == 45:
                        angleDir = "NW"
                    if angle == 90:
                        angleDir = "N"
                    if angle == 135:
                        angleDir = "NE"
                    if angle == 180:
                        angleDir = "E"
                    if angle == 225:
                        angleDir = "SE"
                    if angle == 270:
                        angleDir = "S"
                    if angle == 315:
                        angleDir = "SW"
                        
                    if (angleDir in RENDERED_DIRECTIONS):

                        print("Processing ", a.name, angleDir)         

                        #create folder for specific angle
                        animation_folder = os.path.join(action_folder, angleDir)
                        if not os.path.exists(animation_folder):
                            os.makedirs(animation_folder)
                        
                        #rotate the model for the new angle
                        camera.location.x = camera_distance * math.cos(math.radians(angle))
                        camera.location.y = camera_distance * math.sin(math.radians(angle))
                        
                        # the below is for the use case where the root needed to be translated.
#                        obRoot.rotation_euler[2] = math.radians(angle)
                        
                        output_data[a.name][a.name + "_" + angleDir] = { "loop" : DEFAULT_LOOP, "fps" : DEFAULT_FPS } 
                        
                        if PROCESS_NORMALS:
                            output_data[a.name][a.name + "_" + angleDir + "_normal"] = { "loop" : DEFAULT_LOOP, "fps" : DEFAULT_FPS } 
                            
                            
                        #loop through and render frames.  Can set how "often" it renders.
                        #Every frame is likely not needed.
                        counter = 0
                        for i in range(s.frame_start,s.frame_end, RENDER_EVERY_X_FRAMES):
                            
                            render_image(i, counter, animation_folder, normal_file_output)
                            counter += 1

                        if i != s.frame_end and FORCE_RENDER_LAST_FRAME:
                            render_image(s.frame_end, counter, animation_folder, normal_file_output)
                            
                        # Reset camera in the end
                        camera.location.x = camera_distance * math.cos(math.radians(270))
                        camera.location.y = camera_distance * math.sin(math.radians(270))
            
    if len(output_data.keys()) > 0:
        with open(os.path.join(path,'sprite_sheets.jbss'),'w') as godot_resource:
            json.dump(output_data, godot_resource, sort_keys=True, indent=4)
            
                                                 
render8directions_selected_objects(OUTPUT_FOLDER)

