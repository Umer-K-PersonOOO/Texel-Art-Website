import bpy
point_file = "/tmp/cgt_DRIVERS.fbx"
armature_file = "/home/personooo/Desktop/Code/Texel-Art-Website/default/Texel-Art-Website/backend/uploads/X Bot.fbx"
# bpy.ops.import_scene.fbx(filepath=point_file)
bpy.ops.import_scene.fbx(filepath=armature_file, \
                                force_connect_children=True, \
                                automatic_bone_orientation=True)

bpy.ops.import_scene.fbx(filepath=armature_file, \
                                force_connect_children=True, \
                                automatic_bone_orientation=True)