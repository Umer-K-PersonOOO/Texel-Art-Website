import bpy
import logging
from pathlib import Path

from .cgt_mediapipe.cgt_mp_core import cv_stream
from .cgt_mediapipe import cgt_mp_detection_operator  # reuse get_chain pattern
from .cgt_transfer.core_transfer import tf_load_object_properties, tf_transfer_management

log = logging.getLogger(__name__)

# put this helper near the top of the file (module level)
def _rig_poll(self, obj):
    return (obj is not None) and getattr(obj, "type", None) == 'ARMATURE'


class CGT_PG_LiveMirror(bpy.types.PropertyGroup):
    driver_collection: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Drivers",
        description="Collection of driver empties/objects to transfer."
    )

    # NEW: object eyedropper for the transfer target rig (only Armatures)
    transfer_rig: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Rig (Armature)",
        description="Rig to receive the driver-based transfer.",
        poll=_rig_poll
    )

    # Default to your requested transfer config
    transfer_config: bpy.props.StringProperty(
        name="Transfer Config",
        description="Name of a config in cgt_transfer/data (without .json)",
        default="Rigify_Humanoid_DefaultFace_v0.6.1"
    )

    refresh_interval: bpy.props.IntProperty(
        name="Refresh Interval (frames)",
        description="How often to re-apply transfer drivers (0 = only once on start).",
        default=0, min=0, max=1000
    )
    detection_backend: bpy.props.EnumProperty(
        name="Stream Backend",
        items=(("0","default",""),("1","capdshow","")),
        default="0"
    )
    webcam_device: bpy.props.IntProperty(name="Webcam", default=0, min=0, max=6)
    stream_dim: bpy.props.EnumProperty(
        name="Dimensions",
        items=(("sd","720x480",""),("hd","1240x720",""),("fhd","1920x1080","")),
        default="sd"
    )
    detect_type: bpy.props.EnumProperty(
        name="Detect",
        items=(("HAND","Hands",""),("FACE","Face",""),("POSE","Pose",""),("HOLISTIC","Holistic","")),
        default="POSE"
    )
    active: bpy.props.BoolProperty(default=False)
    applied_once: bpy.props.BoolProperty(
        name="applied_once",
        default=False,
        options={'HIDDEN'},
        description="Internal flag to avoid double-apply"
    )
    
    min_tracking_confidence: bpy.props.FloatProperty(
        name="Min Tracking Confidence",
        description="Minimum confidence threshold [0..1] for detections",
        default=0.7, min=0.0, max=1.0, subtype='FACTOR'
    )


