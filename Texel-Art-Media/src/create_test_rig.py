# create_test_rig.py
"""
Build a simple humanoid armature for testing (no face/fingers):
 - root -> torso -> chest -> head
 - arms: upper_arm_fk.* -> forearm_fk.* -> hand.*
 - legs: thigh_fk.* -> shin_fk.* -> foot.*

Usage (inside Blender):
    blender --python Texel-Art-Media/src/create_test_rig.py -- --name cgt_PlayRig

If a rig with the same name exists, it will be replaced.
"""
from __future__ import annotations
import bpy
import sys
from mathutils import Vector


def parse_args():
    rig_name = "cgt_PlayRig"
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
        if len(argv) >= 2 and argv[0] == "--name":
            rig_name = argv[1]
    return rig_name


def ensure_object_mode():
    obj = bpy.context.object
    if obj and obj.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def remove_existing(name: str):
    obj = bpy.data.objects.get(name)
    if obj and obj.type == "ARMATURE":
        ensure_object_mode()
        try:
            # Attempt deletion via selection if the object is in the current view layer
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.ops.object.delete(use_global=False)
        except RuntimeError:
            # Fallback: unlink from all collections and remove datablock
            for col in list(obj.users_collection):
                col.objects.unlink(obj)
            bpy.data.objects.remove(obj, do_unlink=True)


def add_bone(arm, name: str, head: Vector, tail: Vector):
    eb = arm.edit_bones.new(name)
    eb.head = head
    eb.tail = tail if (tail - head).length > 1e-6 else head + Vector((0, 0, 0.05))
    return eb


def build_rig(name: str):
    ensure_object_mode()
    remove_existing(name)

    arm_data = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(rig)

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    # Core bones
    root = add_bone(arm_data, "root", Vector((0, 0, 0)), Vector((0, 0.05, 0.1)))
    torso = add_bone(arm_data, "torso", Vector((0, 0, 0.1)), Vector((0, 0, 1.0)))
    chest = add_bone(arm_data, "chest", Vector((0, 0, 1.0)), Vector((0, 0, 1.3)))
    head = add_bone(arm_data, "head", Vector((0, 0, 1.3)), Vector((0, 0, 1.6)))
    torso.parent = root
    torso.use_connect = True
    chest.parent = torso
    chest.use_connect = True
    head.parent = chest
    head.use_connect = True

    def add_arm(side: str):
        sx = 1 if side == "L" else -1
        upper = add_bone(arm_data, f"upper_arm_fk.{side}",
                         Vector((0.2 * sx, 0, 1.25)),
                         Vector((0.55 * sx, 0, 1.25)))
        forearm = add_bone(arm_data, f"forearm_fk.{side}",
                           Vector((0.55 * sx, 0, 1.25)),
                           Vector((0.8 * sx, 0, 1.05)))
        hand = add_bone(arm_data, f"hand.{side}",
                        Vector((0.8 * sx, 0, 1.05)),
                        Vector((0.9 * sx, 0, 1.0)))
        upper.parent = chest
        upper.use_connect = False
        forearm.parent = upper
        forearm.use_connect = True
        hand.parent = forearm
        hand.use_connect = True

    def add_leg(side: str):
        sx = 1 if side == "L" else -1
        thigh = add_bone(arm_data, f"thigh_fk.{side}",
                         Vector((0.1 * sx, 0, 1.0)),
                         Vector((0.1 * sx, 0, 0.6)))
        shin = add_bone(arm_data, f"shin_fk.{side}",
                        Vector((0.1 * sx, 0, 0.6)),
                        Vector((0.1 * sx, 0, 0.3)))
        foot = add_bone(arm_data, f"foot.{side}",
                        Vector((0.1 * sx, 0.15, 0.1)),
                        Vector((0.1 * sx, 0.2, 0.05)))
        thigh.parent = torso
        thigh.use_connect = False
        shin.parent = thigh
        shin.use_connect = True
        foot.parent = shin
        foot.use_connect = True

    add_arm("L")
    add_arm("R")
    add_leg("L")
    add_leg("R")

    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def main():
    rig_name = parse_args()
    rig = build_rig(rig_name)
    print(f"Created test rig: {rig.name} with {len(rig.data.bones)} bones")


if __name__ == "__main__":
    main()
