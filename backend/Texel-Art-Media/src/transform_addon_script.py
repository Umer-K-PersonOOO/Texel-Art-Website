import bpy
import json
import time
import os
import sys

# Parse command-line args after '--'
args = sys.argv
if "--" in args:
    arg_index = args.index("--") + 1
    if arg_index < len(args):
        export_name = args[arg_index]
    else:
        export_name = "default_output"
else:
    export_name = "default_output"


class BlenderMocapHandler():
    def clear_scene(self):
        """Manually removes all objects instead of resetting to factory settings."""
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')  # Switch to object mode
        bpy.ops.object.select_all(action='SELECT')  # Select all objects
        bpy.ops.object.delete()  # Delete selected objects
        for collection in bpy.data.collections:
            bpy.data.collections.remove(collection)  # Remove all collections

        # Ensure there's no lingering data
        for block in bpy.data.objects:
            bpy.data.objects.remove(block)
        for block in bpy.data.meshes:
            bpy.data.meshes.remove(block)
        for block in bpy.data.materials:
            bpy.data.materials.remove(block)
        for block in bpy.data.textures:
            bpy.data.textures.remove(block)
        for block in bpy.data.images:
            bpy.data.images.remove(block)
        
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        print("Scene cleared")
        
    def check_detection_status(self):
        """Checks if the detection process has completed."""
        if not bpy.context.scene.cgtinker_mediapipe.modal_active:
            print("Detection complete")
            print("FINISHED RUNNING -------------------------------")
            self.get_cgt_points()
            return None  # Stop the timer
        return 0.5

    # Clear the scene at the start
    def __init__(self):
        self.video_file_name = ""
        # Ensure add-on is enabled
        addon_name = "BlendArMocap"
        self.output = None
        if addon_name not in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_enable(module=addon_name)
        # Set the parameters
        # Remove the default cube
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.context.scene.cgtinker_mediapipe.detection_input_type = "movie"
        self.clear_scene()
    
    def apply_animation(self, export_name):
        # to do: figure out how to get the animation to transfer
        # container = bpy.data.collections.new("cgt_DRIVERS")
        # pose_driver = bpy.data.collections.new("cgt_POSE")
        # bpy.context.scene.collection.children.link(container)
        # container.children.link(pose_driver)
        
        
        # Step 1: Append the rig object from the blend file
        rig_blend_path = "/home/personooo/Desktop/LetsTryThisOne3.blend"

        with bpy.data.libraries.load(rig_blend_path, link=False) as (data_from, data_to):
            data_to.objects = data_from.objects  # Import everything

        # Step 2: Link all imported objects to the current scene
        imported_rig = None
        linked_meshes = []

        for obj in data_to.objects:
            if obj:
                bpy.context.collection.objects.link(obj)
                # Identify the rig
                if obj.name == "rig":
                    imported_rig = obj

        # Step 3: Auto-detect meshes parented to the rig
        if imported_rig:
            linked_meshes = [
                obj for obj in bpy.data.objects
                if obj.parent == imported_rig and obj.type in {"MESH"}
            ]
            print("Detected rig:", imported_rig.name)
            print("Detected meshes:", [m.name for m in linked_meshes])
        else:
            print("❌ Rig not found!")


        # Step 2: Append the 'cgt_DRIVERS' collection
        blend_path = "/home/personooo/test.blend"
        collection_name = "cgt_DRIVERS"

        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
            if collection_name in data_from.collections:
                data_to.collections.append(collection_name)

        # Link imported collection to scene
        for coll in data_to.collections:
            bpy.context.scene.collection.children.link(coll)

        # Step 3: Get reference to 'cgt_POSE' inside 'cgt_DRIVERS'
        drivers_collection = bpy.data.collections.get("cgt_DRIVERS")
        pose_driver = drivers_collection.children.get("cgt_POSE")

        print("Drivers Collection:", drivers_collection)
        print("Pose Driver:", pose_driver)

        # Step 4: Run your operators
        bpy.context.scene.cgtinker_mediapipe.enum_detection_type = 'POSE'
        # bpy.ops.wm.cgt_feature_detection_operator('EXEC_DEFAULT')

        # Set pose driver collection
        bpy.context.scene.cgtinker_transfer.selected_driver_collection = pose_driver
        # bpy.context.scene.cgtinker_transfer.transfer_types = armature_file
        imported_rig = bpy.data.objects.get("rig")

        if imported_rig:
            bpy.context.scene.cgtinker_transfer.selected_rig = imported_rig
            print("Selected Rig set to:", imported_rig)
        else:
            print("Rig not found!")

        # Apply properties
        bpy.ops.button.cgt_object_apply_properties()
        
        # 1. Set rig to Pose Mode and select all bones
        imported_rig = bpy.data.objects.get("rig")
        bpy.ops.object.select_all(action='DESELECT')
        imported_rig.select_set(True)
        bpy.context.view_layer.objects.active = imported_rig
        bpy.context.view_layer.update()
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')

        # 2. Bake the action
        bpy.ops.nla.bake(
            frame_start=1,
            frame_end=250,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            use_current_action=True,
            bake_types={'POSE'}
        )

        # 3. Delete all drivers from all objects
        def delete_collection_recursive(collection_name):
            coll = bpy.data.collections.get(collection_name)
            if not coll:
                print(f"Collection '{collection_name}' not found.")
                return

            # Recursively delete all nested collections
            def delete_contents(collection):
                for obj in list(collection.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                for child in list(collection.children):
                    delete_contents(child)
                    bpy.data.collections.remove(child)

            delete_contents(coll)

            # Finally delete the top-level collection
            bpy.data.collections.remove(coll)
            print(f"Deleted collection and all contents: {collection_name}")

        # Call it
        delete_collection_recursive("cgt_DRIVERS")


        # 4. Return to Object Mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # 5. Export as GLB
        output_dir = os.path.expanduser(os.path.join("~", "blender_tmp"))
        os.makedirs(output_dir, exist_ok=True)
        glb_path = os.path.join(output_dir, f"{export_name}.glb")

        bpy.ops.export_scene.gltf(
            filepath=glb_path,
            export_format='GLB',
            use_selection=False,  # Correct name
            export_apply=True
        )

        print(f"GLB file exported to: {glb_path}")
        
        bpy.ops.wm.quit_blender()

        
        # armature_file = "/home/personooo/rigs.blend"
        # bpy.ops.wm.open_mainfile(filepath=armature_file)
        
        # blend_path = "/home/personooo/test.blend"
        # collection_name = "cgt_DRIVERS"

        # with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        #     if collection_name in data_from.collections:
        #         data_to.collections.append(collection_name)
            

        # # Link to scene
        # for coll in data_to.collections:
        #     bpy.context.scene.collection.children.link(coll)
        

        # # bpy.ops.import_scene.fbx(filepath=point_file)
        # # imported_objects = bpy.context.selected_objects
        # # for obj in imported_objects:
        # #     # Unlink from all other collections
        # #     for coll in obj.users_collection:
        # #         coll.objects.unlink(obj)
        # #     # Link to target collection
        # #     pose_driver.objects.link(obj)
        # # bpy.context.view_layer.objects.active = bpy.data.objects["cgt_POSE"]
        
            
        # bpy.context.scene.cgtinker_mediapipe.enum_detection_type = 'POSE'
        # bpy.ops.wm.cgt_feature_detection_operator('EXEC_DEFAULT')
        # bpy.context.scene.collection.children.link("cgt_DRIVERS")
        # print("Drivers: ", bpy.data.collections.get('cgt_DRIVERS'))
        
        # # bpy.context.scene.cgtinker_transfer.selected_driver_collection = pose_driver
        # # bpy.context.scene.cgtinker_transfer.transfer_types = armature_file
        # # bpy.ops.button.cgt_object_apply_properties()

        # # to do: fix actual armature file (needs to be rigified)
        # # to do: precondition file so it actually works
        
        


        
    
        
    
handler = BlenderMocapHandler()
handler.apply_animation(export_name)
# time.sleep(20)
# while not bpy.context.scene.cgtinker_mediapipe.modal_active:
#     print("Waiting for detection to finish...")
#     time.sleep(1)
# while True:
#     time.sleep(1)
#     print(bpy.context.scene.cgtinker_mediapipe.modal_active)
# bpy.ops.wm.quit_blender_operator()
# print("FINISHED RUNNING -------------------------------")
# output = handler.get_cgt_points()

