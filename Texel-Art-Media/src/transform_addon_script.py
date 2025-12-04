# transform_addon_script.py
import bpy, os, sys, pathlib
import importlib

# Ensure addon sources are importable both inside the packaged addon (BlendArMocap)
# and when running from a checked-out repo.
HERE = pathlib.Path(__file__).resolve()
SRC_DIR = HERE.parent
ADDON_ROOT = SRC_DIR.parent  # e.g. /root/.config/blender/.../BlendArMocap
for p in (SRC_DIR, ADDON_ROOT, ADDON_ROOT.parent):
    if p and str(p) not in sys.path:
        sys.path.append(str(p))

try:
    # Preferred: import with the addon package name so relative imports inside modules stay valid
    from BlendArMocap.src.cgt_transfer.core_transfer import tf_load_object_properties, tf_transfer_management
except ImportError:
    # Fallback: direct import when running from the source tree
    from cgt_transfer.core_transfer import tf_load_object_properties, tf_transfer_management

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/shared/out")
BUILTIN_MAPPING = pathlib.Path(__file__).parent / "cgt_transfer" / "data" / "Rigify_Humanoid_DefaultFace_v0.6.1.json"

# Args: -- <export_name> <blend_input_path> <rig_path> [mapping_path]
args = sys.argv
if "--" in args:
    i = args.index("--")
    export_name = args[i+1]
    blend_input_path = args[i+2]
    rig_path = args[i+3] if len(args) > i+3 else os.getenv("RIG_BLEND_PATH", "")
    mapping_path = args[i+4] if len(args) > i+4 else os.getenv("TRANSFER_MAPPING_PATH", "")
else:
    export_name = "default_output"
    blend_input_path = "/tmp/fallback_mocap.blend"
    rig_path = os.getenv("RIG_BLEND_PATH", "")
    mapping_path = os.getenv("TRANSFER_MAPPING_PATH", "")

mapping_path = mapping_path or str(BUILTIN_MAPPING)
mapping_path = os.path.abspath(mapping_path)

if not rig_path or not os.path.exists(rig_path):
    raise RuntimeError(f"Rig file missing or not found: {rig_path}")
if not os.path.exists(mapping_path):
    raise RuntimeError(f"Transfer mapping file missing or not found: {mapping_path}")

def clear_scene_hard():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # purge data
    for datablock_list in (
        bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images,
        bpy.data.textures, bpy.data.collections, bpy.data.actions,
    ):
        for datablock in list(datablock_list):
            try:
                datablock.user_clear()
                datablock_list.remove(datablock)
            except Exception:
                pass
    bpy.ops.outliner.orphans_purge(do_recursive=True)

def import_rig_any(path: str):
    ext = pathlib.Path(path).suffix.lower()
    before = set(bpy.data.objects)
    if ext == ".blend":
        with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
            # bring in objects & collections
            data_to.objects = data_from.objects
            data_to.collections = list(data_from.collections)
        # link all imported objects (safe)
        for obj in data_to.objects:
            if obj and obj.name not in bpy.context.scene.objects:
                try:
                    bpy.context.collection.objects.link(obj)
                except Exception:
                    pass
        for coll in data_to.collections:
            try:
                bpy.context.scene.collection.children.link(coll)
            except Exception:
                pass
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=True)
    elif ext == ".obj":
        # Newer Blender uses wm.obj_import; older uses import_scene.obj
        try:
            bpy.ops.wm.obj_import(filepath=path)
        except AttributeError:
            bpy.ops.import_scene.obj(filepath=path)
    else:
        raise RuntimeError(f"Unsupported rig format: {ext}")

    after = set(bpy.data.objects)
    new_objs = [o for o in after - before if isinstance(o, bpy.types.Object)]
    return new_objs

def pick_armature():
    """Choose the best armature: prefer Rigify-looking rigs, then common names, else first armature."""
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if not arms:
        return None
    # Heuristic 1: name hints
    by_name = [a for a in arms if a.name.lower() in {"rig", "armature"} or "rigify" in a.name.lower()]
    if by_name:
        return by_name[0]
    # Heuristic 2: bone naming typical to rigify (DEF-, ORG-, MCH-, CTRL-)
    def rigify_score(a):
        names = [b.name for b in a.data.bones]
        prefixes = sum(n.startswith(("DEF-","ORG-","MCH-","CTRL-")) for n in names)
        return prefixes
    best = max(arms, key=rigify_score)
    return best

def append_drivers_collection(blend_path: str):
    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        if "cgt_DRIVERS" in data_from.collections:
            data_to.collections = ["cgt_DRIVERS"]
        else:
            raise RuntimeError("cgt_DRIVERS collection not found in mocap .blend")
    for coll in data_to.collections:
        bpy.context.scene.collection.children.link(coll)
    drivers = bpy.data.collections.get("cgt_DRIVERS")
    pose = drivers.children.get("cgt_POSE") if drivers else None
    return drivers, pose

def bake_pose_action(rig_obj):
    bpy.ops.object.select_all(action='DESELECT')
    rig_obj.select_set(True)
    bpy.context.view_layer.objects.active = rig_obj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(
        frame_start=1, frame_end=250,
        only_selected=True, visual_keying=True,
        clear_constraints=True, use_current_action=True,
        bake_types={'POSE'}
    )
    bpy.ops.object.mode_set(mode='OBJECT')

def delete_collection_recursive(name: str):
    coll = bpy.data.collections.get(name)
    if not coll:
        return
    def purge(c):
        for obj in list(c.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for child in list(c.children):
            purge(child)
            bpy.data.collections.remove(child)
    purge(coll)
    bpy.data.collections.remove(coll)

# -------- Pipeline --------
clear_scene_hard()

# 1) Import the rig (blend/fbx/obj)
import_rig_any(rig_path)

# 2) Validate & pick an armature
rig_obj = pick_armature()
if not rig_obj:
    raise RuntimeError("No armature found in rig file")

print(f"Selected Rig set to: {rig_obj!r}")

# 3) Bring in drivers from the mocap .blend
drivers, pose_driver = append_drivers_collection(blend_input_path)
print("Drivers Collection:", drivers, "Pose Driver:", pose_driver)
print(f"Using transfer mapping: {mapping_path}")

# 4) Wire up addon settings (as you had)
bpy.context.scene.cgtinker_mediapipe.enum_detection_type = 'POSE'
bpy.context.scene.cgtinker_transfer.selected_driver_collection = pose_driver
bpy.context.scene.cgtinker_transfer.selected_rig = rig_obj

# Load mapping and transfer onto rig
tf_load_object_properties.load(bpy.context.scene.objects, mapping_path, rig_obj)
objs_for_transfer = []
def _collect(col):
    objs_for_transfer.extend(list(col.objects))
    for sub in col.children:
        _collect(sub)
if pose_driver:
    _collect(pose_driver)
else:
    raise RuntimeError("Pose driver collection not found in mocap .blend")
tf_transfer_management.main(objs_for_transfer)
bpy.context.view_layer.update()

# 5) Bake pose on the detected rig
bake_pose_action(rig_obj)

# 6) Remove driver collections
delete_collection_recursive("cgt_DRIVERS")

# 7) Export GLB
os.makedirs(OUTPUT_DIR, exist_ok=True)
glb_path = os.path.join(OUTPUT_DIR, f"{export_name}.glb")
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_animations=True,
    export_skins=True
)
print(f"GLB file exported to: {glb_path}")
bpy.ops.wm.quit_blender()