class WM_CGT_LiveMirror(bpy.types.Operator):
    bl_label = "Start Live Mirror"
    bl_idname = "wm.cgt_live_mirror"
    bl_description = "Alternate: capture → driver transfer → rig update (live)."
    _timer = None
    _chain = None
    _frame = 1
    _key_step = 1
    _ticks = 0

    def _build_stream(self, user):
        dims = {'sd': (720,480), 'hd': (1240,720), 'fhd': (1920,1080)}[user.stream_dim]
        backend = int(user.detection_backend)
        return cv_stream.Stream(
            capture_input=user.webcam_device, backend=backend,
            width=dims[0], height=dims[1]
        )

    # --- replace your _build_chain() with this ---
    def _build_chain(self, stream, user):
        # Select detector + premade chain
        from .cgt_mediapipe.cgt_mp_core import (
            mp_hand_detector, mp_face_detector, mp_pose_detector, mp_holistic_detector
        )
        from .cgt_core import cgt_core_chains
        from .cgt_core.cgt_patterns import cgt_nodes

        chain = cgt_nodes.NodeChain()
        conf = float(user.min_tracking_confidence)

        inp, tmpl = None, None
        if user.detect_type == 'HAND':
            inp = mp_hand_detector.HandDetector(stream, 1, conf)
            tmpl = cgt_core_chains.HandNodeChain()
        elif user.detect_type == 'FACE':
            inp = mp_face_detector.FaceDetector(stream, False, conf)
            tmpl = cgt_core_chains.FaceNodeChain()
        elif user.detect_type == 'POSE':
            inp = mp_pose_detector.PoseDetector(stream, 1, conf)
            tmpl = cgt_core_chains.PoseNodeChain()
        else:  # 'HOLISTIC'
            # signature: (stream, model_complexity, min_detection_confidence, refine_face_landmarks)
            inp = mp_holistic_detector.HolisticDetector(stream, 1, conf, False)
            tmpl = cgt_core_chains.HolisticNodeChainGroup()

        if inp is None or tmpl is None:
            log.error("Failed to build mediapipe chain for detect_type=%s", user.detect_type)
            return None

        chain.append(inp)
        chain.append(tmpl)
        return chain


    def _collect_objects_from_collection(self, col):
        objs = []
        def visit(c):
            objs.extend(c.objects)
            for s in c.children:
                visit(s)
        visit(col)
        return objs

    def _apply_transfer(self, live_user):
        # require rig + drivers
        if live_user.driver_collection is None or live_user.transfer_rig is None:
            return

        # default config if empty
        cfg = live_user.transfer_config or "Rigify_Humanoid_DefaultFace_v0.6.1"

        # push selections into existing transfer settings
        tf = bpy.context.scene.cgtinker_transfer
        tf.selected_driver_collection = live_user.driver_collection
        tf.selected_rig = live_user.transfer_rig
        tf.transfer_types = cfg

        # ensure OBJECT mode
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        # find a VIEW_3D area + WINDOW region to satisfy poll()
        win = bpy.context.window
        area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'), None)
        region = next((r for r in (area.regions if area else []) if r.type == 'WINDOW'), None)

        # make the rig active (some ops expect an active object)
        try:
            bpy.ops.object.select_all(action='DESELECT')
            live_user.transfer_rig.select_set(True)
            bpy.context.view_layer.objects.active = live_user.transfer_rig
        except Exception:
            pass

        override = {}
        if area and region:
            override = {'window': win, 'screen': win.screen, 'area': area, 'region': region, 'scene': bpy.context.scene}

        # run your existing operators in a valid UI context
        with bpy.context.temp_override(**override):
            if bpy.ops.button.cgt_object_load_properties.poll():
                bpy.ops.button.cgt_object_load_properties()
            if bpy.ops.button.cgt_object_apply_properties.poll():
                bpy.ops.button.cgt_object_apply_properties()



    def execute(self, context):
        live = context.scene.cgtinker_live_mirror
        if live.active:
            # stop
            live.active = False
            self._teardown(context)
            self.report({'INFO'}, "Stopped Live Mirror.")
            return {'FINISHED'}

        live.active = True
        live.applied_once = False
        self._frame = bpy.context.scene.frame_current
        self._ticks = 0

        # Build stream + chain once
        stream = self._build_stream(live)
        self._chain = self._build_chain(stream, live)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Live Mirror running.")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        live = context.scene.cgtinker_live_mirror
        if not live.active:
            return self.cancel(context)

        if event.type == "TIMER":
            self._ticks += 1

            # 1) Detection step (updates driver targets via your calculators/empties)
            data, _ = self._chain.update([], self._frame)
            if data is None:
                return self.cancel(context)

            # 2) Apply transfer drivers (once, then optionally every N frames)
            if not live.applied_once:
                self._apply_transfer(live)
                live.applied_once = True
            elif live.refresh_interval > 0 and (self._ticks % live.refresh_interval) == 0:
                self._apply_transfer(live)

            self._frame += 1  # lightweight; drivers evaluate automatically

        if event.type in {'Q', 'ESC', 'RIGHTMOUSE'}:
            return self.cancel(context)

        return {'PASS_THROUGH'}

    def _teardown(self, context):
        if self._chain:
            del self._chain
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    def cancel(self, context):
        live = context.scene.cgtinker_live_mirror
        live.active = False
        self._teardown(context)
        logging.debug("Live Mirror finished.")
        return {'FINISHED'}


class CGT_PT_LiveMirror(bpy.types.Panel):
    bl_label = "Live Mirror"
    bl_parent_id = "UI_PT_CGT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_idname = "UI_PT_CGT_LiveMirror"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT','POSE'}

    def draw(self, context):
        live = context.scene.cgtinker_live_mirror
        layout = self.layout

        box = layout.box()
        box.label(text="Capture")
        row = box.row(align=True)
        row.prop(live, "webcam_device")
        row.prop(live, "stream_dim")
        row.prop(live, "detection_backend", text="Backend")
        box.prop(live, "detect_type")
        box.prop(live, "min_tracking_confidence")  # slider you added

        box = layout.box()
        box.label(text="Transfer")
        box.prop(live, "transfer_rig")              # <- eyedropper for armature object
        box.prop(live, "driver_collection")         # collection picker
        box.prop(live, "transfer_config")           # defaults to Rigify_Humanoid_DefaultFace_v0.6.1
        box.prop(live, "refresh_interval")

        if live.active:
            layout.operator(WM_CGT_LiveMirror.bl_idname, text="Stop Live Mirror", icon='CANCEL')
        else:
            layout.operator(WM_CGT_LiveMirror.bl_idname, text="Start Live Mirror", icon='PLAY')


classes = [CGT_PG_LiveMirror, WM_CGT_LiveMirror, CGT_PT_LiveMirror]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.cgtinker_live_mirror = bpy.props.PointerProperty(type=CGT_PG_LiveMirror)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.cgtinker_live_mirror
