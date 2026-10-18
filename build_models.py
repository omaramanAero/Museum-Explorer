"""Builds the three exhibit models as GLB plus a hotspots.json with anatomy anchor points.

All geometry is original (procedural), so the models carry no third-party licence.
Units are metres; +Y up, +Z = the animal's front (model-viewer faces +Z).
"""
import json, math, sys
from pathlib import Path
import numpy as np
from glb import GLB, Geo, quat_axis_angle as qa

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "../site/models")
OUT.mkdir(parents=True, exist_ok=True)
HOT = {}


def bezier(p0, p1, p2, p3, n=16):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.asarray, (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def r3(v):
    return [round(float(x), 3) for x in v]


# =========================================================== EX01 Quetzalcoatlus
def quetzalcoatlus():
    g = GLB()
    skin = g.material("skin", "#7a7266", rough=0.85)
    belly = g.material("belly", "#a39a89", rough=0.85)
    memb = g.material("membrane", "#5a4a3d", rough=0.9, double=True)
    crest = g.material("crest", "#b4442a", rough=0.6, double=True)
    beak = g.material("beak", "#d9cdb2", rough=0.5)
    eye = g.material("eye", "#14130f", rough=0.2)
    claw = g.material("claw", "#2b2620", rough=0.5)

    # ---- body (root-level)
    body = Geo().ellipsoid((0, 0, 0), (0.30, 0.30, 0.58))
    body.tube([(0, 0.02, -0.5), (0, 0.04, -0.75), (0, 0.05, -0.9)], [0.12, 0.06, 0.01], sides=10)
    chest = Geo().ellipsoid((0, -0.12, 0.12), (0.24, 0.2, 0.42))
    m_body = g.mesh("Torso", [(body, skin), (chest, belly)])

    # ---- neck (node at neck base)
    NECK_BASE = np.array([0, 0.12, 0.45])
    neck_path = bezier((0, 0, 0), (0, 0.25, 0.7), (0, 0.55, 1.4), (0, 0.62, 2.05), 18)
    neck = Geo().tube(neck_path, np.linspace(0.15, 0.085, 18), sides=14, squash=(0.85, 1.0))
    m_neck = g.mesh("Neck", [(neck, skin)])
    NECK_END = neck_path[-1]

    # ---- head (node at neck end)
    skull_path = bezier((0, 0.06, -0.22), (0, 0.10, 0.4), (0, -0.05, 1.3), (0, -0.30, 2.25), 22)
    skull_r = np.r_[np.linspace(0.16, 0.11, 6), np.linspace(0.10, 0.012, 16)]
    head = Geo().tube(skull_path, skull_r, sides=14, squash=(0.62, 1.0))
    crest_g = Geo().fin([(-0.18, 0.12), (-0.32, 0.62), (0.05, 0.42), (0.75, 0.16), (0.2, 0.1)], 0.0, 0.03)
    eyes = Geo().ellipsoid((0.085, 0.10, 0.14), (0.035, 0.035, 0.035), 12, 8).ellipsoid((-0.085, 0.10, 0.14), (0.035, 0.035, 0.035), 12, 8)
    m_head = g.mesh("Head", [(head, beak), (crest_g, crest), (eyes, eye)])

    # ---- wings: shoulder node (inner wing) -> wrist node (outer wing)
    WRIST = np.array([1.62, 0.0, 0.0])
    def wing_meshes(side):
        s = side  # +1 left (x>0), -1 right
        X = lambda p: (s * p[0], p[1], p[2])
        arm = Geo().tube([X(p) for p in [(0, 0, 0), (0.55, 0.02, 0.06), (1.1, 0.02, 0.12), (1.62, 0, 0.1)]],
                         [0.09, 0.075, 0.05, 0.045], sides=12)
        pter = Geo().tube([X(p) for p in [(1.6, 0, 0.12), (1.38, 0.0, 0.3), (1.15, 0, 0.36)]], [0.025, 0.018, 0.008], sides=8)
        fingers = Geo()
        for k, (dx, dz) in enumerate([(0.06, 0.2), (0.12, 0.18), (0.16, 0.14)]):
            fingers.tube([X((1.62, 0.02, 0.12)), X((1.62 + dx, 0.0 - 0.03 * k, 0.12 + dz))], [0.018, 0.006], sides=6)
        inner = Geo().plate([X(p) for p in [(0, 0, 0), (1.62, 0, 0.1), (1.62, 0, -1.2), (0.8, 0, -1.05), (0, 0, -0.75)]])
        prop = Geo().plate([X(p) for p in [(0.15, 0, 0.05), (1.15, 0, 0.36), (1.6, 0, 0.12), (1.1, 0, 0.12)]])
        m_inner = g.mesh(f"InnerWing_{'L' if s > 0 else 'R'}", [(arm, skin), (pter, beak), (fingers, claw), (inner, memb), (prop, memb)])
        finger = Geo().tube([X(p) for p in [(0, 0, 0.1), (1.1, 0, -0.18), (2.2, -0.02, -0.55), (3.3, -0.05, -1.0)]],
                            [0.045, 0.035, 0.022, 0.006], sides=10)
        outer = Geo().plate([X(p) for p in [(0, 0, 0.1), (3.3, -0.05, -1.0), (2.2, -0.02, -1.15), (1.1, 0, -1.3), (0, 0, -1.2)]])
        m_outer = g.mesh(f"OuterWing_{'L' if s > 0 else 'R'}", [(finger, beak), (outer, memb)])
        return m_inner, m_outer

    # ---- legs (static, trailing back in flight)
    def leg(side):
        s = side; X = lambda p: (s * p[0], p[1], p[2])
        lg = Geo().tube([X(p) for p in [(0.18, -0.1, -0.45), (0.22, -0.32, -0.95), (0.2, -0.4, -1.55), (0.2, -0.42, -1.72)]],
                        [0.07, 0.045, 0.03, 0.02], sides=10)
        toes = Geo()
        for dx in (-0.04, 0.0, 0.04):
            toes.tube([X((0.2, -0.42, -1.72)), X((0.2 + dx, -0.44, -1.86))], [0.012, 0.004], sides=6)
        return g.mesh(f"Leg_{'L' if s > 0 else 'R'}", [(lg, skin), (toes, claw)])

    n_head = g.node("Head", m_head, t=NECK_END)
    n_neck = g.node("Neck", m_neck, t=NECK_BASE, children=[n_head])
    SH = {1: np.array([0.28, 0.1, 0.3]), -1: np.array([-0.28, 0.1, 0.3])}
    wing_nodes = {}
    for s in (1, -1):
        mi, mo = wing_meshes(s)
        nw = g.node(f"Wrist_{'L' if s > 0 else 'R'}", mo, t=(s * WRIST[0], 0, 0))
        ns = g.node(f"Shoulder_{'L' if s > 0 else 'R'}", mi, t=SH[s], children=[nw])
        wing_nodes[s] = (ns, nw)
    n_legs = [g.node("Leg_L", leg(1)), g.node("Leg_R", leg(-1))]
    n_body = g.node("Torso", m_body)
    root = g.node("Quetzalcoatlus", None, t=(0, 1.2, 0),
                  children=[n_body, n_neck, wing_nodes[1][0], wing_nodes[-1][0]] + n_legs, root=True)
    ROOT = np.array([0, 1.2, 0])

    # ---- animations
    def rot(axis, degs):
        return [qa(axis, d) for d in degs]
    T = [0, 0.4, 0.8, 1.2, 1.6]
    sh = [0, 30, 0, -24, 0]
    wr = [0, -8, 14, 8, 0]
    ch = [
        (wing_nodes[1][0], "rotation", T, rot((0, 0, 1), sh)),
        (wing_nodes[-1][0], "rotation", T, rot((0, 0, 1), [-d for d in sh])),
        (wing_nodes[1][1], "rotation", T, rot((0, 0, 1), wr)),
        (wing_nodes[-1][1], "rotation", T, rot((0, 0, 1), [-d for d in wr])),
        (root, "translation", T, [r3(ROOT + (0, dy, 0)) for dy in (0, -0.14, 0, 0.12, 0)]),
        (n_head, "rotation", T, rot((1, 0, 0), [0, 3, 0, -3, 0])),
    ]
    g.animation("Flap", ch)
    T2 = [0, 1.5, 3.0, 4.5, 6.0]
    g.animation("Glide", [
        (wing_nodes[1][0], "rotation", T2, rot((0, 0, 1), [0, 4, 0, -3, 0])),
        (wing_nodes[-1][0], "rotation", T2, rot((0, 0, 1), [0, -4, 0, 3, 0])),
        (n_head, "rotation", T2, rot((0, 1, 0), [0, 14, 0, -14, 0])),
        (n_neck, "rotation", T2, rot((0, 1, 0), [0, 5, 0, -5, 0])),
        (root, "translation", T2, [r3(ROOT + (0, dy, 0)) for dy in (0, 0.06, 0, -0.06, 0)]),
    ])
    g.save(OUT / "quetzalcoatlus.glb")

    head_w = ROOT + NECK_BASE + NECK_END
    lsh = ROOT + SH[1]
    HOT["EX01"] = [
        {"id": "crest", "pos": r3(head_w + (0.02, 0.48, -0.2)), "normal": [1, 0, 0]},
        {"id": "beak", "pos": r3(head_w + (0.05, -0.08, 1.3)), "normal": [1, 0, 0]},
        {"id": "neck", "pos": r3(ROOT + NECK_BASE + neck_path[9] + (0.12, 0, 0)), "normal": [1, 0, 0]},
        {"id": "pteroid", "pos": r3(lsh + (1.25, 0.0, 0.28)), "normal": [0, 1, 0]},
        {"id": "wingfinger", "pos": r3(lsh + WRIST + (2.0, 0.02, -0.5)), "normal": [0, 1, 0]},
        {"id": "membrane", "pos": r3(lsh + (0.9, 0.0, -0.6)), "normal": [0, 1, 0]},
        {"id": "hindlimb", "pos": r3(ROOT + (0.24, -0.3, -0.95)), "normal": [1, 0, 0]},
    ]


# =========================================================== EX02 Hippotherium three-toed foot
def hippotherium_foot():
    g = GLB()
    bone = g.material("bone", "#e3d6bd", rough=0.7)
    hoof = g.material("hoof", "#9b8b6e", rough=0.6)
    side_b = g.material("side-toe", "#d6c6a6", rough=0.7)
    main = Geo()
    main.tube([(0, 0.44, 0), (0, 0.30, 0.004), (0, 0.18, 0)], [0.020, 0.016, 0.019], sides=16, squash=(1.2, 1.0))
    main.ellipsoid((0, 0.168, 0.004), (0.026, 0.018, 0.022))
    main.tube([(0, 0.16, 0.01), (0, 0.105, 0.03)], [0.017, 0.015], sides=14, squash=(1.15, 1.0))
    main.tube([(0, 0.10, 0.032), (0, 0.068, 0.046)], [0.016, 0.017], sides=14, squash=(1.15, 1.0))
    h = Geo().tube([(0, 0.064, 0.044), (0, 0.035, 0.062), (0, 0.004, 0.08)], [0.019, 0.026, 0.030], sides=18, squash=(1.1, 0.75))
    side = Geo(); sh = Geo()
    for s in (1, -1):
        side.tube([(s * 0.021, 0.40, -0.006), (s * 0.024, 0.29, -0.01), (s * 0.026, 0.19, -0.012)], [0.008, 0.007, 0.009], sides=10)
        side.tube([(s * 0.028, 0.185, -0.01), (s * 0.031, 0.14, 0.0), (s * 0.033, 0.105, 0.008)], [0.008, 0.007, 0.006], sides=10)
        sh.tube([(s * 0.033, 0.103, 0.008), (s * 0.034, 0.088, 0.016), (s * 0.034, 0.074, 0.024)], [0.008, 0.010, 0.009], sides=12, squash=(1.0, 0.8))
    m = g.mesh("Forefoot", [(main, bone), (h, hoof), (side, side_b), (sh, hoof)])
    g.node("Hippotherium forefoot", m, root=True)
    g.save(OUT / "hippotherium_foot.glb")
    HOT["EX02"] = [
        {"id": "centralhoof", "pos": [0, 0.035, 0.085], "normal": [0, 0, 1]},
        {"id": "sidetoes", "pos": [0.04, 0.09, 0.015], "normal": [1, 0, 0]},
        {"id": "cannon", "pos": [0, 0.31, 0.024], "normal": [0, 0, 1]},
        {"id": "fetlock", "pos": [0.027, 0.168, 0.01], "normal": [1, 0, 0]},
    ]


# =========================================================== EX03 Nordkaper skeleton
def nordkaper():
    g = GLB()
    bone = g.material("bone", "#e3d6bd", rough=0.75)
    dark = g.material("bone-shadow", "#c9b993", rough=0.8)
    skull = Geo()
    ros = bezier((0, 0.35, 6.55), (0, 1.25, 5.6), (0, 1.15, 4.0), (0, 0.55, 3.0), 22)
    skull.tube(ros, np.linspace(0.07, 0.24, 22), sides=12, squash=(1.8, 0.7))
    skull.ellipsoid((0, 0.45, 2.85), (0.95, 0.55, 0.55))
    skull.ellipsoid((0, 0.3, 2.5), (0.55, 0.45, 0.35))
    jaws = Geo()
    for s in (1, -1):
        jaws.tube(bezier((s * 0.75, -0.05, 2.8), (s * 1.35, -0.25, 4.0), (s * 1.0, -0.2, 5.6), (s * 0.12, 0.15, 6.45), 24),
                  np.linspace(0.13, 0.07, 24), sides=10, squash=(0.8, 1.2))
    spine = Geo(); spines = Geo()
    N = 52
    zs = np.linspace(2.25, -6.4, N)
    for k, z in enumerate(zs):
        f = k / (N - 1)
        y = 0.35 - 0.55 * f ** 1.5
        r = 0.30 * (1 - f) ** 0.6 + 0.04
        spine.tube([(0, y, z + 0.07), (0, y, z - 0.07)], r, sides=12)
        if f < 0.75:
            hgt = 0.55 * (1 - f) + 0.05
            spines.fin([(z + 0.05, y + r * 0.8), (z - 0.06, y + r * 0.8 + hgt), (z - 0.1, y + r * 0.8 + hgt), (z - 0.06, y + r * 0.8)], 0.0, 0.05)
            if 0.12 < f:
                for s in (1, -1):
                    spines.tube([(s * r * 0.8, y, z), (s * (r + 0.28 * (1 - f) + 0.05), y - 0.02, z - 0.02)], [0.035, 0.012], sides=6)
    ribs = Geo()
    for k in range(14):
        z = 2.05 - k * 0.24
        y = 0.35 - 0.55 * ((2.25 - z) / 8.65) ** 1.5
        span = 1.25 - 0.035 * k; drop = 1.75 - 0.06 * k
        for s in (1, -1):
            ribs.tube(bezier((s * 0.3, y, z), (s * span, y + 0.05, z - 0.08), (s * (span + 0.15), y - drop * 0.6, z - 0.2), (s * span * 0.62, y - drop, z - 0.35), 14),
                      np.linspace(0.06, 0.035, 14), sides=8)
    limbs = Geo()
    for s in (1, -1):
        limbs.fin([(2.05, -0.1), (1.85, 0.55), (1.45, 0.5), (1.6, -0.15)], s * 0.55, 0.06)
        limbs.tube([(s * 0.75, -0.35, 1.75), (s * 1.0, -0.75, 1.75)], [0.1, 0.08], sides=10)
        limbs.tube([(s * 1.0, -0.78, 1.75), (s * 1.12, -1.15, 1.72)], [0.07, 0.06], sides=10, squash=(1.6, 1.0))
        for j, dz in enumerate((-0.12, -0.04, 0.04, 0.12)):
            L = 0.55 - 0.08 * abs(j - 1.5)
            limbs.tube([(s * 1.12, -1.18, 1.72 + dz), (s * (1.12 + 0.12), -1.18 - L, 1.68 + dz * 1.4)], [0.04, 0.02], sides=6)
    pelvis = Geo()
    for s in (1, -1):
        pelvis.tube([(s * 0.35, -0.75, -1.4), (s * 0.42, -0.82, -1.85)], [0.035, 0.02], sides=6)
    m = g.mesh("Skeleton", [(skull, bone), (jaws, bone), (spine, bone), (spines, dark), (ribs, bone), (limbs, bone), (pelvis, dark)])
    g.node("Nordkaper skeleton", m, t=(0, 1.9, 0), root=True)
    g.save(OUT / "nordkaper_skeleton.glb")
    Y = np.array([0, 1.9, 0])
    HOT["EX03"] = [
        {"id": "rostrum", "pos": r3(Y + (0.25, 1.05, 4.8)), "normal": [0, 1, 0]},
        {"id": "mandible", "pos": r3(Y + (1.32, -0.22, 4.2)), "normal": [1, 0, 0]},
        {"id": "flipper", "pos": r3(Y + (1.2, -1.45, 1.72)), "normal": [1, 0, 0]},
        {"id": "ribs", "pos": r3(Y + (1.32, -0.6, 0.9)), "normal": [1, 0, 0]},
        {"id": "pelvis", "pos": r3(Y + (0.45, -0.8, -1.62)), "normal": [1, 0, 0]},
        {"id": "tail", "pos": r3(Y + (0.12, -0.15, -5.6)), "normal": [1, 0, 0]},
    ]


if __name__ == "__main__":
    quetzalcoatlus(); hippotherium_foot(); nordkaper()
    (OUT / "hotspots.json").write_text(json.dumps(HOT, indent=1))
    for f in sorted(OUT.glob("*.glb")):
        print(f.name, f.stat().st_size // 1024, "KB")
