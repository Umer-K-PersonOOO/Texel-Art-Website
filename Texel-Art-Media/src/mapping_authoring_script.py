# mapping_authoring_script.py
"""
Helper to set up a Blender scene for authoring new motion-transfer mappings.

Usage (from repo root):
    blender --python Texel-Art-Media/src/mapping_authoring_script.py -- \
        --mocap /shared/out/walk1.blend \
        --base-mapping Texel-Art-Media/src/cgt_transfer/data/Rigify_Humanoid_DefaultFace_v0.6.1.json \
        --save-path /shared/rig_mappings/remy_mimaxo.json \
        --create-play-rig \
        --no-quit

By default this script:
 - assumes the target rig is already present in the scene,
 - appends the driver collection (cgt_DRIVERS) from a mocap .blend,
 - loads a base mapping (defaults to the built-in Rigify template),
 - wires Blender UI state (selected rig, driver collection),
 - optionally applies transfer to preview motion (disabled by default),
 - optionally saves the mapping to disk.
You can also pass --create-play-rig to scaffold a minimal armature using all target bones from the mapping file.
If the mocap .blend is missing, the script will create empty driver collections based on the mapping JSON so you can still author targets.
"""
from __future__ import annotations
import bpy, os, sys, pathlib, traceback, types, json, math
import importlib
from typing import Dict, Any, Optional, List, Tuple
from mathutils import Vector

# Ensure addon sources are importable both inside the packaged addon (BlendArMocap)
# and when running from a checked-out repo.
HERE = pathlib.Path(__file__).resolve()
SRC_DIR = HERE.parent
ADDON_ROOT = SRC_DIR.parent  # e.g. /root/.config/blender/.../BlendArMocap
# Make sure we can import both the installed add-on namespace (BlendArMocap)
# and the source checkout (cgt_transfer, cgt_core, ...).
for p in (SRC_DIR, ADDON_ROOT, ADDON_ROOT.parent):
    if p and str(p) not in sys.path:
        sys.path.append(str(p))

# If the add-on isn't installed under BlendArMocap/, create a lightweight namespace
# so `from BlendArMocap.src...` works against the checked-out sources.
def ensure_blendarmocap_namespace():
    if "BlendArMocap" not in sys.modules:
        pkg = types.ModuleType("BlendArMocap")
        pkg.__path__ = [str(ADDON_ROOT)]
        sys.modules["BlendArMocap"] = pkg
    if "BlendArMocap.src" not in sys.modules:
        src_pkg = types.ModuleType("BlendArMocap.src")
        src_pkg.__path__ = [str(SRC_DIR)]
        sys.modules["BlendArMocap.src"] = src_pkg

ensure_blendarmocap_namespace()

try:
    # Preferred: import with the addon package name so relative imports stay valid
    from BlendArMocap.src.cgt_transfer.core_transfer import (
        tf_load_object_properties,
        tf_transfer_management,
        tf_save_object_properties,
    )
    from BlendArMocap.src.cgt_core.cgt_bpy import cgt_bpy_utils, cgt_drivers
except ImportError as exc:
    msg = (
        "Unable to import BlendArMocap modules. "
        "Ensure either the add-on is installed as 'BlendArMocap' or run from the repo root "
        "so Texel-Art-Media/src is on PYTHONPATH. "
        f"Details: {exc}"
    )
    raise ImportError(msg) from exc


OUTPUT_DIR: Optional[pathlib.Path] = None
BUILTIN_MAPPING = SRC_DIR / "cgt_transfer" / "data" / "Rigify_Humanoid_DefaultFace_v0.6.1.json"


