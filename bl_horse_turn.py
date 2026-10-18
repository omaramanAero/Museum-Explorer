import sys, bpy
exec(open('/home/claude/museum/tools/bl_foot_turn.py').read().split("sc, co = base_scene()")[0])
sc, co = base_scene()
bpy.ops.import_scene.gltf(filepath="/home/claude/museum/site/models/hippotherium_skeleton.glb")
import mathutils
xs=[]; 
for o in bpy.data.objects:
    if o.type=='MESH':
        for v in o.bound_box: xs.append(o.matrix_world @ mathutils.Vector(v))
mn=mathutils.Vector((min(v.x for v in xs),min(v.y for v in xs),min(v.z for v in xs))); mx=mathutils.Vector((max(v.x for v in xs),max(v.y for v in xs),max(v.z for v in xs)))
c=(mn+mx)/2; size=max(mx-mn); print("bbox", mn, mx, size)
orbit(sc, co, "horse", (c.x, c.y, c.z), size*1.35, 18, 24)
print("HORSE DONE")
