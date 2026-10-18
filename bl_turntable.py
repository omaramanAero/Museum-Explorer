"""Turntable frame renders of the three models (transparent PNG sequences) for animated GIF/MP4 in the slides.
usage: bl_turntable.py <out_dir>
"""
import sys, math, bpy
from mathutils import Vector
OUT = sys.argv[1]
W, H, SAMPLES = 720, 450, 28


def base_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False
    sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
    sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.87, 0.8, 1); sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 2.6; sun.angle = 0.3
    so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-15), math.radians(40))
    fill = bpy.data.lights.new("fill", 'AREA'); fill.energy = 900; fill.size = 12
    fo = bpy.data.objects.new("Fill", fill); sc.collection.objects.link(fo); fo.location = (-7, 5, 4); fo.rotation_euler = (math.radians(62), 0, math.radians(-120))
    cam = bpy.data.cameras.new("c"); cam.lens = 40
    co = bpy.data.objects.new("Cam", cam); sc.collection.objects.link(co); sc.camera = co
    return sc, co


def look_at(co, target):
    d = Vector(target) - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def orbit(sc, co, name, center, radius, elev_deg, frames, start_deg=35, per_frame=None):
    for i in range(frames):
        ang = math.radians(start_deg + 360 * i / frames); el = math.radians(elev_deg)
        co.location = (center[0] + radius * math.cos(el) * math.sin(ang), center[1] - radius * math.cos(el) * math.cos(ang), center[2] + radius * math.sin(el))
        look_at(co, center)
        if per_frame: per_frame(i)
        sc.render.filepath = f"{OUT}/{name}_{i:03d}.png"; bpy.ops.render.render(write_still=True)


# ---- pterosaur: flap once per full turn
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-claude/898a7bc2-c318-5fd4-a86f-114cc663fbd0/scratchpad/bl/quetzalcoatlus.blend")
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = False
sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 2.6; sun.angle = 0.3
so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-15), math.radians(40))
fill = bpy.data.lights.new("fill", 'AREA'); fill.energy = 900; fill.size = 12
fo = bpy.data.objects.new("Fill", fill); sc.collection.objects.link(fo); fo.location = (-7, 5, 4); fo.rotation_euler = (math.radians(62), 0, math.radians(-120))
cam = bpy.data.cameras.new("c"); cam.lens = 40
co = bpy.data.objects.new("Cam", cam); sc.collection.objects.link(co); sc.camera = co
rig = bpy.data.objects["Rig"]; rig.animation_data.action = bpy.data.actions["Flap"]
N = 32
orbit(sc, co, "quetz", (0, -1.2, 0.2), 14.5, 22, N, per_frame=lambda i: sc.frame_set(1 + i))

# ---- whale and foot turntables
for glb, name, center, radius, elev in [("/home/claude/museum/site/models/nordkaper_skeleton.glb", "whale", (0, 0, 1.9), 19, 20),
                                        ("/home/claude/museum/site/models/hippotherium_foot.glb", "foot", (0, 0, 0.22), 1.05, 15)]:
    sc, co = base_scene()
    bpy.ops.import_scene.gltf(filepath=glb)
    orbit(sc, co, name, center, radius, elev, 24)
print("TURNTABLE DONE")