# --------------------- Scene helpers --------------------- #
def clear_scene_hard():
    """Unused now, kept for reference; script no longer clears scene."""
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # purge data
    for datablock_list in (
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.textures,
        bpy.data.collections,
        bpy.data.actions,
    ):
        for datablock in list(datablock_list):
            try:
                datablock.user_clear()
                datablock_list.remove(datablock)
            except Exception:
                pass
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def import_rig_any(path: str) -> List[bpy.types.Object]:
    """Unused now; rig must already be present in the scene."""
    ext = pathlib.Path(path).suffix.lower()
    before = set(bpy.data.objects)
    if ext == ".blend":
        with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
            data_to.objects = data_from.objects
            data_to.collections = list(data_from.collections)
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
        try:
            bpy.ops.wm.obj_import(filepath=path)
        except AttributeError:
            bpy.ops.import_scene.obj(filepath=path)
    else:
        raise RuntimeError(f"Unsupported rig format: {ext}")

    after = set(bpy.data.objects)
    return [o for o in after - before if isinstance(o, bpy.types.Object)]


def pick_armature() -> Optional[bpy.types.Object]:
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if not arms:
        return None
    by_name = [a for a in arms if a.name.lower() in {"rig", "armature"} or "rigify" in a.name.lower()]
    if by_name:
        return by_name[0]

    def rigify_score(a: bpy.types.Object) -> int:
        names = [b.name for b in a.data.bones]
        prefixes = sum(n.startswith(("DEF-", "ORG-", "MCH-", "CTRL-")) for n in names)
        return prefixes

    return max(arms, key=rigify_score)


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


def ensure_driver_collections_from_mapping(mapping_path: str):
    """Create a minimal driver collection hierarchy when no mocap blend is available."""
    try:
        with open(mapping_path, "r", encoding="utf-8") as fh:
            mapping = json.load(fh)
    except Exception as exc:
        raise RuntimeError(f"Failed to read mapping file {mapping_path}") from exc

    def ensure_collection(name: str) -> bpy.types.Collection:
        col = bpy.data.collections.get(name)
        if col is None:
            col = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(col)
        return col

    root = ensure_collection("cgt_DRIVERS")
    collection_names = {entry.get("collection") for entry in mapping.values() if isinstance(entry, dict)}
    pose_col = None
    for cname in sorted(x for x in collection_names if x):
        col = ensure_collection(cname)
        if col.name not in [c.name for c in root.children]:
            root.children.link(col)
        if col.name == "cgt_POSE":
            pose_col = col
    return root, pose_col


def collect_objects(col: bpy.types.Collection) -> List[bpy.types.Object]:
    out: List[bpy.types.Object] = []
    def _walk(c: bpy.types.Collection):
        out.extend(list(c.objects))
        for sub in c.children:
            _walk(sub)
    _walk(col)
    return out


def create_instruction_text(
    params: Dict[str, Any],
    pose_collection: Optional[bpy.types.Collection],
    output_dir: pathlib.Path,
    rig_obj: Optional[bpy.types.Object],
):
    rig_line = f"Rig: {rig_obj.name if rig_obj else '<no armature found>'}\n"
    msg = [
        "BlendArMocap Mapping Authoring Helper\n",
        "--------------------------------------\n",
        rig_line,
        f"Mocap drivers: {params['mocap_blend']}\n",
        f"Base mapping: {params['base_mapping']}\n",
        "\nNext steps:\n",
        "1) In the Constraints tab, use the BlendArMocap panels to point each driver empty at your rig bones.\n",
        "2) Use 'Transfer Selection' after editing drivers/constraints to refresh the rig.\n",
        "3) Use 'Object MinMax' to inspect value ranges for tricky channels.\n",
        "4) Save the mapping when happy.\n",
        "\nSaving:\n",
        f"- Run the operator 'Save Transfer Properties' (or rerun this script with --save-path).\n",
        f"- Suggested path: {params.get('save_path') or (output_dir / 'custom_mapping.json')}\n",
        "\nCollections:\n",
        f"- Drivers: cgt_DRIVERS{' / ' + pose_collection.name if pose_collection else ''}\n",
    ]
    text = bpy.data.texts.get("MappingHelper")
    if text is None:
        text = bpy.data.texts.new("MappingHelper")
    text.clear()
    text.write("".join(msg))


