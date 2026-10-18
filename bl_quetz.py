"""Builds a rigged, animated Quetzalcoatlus in Blender (bpy module) and exports GLB + hotspots.
Blender axes: head toward -Y, +Z up, wings along X. glTF export converts to Y-up (-Y -> +Z front).
Run:  /home/claude/bl/bin/python bl_quetz.py <out_dir> [render]
"""
import sys, math, json
import bpy, bmesh
from mathutils import Vector, Matrix, noise

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
RENDER = "render" in sys.argv

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'

# ------------------------------------------------------------------ skeleton (joints, metres)
J = {  # name: (x, y, z, rx, ry)   rx = half-width, ry = half-height for the skin modifier
    "tail_tip": (0, 1.05, 0.08, 0.035, 0.035),
    "hip": (0, 0.55, 0.12, 0.2, 0.22),
    "torso": (0, 0.05, 0.2, 0.25, 0.29),
    "shoulder_c": (0, -0.42, 0.24, 0.23, 0.25),
    "neck_base": (0, -0.72, 0.3, 0.19, 0.18),
    "neck1": (0, -1.4, 0.4, 0.15, 0.15),
    "neck2": (0, -2.1, 0.46, 0.13, 0.13),
    "neck3": (0, -2.75, 0.47, 0.12, 0.125),
    "occiput": (0, -3.1, 0.47, 0.13, 0.19),
    "skull": (0, -3.75, 0.43, 0.11, 0.17),
    "beak1": (0, -4.45, 0.33, 0.075, 0.105),
    "beak2": (0, -5.0, 0.22, 0.04, 0.055),
    "beak_tip": (0, -5.45, 0.13, 0.012, 0.012),
}
ARM = {  # left side; mirrored for right
    "shoulder": (0.43, -0.36, 0.2, 0.11, 0.1),
    "elbow": (0.92, -0.05, 0.14, 0.085, 0.08),
    "wrist": (1.78, -0.46, 0.1, 0.075, 0.07),
    "knuckle": (2.78, -0.56, 0.08, 0.065, 0.06),
    "ph1": (3.58, -0.3, 0.05, 0.05, 0.045),
    "ph2": (4.22, 0.1, 0.0, 0.038, 0.035),
    "ph3": (4.72, 0.6, -0.05, 0.028, 0.026),
    "tip": (5.02, 1.0, -0.1, 0.012, 0.012),
    "pteroid_tip": (1.33, -0.78, 0.12, 0.022, 0.02),
    "f1": (2.86, -0.74, 0.03, 0.018, 0.016),
    "f2": (2.92, -0.72, 0.09, 0.018, 0.016),
    "f3": (2.95, -0.66, 0.14, 0.018, 0.016),
    "hip_j": (0.3, 0.5, 0.02, 0.085, 0.085),
    "knee": (0.34, 1.2, -0.33, 0.07, 0.07),
    "ankle": (0.31, 2.0, -0.45, 0.05, 0.05),
    "foot": (0.31, 2.38, -0.5, 0.025, 0.02),
}
SPINE_EDGES = [("tail_tip", "hip"), ("hip", "torso"), ("torso", "shoulder_c"), ("shoulder_c", "neck_base"),
               ("neck_base", "neck1"), ("neck1", "neck2"), ("neck2", "neck3"), ("neck3", "occiput"),
               ("occiput", "skull"), ("skull", "beak1"), ("beak1", "beak2"), ("beak2", "beak_tip")]
ARM_EDGES = [("shoulder_c", "shoulder"), ("shoulder", "elbow"), ("elbow", "wrist"), ("wrist", "knuckle"),
             ("knuckle", "ph1"), ("ph1", "ph2"), ("ph2", "ph3"), ("ph3", "tip"), ("wrist", "pteroid_tip"),
             ("knuckle", "f1"), ("knuckle", "f2"), ("knuckle", "f3"),
             ("hip", "hip_j"), ("hip_j", "knee"), ("knee", "ankle"), ("ankle", "foot")]


def P(name, side=1):
    if name in J:
        x, y, z, *_ = J[name]; return Vector((x, y, z))
    x, y, z, *_ = ARM[name]; return Vector((side * x, y, z))


def R(name):
    return (J.get(name) or ARM[name])[3:5]


# ------------------------------------------------------------------ helpers
def new_obj(name, mesh):
    o = bpy.data.objects.new(name, mesh); sc.collection.objects.link(o); return o


