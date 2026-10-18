"""Renders short clips of the three models for the slides (PNG frames -> ffmpeg mp4).
usage: bl_video.py <out_dir> <which: quetz|horse|whale>"""
import sys, math, bpy
from mathutils import Vector
OUT, WHICH = sys.argv[1], sys.argv[2]
BG = (0.946, 0.905, 0.831, 1)   # linear value of the slide paper #FBF8F2


def common(frames, res=(1280, 720)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.render.fps = 24; sc.frame_start = 1; sc.frame_end = frames
    sc.world = sc.world or bpy.data.worlds.new("W"); sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = BG
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    return sc


def lights():
    sc = bpy.context.scene
    sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 2.6; sun.angle = 0.3
    so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-15), math.radians(40))
    fill = bpy.data.lights.new("fill", 'AREA'); fill.energy = 900; fill.size = 10
    fo = bpy.data.objects.new("Fill", fill); sc.collection.objects.link(fo); fo.location = (-6, 4, 3); fo.rotation_euler = (math.radians(65), 0, math.radians(-115))


def camera(lens=40):
    sc = bpy.context.scene
    cam = bpy.data.cameras.new("c"); cam.lens = lens
    co = bpy.data.objects.new("Cam", cam); sc.collection.objects.link(co); sc.camera = co
    return co


def track(co, target):
    tr = co.constraints.new('TRACK_TO'); tr.target = target; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'


def orbit_keys(co, center, radius, height, frames, start_deg=35, sweep=70):
    for f in (1, frames):
        a = math.radians(start_deg + (sweep if f > 1 else 0))
        co.location = (center[0] + radius * math.cos(a), center[1] + radius * math.sin(a), center[2] + height)
        co.keyframe_insert("location", frame=f)
    for fc in co.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'


if WHICH == "quetz":
    bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-claude/898a7bc2-c318-5fd4-a86f-114cc663fbd0/scratchpad/bl/quetzalcoatlus.blend")
    for o in list(bpy.data.objects):
        if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)
    sc = common(96)
    rig = bpy.data.objects["Rig"]
    rig.animation_data.action = bpy.data.actions["Flap"]
    # Flap action spans frames 1..33; loop it with a cycles modifier
    for fc in rig.animation_data.action.fcurves:
        m = fc.modifiers.new('CYCLES')
    lights(); co = camera(38)
    tgt = bpy.data.objects.new("Tgt", None); sc.collection.objects.link(tgt); tgt.location = (0, -1.0, 0.6)
    track(co, tgt)
    orbit_keys(co, (0, -1.0, 0.6), 13.5, 5.0, 96, start_deg=-60, sweep=60)
elif WHICH in ("horse", "whale"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = common(72, res=(960, 540)); sc.cycles.samples = 16
    glb = "/home/claude/museum/site/models/" + ("hippotherium_skeleton.glb" if WHICH == "horse" else "nordkaper_skeleton.glb")
    bpy.ops.import_scene.gltf(filepath=glb)
    # spin the whole import around Z via a parent empty
    pivot = bpy.data.objects.new("Pivot", None); sc.collection.objects.link(pivot)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.parent is None: o.parent = pivot
    pivot.rotation_euler = (0, 0, 0); pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, math.radians(360)); pivot.keyframe_insert("rotation_euler", frame=73)
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    lights(); co = camera(42)
    if WHICH == "horse":
        tgt = bpy.data.objects.new("Tgt", None); sc.collection.objects.link(tgt); tgt.location = (0, 0, 0.8)
        co.location = (3.2, -3.2, 1.9)
    else:
        tgt = bpy.data.objects.new("Tgt", None); sc.collection.objects.link(tgt); tgt.location = (0, 0, 1.6)
        co.location = (12, -14, 7)
    track(co, tgt)
sc.render.filepath = f"{OUT}/{WHICH}_"
bpy.ops.render.render(animation=True)
