# load_drivers_only.py
"""
Append the mocap driver collection (cgt_DRIVERS / cgt_POSE) into the current Blender scene
without applying any transfer or loading mappings.

Usage:
  - Set MOCAP_BLEND below to the .blend file that contains cgt_DRIVERS.
  - Run in Blender: blender --python Texel-Art-Media/src/load_drivers_only.py
  - The script links cgt_DRIVERS (and its children) into the scene.
  - Set QUIT_AFTER to True if you want Blender to close after loading.
"""
from __future__ import annotations
import bpy
import pathlib
import sys
import types
import os

HERE = pathlib.Path(__file__).resolve()
SRC_DIR = HERE.parent
ADDON_ROOT = SRC_DIR.parent


def _split_env_list(raw: str | None):
    if not raw:
        return None
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item]


# ------------------ CONFIG ------------------ #
# Path to the mocap .blend containing cgt_DRIVERS
MOCAP_BLEND = os.getenv("MOCAP_BLEND_PATH", "shared/out/walk1.blend")
# Path to the rig .blend to append (defaults to Remy rig)
RIG_BLEND = os.getenv("RIG_BLEND_PATH", "shared/rig_uploads/remy.blend")
# Comma separated list of rig object names to append (load all if empty)
RIG_OBJECT_NAMES = _split_env_list(
    os.getenv(
        "RIG_OBJECT_NAMES",
        "Armature,Body,Bottoms,Eyelashes,Eyes,Hair,Shoes,Tops",
    )
)
# Optional name for the collection that will hold the appended rig
RIG_COLLECTION_NAME = os.getenv("RIG_COLLECTION_NAME", "remy_rig")
# Quit Blender when done?
QUIT_AFTER = False
# -------------------------------------------- #


def ensure_blendarmocap_namespace():
    if "BlendArMocap" not in sys.modules:
        pkg = types.ModuleType("BlendArMocap")
        pkg.__path__ = [str(ADDON_ROOT)]
        sys.modules["BlendArMocap"] = pkg
    if "BlendArMocap.src" not in sys.modules:
        src_pkg = types.ModuleType("BlendArMocap.src")
        src_pkg.__path__ = [str(SRC_DIR)]
        sys.modules["BlendArMocap.src"] = src_pkg


def append_drivers_collection(blend_path: str):
    if not os.path.exists(blend_path):
        raise RuntimeError(f"mocap blend not found: {blend_path}")
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


def append_rig_objects(blend_path: str, object_names=None, collection_name: str | None = None):
    if not os.path.exists(blend_path):
        raise RuntimeError(f"rig blend not found: {blend_path}")

    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        available = set(data_from.objects)
        if object_names:
            missing = [name for name in object_names if name not in available]
            if missing:
                raise RuntimeError(
                    f"Objects {missing} not found in rig blend {blend_path}. "
                    f"Available objects: {sorted(available)}"
                )
            data_to.objects = object_names
        else:
            data_to.objects = list(available)

    appended_objects = [obj for obj in data_to.objects if obj is not None]
    if not appended_objects:
        return []

    target_collection = None
    if collection_name:
        target_collection = bpy.data.collections.get(collection_name)
        if target_collection is None:
            target_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(target_collection)

    for obj in appended_objects:
        if collection_name and target_collection is not None:
            if target_collection.objects.get(obj.name) is None:
                target_collection.objects.link(obj)
        else:
            if bpy.context.scene.collection.objects.get(obj.name) is None:
                bpy.context.scene.collection.objects.link(obj)

    return appended_objects


def main():
    ensure_blendarmocap_namespace()
    drivers_col, pose_col = append_drivers_collection(MOCAP_BLEND)
    print("Driver collection:", drivers_col, "Pose collection:", pose_col)

    # Wire addon UI state if available
    rig_objects = []
    try:
        rig_objects = append_rig_objects(RIG_BLEND, RIG_OBJECT_NAMES, RIG_COLLECTION_NAME)
        print(f"Appended rig from {RIG_BLEND}: {[obj.name for obj in rig_objects]}")
    except RuntimeError as exc:
        print(exc)

    try:
        transfer_state = bpy.context.scene.cgtinker_transfer
        transfer_state.selected_driver_collection = pose_col or drivers_col
        armature_obj = next((obj for obj in rig_objects if obj.type == 'ARMATURE'), None)
        if armature_obj is not None:
            transfer_state.selected_rig = armature_obj
    except Exception:
        pass

    if QUIT_AFTER:
        bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
