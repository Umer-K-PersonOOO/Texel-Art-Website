import bpy
import json
import time
import os
from datetime import datetime
import sys

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
            if not hasattr(self, "_done"):
                self._done = True  # Prevents running multiple times
                print("Detection complete")
                print("FINISHED RUNNING -------------------------------")
                self.get_cgt_points()
                bpy.app.timers.register(self._exit_blender, first_interval=0.1)
            return None  # Stop the timer
        return 0.5

    def _exit_blender(self):
        print("Closing Blender...")
        sys.exit(0)
        bpy.ops.wm.quit_blender()
        return None  # Just in case, to stop the new timer too

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
        
    def detect(self, video_path, detection_type="POSE", key_frame_step=4, min_detection_confidence=0.5):
        self.video_file_name = os.path.splitext(os.path.basename(video_path))[0]

        # Start detection using EXEC_DEFAULT instead of INVOKE_DEFAULT
        bpy.context.scene.cgtinker_mediapipe.mov_data_path = video_path # "/home/personooo/Desktop/Code/Texel-Art-Media/src/Walk.mp4"
        bpy.context.scene.cgtinker_mediapipe.enum_detection_type = detection_type
        bpy.context.scene.cgtinker_mediapipe.key_frame_step = key_frame_step
        bpy.context.scene.cgtinker_mediapipe.min_detection_confidence = min_detection_confidence
        print("Starting detection...")
        bpy.ops.wm.cgt_feature_detection_operator('EXEC_DEFAULT')
        print("Detection complete")
        bpy.app.timers.register(self.check_detection_status, first_interval=0.5)
        print("This complete")
        # bpy.ops.wm.quit_blender()
        # output = handler.get_cgt_points()
    
        
    def get_cgt_points(self):
        """Saves the cgt_DRIVERS collection as a .blend file."""

        if "--" in sys.argv:
            idx = sys.argv.index("--")
            collection_name = sys.argv[idx + 1]
            print("Received collection name:", collection_name)
        else:
            print("No custom collection name passed.")
            return -1

        output_path = os.path.expanduser(os.path.join("~", "blender_tmp" ,f"{collection_name}.blend"))
        print("Output path:", output_path)

        # Deselect all, just for safety
        bpy.ops.object.select_all(action='DESELECT')

        # Find and isolate the collection
        collection = bpy.data.collections.get("cgt_DRIVERS")
        if not collection:
            print("Collection 'cgt_DRIVERS' not found.")
            return -1

        # Create a new temporary scene
        new_scene = bpy.data.scenes.new(name="ExportScene")
        bpy.context.window.scene = new_scene

        # Link the collection
        new_scene.collection.children.link(collection)

        # Save the new .blend
        bpy.ops.wm.save_as_mainfile(filepath=output_path)
        print(f"Saved 'cgt_DRIVERS' collection to {output_path}")


    
handler = BlenderMocapHandler()

# Get args
if "--" in sys.argv:
    idx = sys.argv.index("--")
    collection_name = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "output"
    video_path = sys.argv[idx + 2] if len(sys.argv) > idx + 2 else ""
else:
    collection_name = "output"
    video_path = ""

print("Collection Name:", collection_name)
print("Video Path:", video_path)

# Run detection
handler.detect(video_path)

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






# import sys
# import os

# # Get the absolute path of the src directory
# script_dir = os.path.dirname(os.path.abspath(__file__))
# src_path = os.path.join(script_dir, "..")  # Adjust as needed

# # Add to sys.path if not already present
# if src_path not in sys.path:
#     sys.path.append(src_path)

# # Now you can import the modules
# import cgt_core
# import cgt_freemocap
# import cgt_mediapipe
# import cgt_socket_ipc
# import cgt_transfer
# # from cgt_mediapipe.cgt_mp_core import cv_stream


# # Add a custom property to store detection settings
# bpy.types.Scene.cgtinker_mediapipe = bpy.props.PointerProperty(type=bpy.types.PropertyGroup)

# bpy.context.scene.cgtinker_mediapipe.enum_detection_type = 'POSE'  # Use Pose detection
# bpy.context.scene.cgtinker_mediapipe.detection_input_type = 'movie'  # Movie instead of webcam
# bpy.context.scene.cgtinker_mediapipe.mov_data_path = "/home/personooo/Desktop/Code/Texel-Art-Media/src/Walk.mp4"
# bpy.context.scene.cgtinker_mediapipe.key_frame_step = 4
# bpy.context.scene.cgtinker_mediapipe.min_detection_confidence = 0.5
# bpy.context.scene.cgtinker_mediapipe.modal_active = False
# bpy.context.scene.cgtinker_mediapipe.refine_face_landmarks = False
# bpy.context.scene.cgtinker_mediapipe.pose_model_complexity = 1
# bpy.context.scene.cgtinker_mediapipe.webcam_input_device = 0  # Default webcam if needed
# bpy.context.scene.cgtinker_mediapipe.enum_stream_dim = 'hd'  # Set resolution
# bpy.context.scene.cgtinker_mediapipe.enum_stream_type = 0  # Backend type

# print("Properties set up successfully!")

# from cgt_mediapipe import cgt_mp_detection_operator

# # Register the operator
# cgt_mp_detection_operator.register()

# # Run the operator manually
# bpy.ops.wm.cgt_feature_detection_operator()

