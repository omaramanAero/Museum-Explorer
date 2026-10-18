import sys, math, bpy
OUT=sys.argv[1]
def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
    sc.render.engine='CYCLES'; sc.cycles.samples=64; sc.cycles.device='CPU'; sc.cycles.use_denoising=False
    sc.render.resolution_x=1400; sc.render.resolution_y=1000; sc.render.film_transparent=True; sc.render.image_settings.color_mode='RGBA'
    sc.world=bpy.data.worlds.new("W"); sc.world.use_nodes=True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value=(0.9,0.87,0.8,1); sc.world.node_tree.nodes["Background"].inputs[1].default_value=0.8
    sun=bpy.data.lights.new("sun",'SUN'); sun.energy=2.5; sun.angle=0.3; so=bpy.data.objects.new("Sun",sun); sc.collection.objects.link(so); so.rotation_euler=(math.radians(50),math.radians(-15),math.radians(40))
    fill=bpy.data.lights.new("fill",'AREA'); fill.energy=800; fill.size=10; fo=bpy.data.objects.new("Fill",fill); sc.collection.objects.link(fo); fo.location=(-6,4,3); fo.rotation_euler=(math.radians(65),0,math.radians(-115))
    cam=bpy.data.cameras.new("c"); cam.lens=45; co=bpy.data.objects.new("Cam",cam); sc.collection.objects.link(co); sc.camera=co
    return sc, co
def shoot(glb, name, loc, rot, scale=1.0):
    sc, co = setup()
    bpy.ops.import_scene.gltf(filepath=glb)
    for o in bpy.data.objects:
        if o.type=='MESH': o.scale=(scale,scale,scale)
    co.location=loc; co.rotation_euler=rot
    sc.render.filepath=f"{OUT}/{name}.png"; bpy.ops.render.render(write_still=True)
# glTF import converts to Blender axes: model front (+Z glTF) -> -Y
shoot("/home/claude/museum/site/models/nordkaper_skeleton.glb", "r_whale", (13.5,-16.0,7.0), (math.radians(68),0,math.radians(40)))
shoot("/home/claude/museum/site/models/hippotherium_foot.glb", "r_foot", (0.62,-0.75,0.42), (math.radians(72),0,math.radians(40)))