def gather_target_bone_names(mapping_path: str) -> List[str]:
    """Collect all bone names referenced in mapping (target + distance helpers) to scaffold a play rig."""
    try:
        with open(mapping_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        raise RuntimeError(f"Unable to read mapping json at {mapping_path}") from exc

    seen = set()
    names: List[str] = []
    allowed_bases = {
        "root", "torso", "chest", "head",
        "upper_arm_fk", "forearm_fk", "forearm_tweak", "hand_ik", "hand",
        "thigh_fk", "shin_fk", "shin_tweak", "foot_ik", "foot_spin_ik",
        "heel", "toe", "toe_spin"
    }

    def norm_name(name: str) -> str:
        # strip rigify-style prefixes
        for prefix in ("DEF-", "ORG-", "MCH-", "CTRL-"):
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        for suffix in (".L", ".R", "_L", "_R"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break
        return name

    for entry in data.values():
        cgt_props = entry.get("cgt_props", {})
        tgt = cgt_props.get("target", {})
        by_obj = cgt_props.get("by_obj", {})
        for name in (
            tgt.get("target_bone"),
            by_obj.get("target_bone"),
            by_obj.get("other_bone"),
        ):
            if not name or name == "NONE":
                continue
            base = norm_name(name)
            if base not in allowed_bases:
                continue
            if name in seen:
                continue
            seen.add(name)
            names.append(name)
    return names


def create_play_armature_from_mapping(mapping_path: str, name: str = "cgt_PlayRig") -> bpy.types.Object:
    """
    Build a simple humanoid-ish armature that covers all bones referenced in the mapping json.
    Known limbs are placed in a rough T-pose; unknown names are scattered nearby so enums resolve.
    """
    bone_names = gather_target_bone_names(mapping_path)
    if not bone_names:
        bone_names = ["root"]

    # Ensure we're in object mode before editing armatures
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Reuse or create the armature object
    arm_obj = bpy.data.objects.get(name)
    if arm_obj and arm_obj.type != "ARMATURE":
        raise RuntimeError(f"Object named {name} exists but is not an armature.")
    if arm_obj is None:
        arm_data = bpy.data.armatures.new(name)
        arm_obj = bpy.data.objects.new(name, arm_data)
        bpy.context.scene.collection.objects.link(arm_obj)
    arm_data = arm_obj.data

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    # Clear any existing bones
    for eb in list(arm_data.edit_bones):
        arm_data.edit_bones.remove(eb)

    # --- Build a small humanoid template ---
    def side_from_name(n: str) -> Optional[str]:
        if n.endswith((".L", "_L")):
            return "L"
        if n.endswith((".R", "_R")):
            return "R"
        return None

    def base_name(n: str) -> str:
        for prefix in ("DEF-", "ORG-", "MCH-", "CTRL-"):
            if n.startswith(prefix):
                return n[len(prefix):]
        return n

    def lr_offset(side: Optional[str], x: float) -> float:
        if side == "L":
            return abs(x)
        if side == "R":
            return -abs(x)
        return x

    allowed_bases = {
        "root", "torso", "chest", "head",
        "upper_arm_fk", "forearm_fk", "forearm_tweak", "hand_ik", "hand",
        "thigh_fk", "shin_fk", "shin_tweak", "foot_ik", "foot_spin_ik",
        "heel", "toe", "toe_spin"
    }

    def is_allowed_core(name: str) -> bool:
        base = base_name(name)
        if base.endswith((".L", ".R", "_L", "_R")):
            base = base[:-2]
        return base in allowed_bases

    def make_spec() -> Dict[str, Tuple[Vector, Vector, Optional[str]]]:
        spec: Dict[str, Tuple[Vector, Vector, Optional[str]]] = {}

        def add(name: str, head: Tuple[float, float, float], tail: Tuple[float, float, float],
                parent: Optional[str]):
            if name not in spec:
                spec[name] = (Vector(head), Vector(tail), parent)

        # Core spine
        add("root", (0.0, 0.0, 0.0), (0.0, 0.05, 0.1), None)
        add("torso", (0.0, 0.0, 0.1), (0.0, 0.0, 1.0), "root")
        add("chest", (0.0, 0.0, 1.0), (0.0, 0.0, 1.3), "torso")
        add("head", (0.0, 0.0, 1.3), (0.0, 0.0, 1.6), "chest")
        # face/jaw skipped for play rig

        # Arms
        def arm_chain(side: str):
            shoulder = (lr_offset(side, 0.2), 0.0, 1.25)
            elbow = (lr_offset(side, 0.5), 0.05, 1.05)
            wrist = (lr_offset(side, 0.65), 0.1, 0.95)
            add(f"upper_arm_fk.{side}", shoulder, (shoulder[0], shoulder[1], shoulder[2] + 0.15), "chest")
            add(f"forearm_fk.{side}", elbow, (elbow[0], elbow[1], elbow[2] - 0.1), f"upper_arm_fk.{side}")
            add(f"forearm_tweak.{side}", elbow, (elbow[0], elbow[1], elbow[2] - 0.1), f"forearm_fk.{side}")
            add(f"hand_ik.{side}", wrist, (wrist[0], wrist[1], wrist[2] - 0.05), f"forearm_fk.{side}")
            add(f"hand.{side}", wrist, (wrist[0], wrist[1], wrist[2] - 0.05), f"forearm_fk.{side}")
        arm_chain("L")
        arm_chain("R")

        # Legs
        def leg_chain(side: str):
            hip = (lr_offset(side, 0.12), 0.0, 1.0)
            knee = (lr_offset(side, 0.12), 0.05, 0.5)
            ankle = (lr_offset(side, 0.12), 0.12, 0.1)
            toe = (lr_offset(side, 0.12), 0.25, 0.05)
            add(f"thigh_fk.{side}", hip, (hip[0], hip[1], hip[2] - 0.2), "torso")
            add(f"shin_fk.{side}", knee, (knee[0], knee[1], knee[2] - 0.2), f"thigh_fk.{side}")
            add(f"shin_tweak.{side}", knee, (knee[0], knee[1], knee[2] - 0.1), f"shin_fk.{side}")
            add(f"foot_ik.{side}", ankle, (ankle[0], ankle[1], ankle[2] - 0.05), f"shin_fk.{side}")
            add(f"foot_spin_ik.{side}", ankle, (ankle[0], ankle[1] + 0.05, ankle[2]), f"foot_ik.{side}")
            add(f"heel.{side}", (ankle[0], ankle[1] - 0.05, ankle[2]), (ankle[0], ankle[1] - 0.05, ankle[2] + 0.05), f"foot_ik.{side}")
            add(f"toe.{side}", toe, (toe[0], toe[1] + 0.05, toe[2]), f"foot_ik.{side}")
            add(f"toe_spin.{side}", toe, (toe[0], toe[1] + 0.05, toe[2] + 0.02), f"foot_ik.{side}")
        leg_chain("L")
        leg_chain("R")

        return spec

    template_spec = make_spec()

    # Fill in any bones from mapping that aren't covered by the template
    def scatter_pos(index: int, name: str) -> Tuple[Vector, Vector]:
        """Deterministic scatter using a golden-angle spiral; mirror L/R on X."""
        theta = index * (math.pi * (3.0 - math.sqrt(5.0)))  # golden angle
        radius = 0.08 * math.sqrt(index + 1)
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        side = side_from_name(name)
        if side == "L":
            x = abs(x)
        elif side == "R":
            x = -abs(x)
        head = Vector((x, y, 0.2))
        tail = head + Vector((0.0, 0.0, 0.05))
        return head, tail

    for idx, bname in enumerate(bone_names):
        if bname in template_spec:
            continue
        # Use base name for positioning hints
        b = base_name(bname)
        if not is_allowed_core(bname):
            continue
        side = side_from_name(bname)
        head, tail = scatter_pos(idx, bname)
        parent = "root"
        if "forearm" in b:
            parent = f"upper_arm_fk.{side}" if side else "chest"
        elif "hand" in b:
            parent = f"forearm_fk.{side}" if side else "chest"
        elif "thigh" in b:
            parent = "root"
        elif "shin" in b:
            parent = f"thigh_fk.{side}" if side else "root"
        elif "foot" in b or "toe" in b:
            parent = f"shin_fk.{side}" if side else "root"
        elif "cheek" in b or "brow" in b or "lip" in b or "lid" in b or "head" in b:
            parent = "head"
        template_spec[bname] = (head, tail, parent)

    # Create bones from spec
    ebones: Dict[str, bpy.types.EditBone] = {}
    # Make sure root exists first
    if "root" not in template_spec:
        template_spec["root"] = (Vector((0, 0, 0)), Vector((0, 0, 0.1)), None)

    for name, (head, tail, _) in template_spec.items():
        eb = arm_data.edit_bones.new(name)
        eb.head = head
        eb.tail = tail if (tail - head).length > 1e-6 else head + Vector((0, 0, 0.05))
        ebones[name] = eb

    # Parent pass
    for name, (_, _, parent_name) in template_spec.items():
        if parent_name and parent_name in ebones:
            ebones[name].parent = ebones[parent_name]

    # Connect major pose chains so heads sit on parent tails
    def connect_chain(chain: List[str]):
        for parent_name, child_name in zip(chain, chain[1:]):
            parent = ebones.get(parent_name)
            child = ebones.get(child_name)
            if not parent or not child:
                continue
            child.head = parent.tail.copy()
            child.use_connect = True
            if (child.tail - child.head).length < 1e-6:
                child.tail = child.head + Vector((0, 0, 0.05))

    connect_chain(["root", "torso", "chest", "head"])
    for side in ("L", "R"):
        connect_chain([f"upper_arm_fk.{side}", f"forearm_fk.{side}", f"hand_ik.{side}"])
        connect_chain(["torso", f"thigh_fk.{side}", f"shin_fk.{side}", f"foot_ik.{side}"])

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


# --------------------- Args --------------------- #
def parse_args(argv: List[str]) -> Dict[str, Any]:
    defaults = dict(
        mocap_blend=os.getenv("MOCAP_BLEND_PATH"),
        base_mapping=str(BUILTIN_MAPPING),
        save_path=None,
        output_dir=None,
        mapping_name=None,
        apply_transfer=False,
        quit_after=False,
        auto_save=False,
        create_play_rig=False,
        play_rig_name="cgt_PlayRig",
    )

    flag_map = {
        "--mocap": "mocap_blend",
        "--base-mapping": "base_mapping",
        "--save-path": "save_path",
        "--mapping-name": "mapping_name",
        "--output-dir": "output_dir",
        "--apply-transfer": "apply_transfer",
        "--quit-after": "quit_after",
        "--auto-save": "auto_save",
        "--play-rig-name": "play_rig_name",
    }

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)

        if arg == "--apply-transfer":
            defaults["apply_transfer"] = True
            i += 1
            continue
        if arg == "--no-quit":
            defaults["quit_after"] = False
            i += 1
            continue
        if arg == "--quit-after":
            defaults["quit_after"] = True
            i += 1
            continue
        if arg == "--auto-save":
            defaults["auto_save"] = True
            i += 1
            continue
        if arg == "--create-play-rig":
            defaults["create_play_rig"] = True
            i += 1
            continue

        if arg in flag_map:
            if i + 1 >= len(argv):
                raise RuntimeError(f"Missing value for {arg}")
            defaults[flag_map[arg]] = argv[i + 1]
            i += 2
        else:
            i += 1

    return defaults


def resolve_output_dir(arg_dir: Optional[str]) -> pathlib.Path:
    env_dir = os.getenv("MAPPINGS_DIR")
    workspace_dir = (ADDON_ROOT.parent / "shared" / "rig_mappings").resolve()

    if arg_dir:
        target = pathlib.Path(arg_dir)
    elif env_dir:
        target = pathlib.Path(env_dir)
    elif workspace_dir.exists() or workspace_dir.parent.exists():
        target = workspace_dir
    else:
        target = pathlib.Path("/shared/rig_mappings")

    try:
        target.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # fallback to workspace location if /shared is not writable
        fallback = workspace_dir
        fallback.mkdir(parents=True, exist_ok=True)
        target = fallback
    return target


# --------------------- Main --------------------- #
def main():
    # Only parse args after Blender's "--"
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    params = parse_args(argv)

    mocap_blend = params["mocap_blend"]
    base_mapping = params["base_mapping"]
    save_path = params["save_path"]
    output_dir = resolve_output_dir(params.get("output_dir"))
    global OUTPUT_DIR
    OUTPUT_DIR = output_dir

    # derive save_path if only mapping_name was supplied or if a relative path was given
    if save_path is None and params.get("mapping_name"):
        save_path = str(output_dir / f"{params['mapping_name']}.json")
    elif save_path and not os.path.isabs(save_path):
        save_path = str((output_dir / save_path).resolve())
    params["save_path"] = save_path

    drivers_col: Optional[bpy.types.Collection] = None
    pose_col: Optional[bpy.types.Collection] = None

    if mocap_blend is None or not os.path.exists(mocap_blend):
        if base_mapping and os.path.exists(base_mapping):
            print(f"WARNING: mocap blend not found at {mocap_blend}; creating empty driver collections from mapping.")
            drivers_col, pose_col = ensure_driver_collections_from_mapping(base_mapping)
            mocap_blend = None
        else:
            raise RuntimeError(f"--mocap is required and must exist. Got: {mocap_blend}")
    else:
        if base_mapping and not os.path.exists(base_mapping):
            raise RuntimeError(f"Base mapping file not found: {base_mapping}")

    rig_obj: Optional[bpy.types.Object] = None
    if params["create_play_rig"]:
        rig_obj = create_play_armature_from_mapping(base_mapping, params["play_rig_name"])
        print(f"Created play armature: {rig_obj.name}")
    else:
        rig_obj = pick_armature()

    if not rig_obj:
        raise RuntimeError(
            "No armature found in the current scene. "
            "Use --create-play-rig to generate a simple target armature from the mapping file."
        )

    print("### Mapping Authoring Setup ###")
    print(f"Rig: {rig_obj.name}")
    mocap_label = mocap_blend if mocap_blend else "<none - synthetic drivers>"
    print(f"Mocap blend: {mocap_label}")
    print(f"Base mapping: {base_mapping}")
    print(f"Save path: {save_path or '<manual>'}")
    print(f"Output dir: {output_dir}")

    # NOTE: we no longer clear the scene or import the rig; we operate on the existing rig.

    if mocap_blend:
        drivers_col, pose_col = append_drivers_collection(mocap_blend)
        print("Driver collection:", drivers_col, "Pose collection:", pose_col)

    # Wire addon state so UI buttons work out-of-the-box
    try:
        bpy.context.scene.cgtinker_mediapipe.enum_detection_type = "POSE"
        bpy.context.scene.cgtinker_transfer.selected_driver_collection = pose_col or drivers_col
        bpy.context.scene.cgtinker_transfer.selected_rig = rig_obj
    except Exception:
        # Keep going even if UI props are unavailable in the current build
        traceback.print_exc()

    # Load base mapping to seed cgt_props and constraints
    if base_mapping:
        tf_load_object_properties.load(bpy.context.scene.objects, base_mapping, rig_obj)
        print(f"Loaded base mapping: {base_mapping}")

    # Optionally apply transfer to preview motion
    if params["apply_transfer"] and (pose_col or drivers_col):
        objs = collect_objects(pose_col or drivers_col)
        tf_transfer_management.main(objs)
        bpy.context.view_layer.update()
        print(f"Applied transfer on {len(objs)} driver objects.")

    # Authoring guide
    create_instruction_text(params, pose_col, output_dir, rig_obj)

    # Optional auto-save
    if params["auto_save"] and save_path:
        objs_for_save = [o for o in bpy.data.objects if o.get("cgt_id") == "11b1fb41-1349-4465-b3aa-78db80e8c761"]
        if not objs_for_save:
            raise RuntimeError("No objects with cgt_id found to save mapping from.")
        json_data = tf_save_object_properties.save(objs_for_save)
        pathlib.Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        json_data.save(str(save_path))
        print(f"Saved mapping to {save_path}")

    if params["quit_after"]:
        bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