def evaluated_copy(obj, name):
    """Apply the modifier stack into a fresh mesh object; removes the original."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    bpy.data.objects.remove(obj, do_unlink=True)
    me.name = name
    o = new_obj(name, me); o.name = name
    for p in me.polygons: p.use_smooth = True
    return o


def smooth(o):
    for p in o.data.polygons: p.use_smooth = True


def material(name, rgb, rough=0.7, double=False, vcol=True, spec=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if vcol:
        ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Col"
        nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
    m.use_backface_culling = not double
    return m


def srgb(hexs):
    c = [int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def lerp(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ------------------------------------------------------------------ body via skin modifier
bm = bmesh.new(); vid = {}
for n in J: vid[n] = bm.verts.new(P(n))
for s, tag in ((1, "L"), (-1, "R")):
    for n in ARM: vid[f"{n}_{tag}"] = bm.verts.new(P(n, s))
bm.verts.ensure_lookup_table()
for a, b in SPINE_EDGES: bm.edges.new((vid[a], vid[b]))
for s, tag in ((1, "L"), (-1, "R")):
    for a, b in ARM_EDGES:
        va = vid[a] if a in J else vid[f"{a}_{tag}"]
        vb = vid[b] if b in J else vid[f"{b}_{tag}"]
        bm.edges.new((va, vb))
me = bpy.data.meshes.new("BodySkel"); bm.to_mesh(me); bm.free()
body = new_obj("Body", me)
skin = body.modifiers.new("Skin", 'SKIN'); skin.use_smooth_shade = True
# radii
idx = {v.co.to_tuple(3): i for i, v in enumerate(me.vertices)}
for n in J:
    i = idx[P(n).to_tuple(3)]; me.skin_vertices[0].data[i].radius = R(n)
for s in (1, -1):
    for n in ARM:
        i = idx[P(n, s).to_tuple(3)]; me.skin_vertices[0].data[i].radius = R(n)
me.skin_vertices[0].data[idx[P("torso").to_tuple(3)]].use_root = True
sub = body.modifiers.new("Sub", 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
tex = bpy.data.textures.new("skin_noise", 'CLOUDS'); tex.noise_scale = 0.12; tex.noise_depth = 3
disp = body.modifiers.new("Disp", 'DISPLACE'); disp.texture = tex; disp.strength = 0.012; disp.mid_level = 0.5
body = evaluated_copy(body, "Body")

# ------------------------------------------------------------------ membranes
def polyline_sampler(pts):
    pts = [Vector(p) for p in pts]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg); cum = [0]
    for s in seg: cum.append(cum[-1] + s)
    def f(t):
        d = t * total
        for i in range(len(seg)):
            if d <= cum[i + 1] or i == len(seg) - 1:
                u = (d - cum[i]) / seg[i] if seg[i] else 0
                return pts[i].lerp(pts[i + 1], max(0, min(1, u)))
    return f


def grid_mesh(name, lead, trail, nu=96, nv=18, sag=0.12):
    L, T = polyline_sampler(lead), polyline_sampler(trail)
    bm = bmesh.new(); rows = []
    for i in range(nu + 1):
        t = i / nu; a, b = L(t), T(t); row = []
        for j in range(nv + 1):
            v = -0.06 + 1.06 * j / nv
            p = a.lerp(b, v)
            p.z -= sag * math.sin(math.pi * v) * (0.4 + 0.6 * math.sin(math.pi * t))
            row.append(bm.verts.new(p))
        rows.append(row)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = new_obj(name, me)
    so = o.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.03; so.offset = 0
    return evaluated_copy(o, name)


membranes = []
for s, tag in ((1, "L"), (-1, "R")):
    lead = [P(n, s) for n in ("shoulder", "elbow", "wrist", "knuckle", "ph1", "ph2", "ph3", "tip")]
    tip = P("tip", s); ank = P("ankle", s)
    lead = [Vector((s * 0.1, -0.3, 0.18))] + lead
    trail = [Vector((s * 0.1, 1.1, -0.02)), ank, Vector((s * 1.7, 2.02, -0.25)), Vector((s * 2.9, 1.85, -0.15)), Vector((s * 4.1, 1.5, -0.12)), tip]
    membranes.append(grid_mesh(f"Wing_{tag}", lead, trail))
    # propatagium: shoulder -> pteroid tip -> wrist against the arm line
    plead = [P("shoulder", s), P("pteroid_tip", s), P("wrist", s)]
    ptrail = [P("shoulder", s), P("elbow", s), P("wrist", s)]
    membranes.append(grid_mesh(f"Pro_{tag}", plead, ptrail, nu=32, nv=8, sag=0.02))

# ------------------------------------------------------------------ crest + eyes
bm = bmesh.new()
prof = [(-3.05, 0.62), (-3.2, 0.78), (-3.45, 0.98), (-3.75, 1.02), (-4.05, 0.82), (-4.25, 0.56), (-4.0, 0.5), (-3.5, 0.52), (-3.1, 0.5)]
vs = [bm.verts.new(Vector((0, y, z))) for y, z in prof]
bm.faces.new(vs)
me = bpy.data.meshes.new("Crest"); bm.to_mesh(me); bm.free()
crest = new_obj("Crest", me)
so = crest.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.07; so.offset = 0
su = crest.modifiers.new("Sub", 'SUBSURF'); su.levels = 2; su.render_levels = 2
crest = evaluated_copy(crest, "Crest")

eyes = []
for s in (1, -1):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.05)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((s * 0.1, -3.42, 0.5)))
    me = bpy.data.meshes.new("Eye"); bm.to_mesh(me); bm.free()
    e = new_obj("Eye", me); smooth(e); eyes.append(e)

# ------------------------------------------------------------------ vertex colours
C_BACK, C_BELLY, C_MOTTLE = srgb("#4f4740"), srgb("#b9a98e"), srgb("#2e2924")
C_BEAK, C_BEAK2 = srgb("#d8cdb3"), srgb("#8a7a5e")
C_MEM, C_FIBRE = srgb("#4a3a2e"), srgb("#7d6753")
C_CREST, C_CREST2 = srgb("#b4442a"), srgb("#5a1f12")


def paint(o, fn):
    me = o.data
    ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
    for i, v in enumerate(me.vertices):
        r, g, b = fn(v.co, v.normal); ca.data[i].color = (r, g, b, 1)


def body_col(co, n):
    if co.y < -3.95:   # beak keratin
        t = min(1, max(0, (-3.95 - co.y) / 1.5)); return lerp(C_BEAK2, C_BEAK, 0.3 + 0.7 * t)
    up = max(0, min(1, (n.z + 1) / 2))          # dorsal vs ventral
    base = lerp(C_BELLY, C_BACK, 0.25 + 0.75 * up)
    m = noise.noise(co * 6.0) * 0.5 + 0.5
    m2 = noise.noise(co * 18.0 + Vector((7, 3, 1))) * 0.5 + 0.5
    base = lerp(base, C_MOTTLE, 0.45 * m * up)
    base = lerp(base, C_BELLY, 0.12 * m2 * (1 - up))
    if -3.95 < co.y < -3.0 and co.z > 0.42:    # skull top warms toward the crest
        base = lerp(base, C_CREST, 0.25)
    return base


def membrane_col(co, n):
    s = 1 if co.x >= 0 else -1
    w = P("wrist", s)
    a = math.atan2(co.y - w.y, (co.x - w.x) * s)
    fib = 0.5 + 0.5 * math.sin(a * 42 + 2.5 * noise.noise(co * 1.1))
    d = (co - w).length
    fib *= min(1, d / 0.8) * (0.6 + 0.4 * (noise.noise(co * 1.3 + Vector((3, 1, 9))) * 0.5 + 0.5))
    base = lerp(C_MEM, C_FIBRE, 0.35 * fib)
    m = noise.noise(co * 3.0) * 0.5 + 0.5
    return lerp(base, C_MOTTLE, 0.25 * m)


def crest_col(co, n):
    t = max(0, min(1, (co.z - 0.5) / 0.55))
    return lerp(C_CREST2, C_CREST, 0.2 + 0.8 * t)


paint(body, body_col)
for m in membranes: paint(m, membrane_col)
paint(crest, crest_col)
for e in eyes: paint(e, lambda co, n: srgb("#120f0c"))

mat_body = material("skin", (0.5, 0.45, 0.4), 0.72)
mat_mem = material("membrane", (0.3, 0.25, 0.2), 0.85, double=True)
mat_crest = material("crest", (0.6, 0.2, 0.1), 0.55, double=True)
mat_eye = material("eye", (0.02, 0.02, 0.02), 0.15, vcol=False, spec=0.8)
body.data.materials.append(mat_body)
for m in membranes: m.data.materials.append(mat_mem)
crest.data.materials.append(mat_crest)
for e in eyes: e.data.materials.append(mat_eye)

# ------------------------------------------------------------------ armature
BONES = [  # name, head, tail, parent
    ("spine", P("hip"), P("shoulder_c"), None),
    ("tail", P("hip"), P("tail_tip"), "spine"),
    ("neck1", P("shoulder_c"), P("neck1"), "spine"),
    ("neck2", P("neck1"), P("neck2"), "neck1"),
    ("neck3", P("neck2"), P("neck3"), "neck2"),
    ("head", P("neck3"), P("skull"), "neck3"),
    ("beak", P("skull"), P("beak_tip"), "head"),
]
for s, t in ((1, "L"), (-1, "R")):
    BONES += [
        (f"humerus_{t}", P("shoulder_c") + Vector((s * 0.2, 0.06, -0.04)), P("elbow", s), "spine"),
        (f"radius_{t}", P("elbow", s), P("wrist", s), f"humerus_{t}"),
        (f"metacarpal_{t}", P("wrist", s), P("knuckle", s), f"radius_{t}"),
        (f"ph1_{t}", P("knuckle", s), P("ph1", s), f"metacarpal_{t}"),
        (f"ph2_{t}", P("ph1", s), P("ph2", s), f"ph1_{t}"),
        (f"ph3_{t}", P("ph2", s), P("ph3", s), f"ph2_{t}"),
        (f"ph4_{t}", P("ph3", s), P("tip", s), f"ph3_{t}"),
        (f"pteroid_{t}", P("wrist", s), P("pteroid_tip", s), f"radius_{t}"),
        (f"femur_{t}", P("hip") + Vector((s * 0.15, 0, -0.08)), P("knee", s), "spine"),
        (f"tibia_{t}", P("knee", s), P("ankle", s), f"femur_{t}"),
        (f"foot_{t}", P("ankle", s), P("foot", s), f"tibia_{t}"),
    ]
arm_data = bpy.data.armatures.new("Rig"); rig = new_obj("Rig", arm_data)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = {}
for name, h, t, par in BONES:
    b = arm_data.edit_bones.new(name); b.head = h; b.tail = t; eb[name] = b
    if par: b.parent = eb[par]; b.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
BONE_SEG = {name: (Vector(h), Vector(t)) for name, h, t, _ in BONES}


def seg_dist(p, a, b):
    ab = b - a; L2 = ab.length_squared
    u = 0 if L2 == 0 else max(0, min(1, (p - a).dot(ab) / L2))
    return (p - (a + ab * u)).length


def weight(o, candidates, power=4.0, k=3):
    groups = {n: o.vertex_groups.new(name=n) for n in candidates}
    segs = [(n, BONE_SEG[n]) for n in candidates]
    for v in o.data.vertices:
        ds = sorted(((seg_dist(v.co, a, b) + 0.02, n) for n, (a, b) in segs))[:k]
        ws = [(1 / d ** power, n) for d, n in ds]; tot = sum(w for w, _ in ws)
        for w, n in ws:
            if w / tot > 0.01: groups[n].add([v.index], w / tot, 'REPLACE')
    mod = o.modifiers.new("Arm", 'ARMATURE'); mod.object = rig
    o.parent = rig


ALL = [n for n, *_ in BONES]
weight(body, ALL)
def interp_y(pts, x):
    pts = sorted(((abs(p.x), p.y) for p in pts))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1 or (x1, y1) == pts[-1]:
            u = 0 if x1 == x0 else max(0, min(1, (x - x0) / (x1 - x0))); return y0 + (y1 - y0) * u
    return pts[-1][1]


def membrane_weight(o, side, lead_pts, trail_pts, with_leg=True):
    s = 1 if side == "L" else -1
    chain = [f"humerus_{side}", f"radius_{side}", f"metacarpal_{side}", f"ph1_{side}", f"ph2_{side}", f"ph3_{side}", f"ph4_{side}"]
    spans = [(abs(BONE_SEG[n][0].x), abs(BONE_SEG[n][1].x)) for n in chain]
    names = chain + [f"tibia_{side}", "spine"]
    groups = {n: o.vertex_groups.new(name=n) for n in names}
    for v in o.data.vertices:
        x = abs(v.co.x)
        yl, yt = interp_y(lead_pts, x), interp_y(trail_pts, x)
        chord = max(0.0, min(1.0, (v.co.y - yl) / (yt - yl))) if yt > yl else 0.0
        w = {}
        for n, (x0, x1) in zip(chain, spans):          # linear blend over 0.25 m around each joint
            f = 0.25
            wa = max(0.0, min(1.0, (x - (x0 - f)) / (2 * f))) if n != chain[0] else 1.0
            wb = max(0.0, min(1.0, ((x1 + f) - x) / (2 * f))) if n != chain[-1] else 1.0
            ww = min(wa, wb)
            if ww > 0: w[n] = ww
        tot = sum(w.values()) or 1.0
        w = {n: ww / tot for n, ww in w.items()}
        if with_leg:
            leg = max(0.0, 1 - x / 1.0) * chord ** 1.5
            root = max(0.0, 1 - x / 0.3) * (1 - chord)
            keep = max(0.0, 1 - leg - root)
            w = {n: ww * keep for n, ww in w.items()}
            if leg > 0.01: w[f"tibia_{side}"] = leg
            if root > 0.01: w["spine"] = root
        for n, ww in w.items():
            if ww > 0.005: groups[n].add([v.index], ww, 'REPLACE')
    mod = o.modifiers.new("Arm", 'ARMATURE'); mod.object = rig
    o.parent = rig


for m in membranes:
    side = "L" if "_L" in m.name else "R"
    s = 1 if side == "L" else -1
    if m.name.startswith("Wing"):
        lead = [Vector((s * 0.1, -0.3, 0.18))] + [P(n, s) for n in ("shoulder", "elbow", "wrist", "knuckle", "ph1", "ph2", "ph3", "tip")]
        trail = [Vector((s * 0.1, 1.1, -0.02)), P("ankle", s), Vector((s * 1.7, 2.02, -0.25)), Vector((s * 2.9, 1.85, -0.15)), Vector((s * 4.1, 1.5, -0.12)), P("tip", s)]
        membrane_weight(m, side, lead, trail, True)
    else:
        membrane_weight(m, side, [P("shoulder", s), P("pteroid_tip", s), P("wrist", s)], [P("shoulder", s), P("elbow", s), P("wrist", s)], False)
weight(crest, ["head"]);
for e in eyes: weight(e, ["head"])

# ------------------------------------------------------------------ animations
rig.rotation_mode = 'XYZ'
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
rest = {b.name: b.matrix_local.to_3x3() for b in arm_data.bones}


def set_rot(name, axis, deg):
    pb = rig.pose.bones[name]
    Rw = Matrix.Rotation(math.radians(deg), 3, axis)
    par = arm_data.bones[name].parent
    # express the world-axis rotation in the bone's own rest frame
    M = rest[name]
    pb.rotation_quaternion = (M.inverted() @ Rw @ M).to_quaternion()


def key(name, frame):
    rig.pose.bones[name].keyframe_insert("rotation_quaternion", frame=frame)


def make_action(label, frames, poser):
    act = bpy.data.actions.new(label)
    rig.animation_data_create(); rig.animation_data.action = act
    for f, phase in frames:
        for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0)
        poser(phase)
        for pb in rig.pose.bones: key(pb.name, f)
    act.frame_range = (frames[0][0], frames[-1][0])
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
    rig.animation_data.action = None
    tr = rig.animation_data.nla_tracks.new(); tr.name = label
    st = tr.strips.new(label, int(frames[0][0]), act); st.name = label
    return act


def flap_pose(ph):   # ph in [0, 2pi)
    up = math.sin(ph)
    for s, t in ((1, "L"), (-1, "R")):
        set_rot(f"humerus_{t}", 'Y', -s * 26 * up)
        set_rot(f"radius_{t}", 'Y', -s * 6 * math.sin(ph - 0.5))
        set_rot(f"metacarpal_{t}", 'Y', -s * 7 * math.sin(ph - 0.9))
        set_rot(f"ph1_{t}", 'Y', -s * 8 * math.sin(ph - 1.3))
        set_rot(f"ph2_{t}", 'Y', -s * 9 * math.sin(ph - 1.6))
        set_rot(f"ph3_{t}", 'Y', -s * 9 * math.sin(ph - 1.9))
        set_rot(f"femur_{t}", 'X', 3 * up)
    set_rot("neck2", 'X', 2 * up); set_rot("head", 'X', -2.5 * up)
    set_rot("spine", 'X', 1.5 * math.sin(ph - 1.0))


def glide_pose(ph):
    for s, t in ((1, "L"), (-1, "R")):
        set_rot(f"humerus_{t}", 'Y', -s * 4 * math.sin(ph))
        set_rot(f"ph2_{t}", 'Y', -s * 5 * math.sin(ph + 1.2))
        set_rot(f"ph3_{t}", 'Y', -s * 6 * math.sin(ph + 1.5))
    set_rot("neck1", 'Z', 6 * math.sin(ph * 0.5)); set_rot("neck2", 'Z', 6 * math.sin(ph * 0.5))
    set_rot("head", 'Z', 10 * math.sin(ph * 0.5 + 0.4)); set_rot("spine", 'Z', 2 * math.sin(ph * 0.5))


sc.render.fps = 24
N = 8
make_action("Flap", [(1 + i * 4, 2 * math.pi * i / N) for i in range(N + 1)], flap_pose)          # 32 frames = 1.33 s
make_action("Glide", [(1 + i * 18, 2 * math.pi * i / N) for i in range(N + 1)], glide_pose)      # 144 frames = 6 s
sc.frame_start = 1; sc.frame_end = 1 + N * 18
for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0)

# ------------------------------------------------------------------ export
for o in bpy.data.objects: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=f"{OUT}/quetzalcoatlus.glb", export_format='GLB', export_apply=True,
                          export_yup=True, export_animations=True, export_animation_mode='NLA_TRACKS',
                          export_skins=True, export_vertex_color='ACTIVE', export_all_vertex_colors=False,
                          export_force_sampling=True, export_frame_step=2, export_optimize_animation_size=True,
                          export_texcoords=False, export_normals=True, use_selection=True)


def g(v): return [round(v.x, 3), round(v.z, 3), round(-v.y, 3)]  # Blender -> glTF


HOT = [
    {"id": "crest", "pos": g(Vector((0.04, -3.65, 0.98))), "normal": [1, 0, 0]},
    {"id": "beak", "pos": g(Vector((0.07, -4.75, 0.3))), "normal": [1, 0, 0]},
    {"id": "neck", "pos": g(Vector((0.14, -2.1, 0.5))), "normal": [1, 0, 0]},
    {"id": "pteroid", "pos": g(Vector((1.5, -0.62, 0.15))), "normal": [0, 0, 1]},
    {"id": "wingfinger", "pos": g(Vector((3.9, -0.1, 0.1))), "normal": [0, 0, 1]},
    {"id": "membrane", "pos": g(Vector((2.6, 0.9, -0.05))), "normal": [0, 0, 1]},
    {"id": "hindlimb", "pos": g(Vector((0.4, 1.25, -0.3))), "normal": [1, 0, 0]},
]
json.dump(HOT, open(f"{OUT}/quetz_hotspots.json", "w"))
tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == 'MESH' for p in o.data.polygons)
print("triangles", tris)

# ------------------------------------------------------------------ review / hero renders
if RENDER:
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False
    sc.render.resolution_x = 1600; sc.render.resolution_y = 1000
    sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
    sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.87, 0.8, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 2.8; sun.angle = 0.25
    so = new_obj("Sun", sun); so.rotation_euler = (math.radians(48), math.radians(-18), math.radians(35))
    fill = bpy.data.lights.new("fill", 'AREA'); fill.energy = 1200; fill.size = 10; fill.color = (0.9, 0.95, 1.0)
    fo = new_obj("Fill", fill); fo.location = (-7, 4, 3); fo.rotation_euler = (math.radians(65), 0, math.radians(-115))
    cam = bpy.data.cameras.new("c"); cam.lens = 38
    co = new_obj("Cam", cam); sc.camera = co
    flap = bpy.data.actions["Flap"]; glide = bpy.data.actions["Glide"]
    views = {"q_hero": ((9.2, -12.6, 5.8), (math.radians(67), 0, math.radians(36)), flap, 7),
             "q_hero_glide": ((8.6, -11.8, 6.4), (math.radians(63), 0, math.radians(36)), glide, 1),
             "q_top": ((0.4, -1.6, 14.5), (math.radians(2), 0, 0), glide, 1),
             "q_front": ((1.2, -13.5, 2.0), (math.radians(84), 0, math.radians(5)), flap, 7),
             "q_head": ((2.4, -6.4, 1.7), (math.radians(78), 0, math.radians(31)), glide, 1)}
    for name, (loc, rot, act, fr) in views.items():
        rig.animation_data.action = act; sc.frame_set(fr)
        co.location = loc; co.rotation_euler = rot
        sc.render.filepath = f"{OUT}/{name}.png"; bpy.ops.render.render(write_still=True)
    rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/quetzalcoatlus.blend")
