"""Hippotherium primigenium: a complete mounted three-toed horse skeleton (stylised), as shown at SMNK.
Units metres; +Y up, +Z front (head). Output: site/models/hippotherium_skeleton.glb + hotspots.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from glb import GLB, Geo

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "../site/models")
g = GLB()
bone = g.material("bone", "#e6dcc4", rough=0.72)
dark = g.material("bone-shadow", "#cdbf9e", rough=0.8)
tooth = g.material("tooth", "#f0e9d6", rough=0.5)


def bez(p0, p1, p2, p3, n=16):
    t = np.linspace(0, 1, n)[:, None]; p0, p1, p2, p3 = map(np.asarray, (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


# ---------------------------------------------------------------- spine: neck + back + tail (withers ~1.25 m)
spine = Geo(); proc = Geo()
# path from tail tip to skull base
path = np.vstack([
    bez((0, 1.05, -1.25), (0, 1.15, -1.0), (0, 1.18, -0.85), (0, 1.2, -0.7), 8),       # tail
    bez((0, 1.2, -0.7), (0, 1.24, -0.3), (0, 1.26, 0.15), (0, 1.3, 0.35), 14),          # back to withers
    bez((0, 1.3, 0.35), (0, 1.4, 0.55), (0, 1.55, 0.72), (0, 1.62, 0.88), 10),          # neck
])
path = np.array([p for i, p in enumerate(path) if i == 0 or np.linalg.norm(p - path[i - 1]) > 1e-6])
for i in range(len(path) - 1):
    a, b = path[i], path[i + 1]
    r = 0.045 if 7 < i < 24 else 0.03
    spine.tube([a + (0, 0, 0.0), b], r, sides=10)
    if 8 <= i < 30:   # neural spines, tallest at withers
        h = 0.16 if 20 <= i < 25 else 0.09
        proc.tube([a, a + (0, h, -0.02)], [0.014, 0.008], sides=6)
# ribs (18 pairs)
ribs = Geo()
for k in range(16):
    z = 0.3 - k * 0.055
    y0 = 1.25 - 0.01 * k
    drop = 0.55 + 0.12 * math.sin(math.pi * k / 15)
    span = 0.18 + 0.06 * math.sin(math.pi * k / 15)
    for s in (1, -1):
        ribs.tube(bez((s * 0.04, y0, z), (s * span, y0 - 0.08, z - 0.02), (s * (span + 0.02), y0 - drop * 0.6, z - 0.06), (s * span * 0.55, y0 - drop, z - 0.1), 12),
                  np.linspace(0.016, 0.011, 12), sides=7)
sternum = Geo().tube([(0, 0.62, 0.32), (0, 0.58, 0.1), (0, 0.6, -0.1)], 0.02, sides=7)
pelvis = Geo()
for s in (1, -1):
    pelvis.fin([(-0.95, 1.12), (-0.62, 1.2), (-0.55, 1.0), (-0.72, 0.86), (-0.9, 0.92)], s * 0.09, 0.035)
scap = Geo()
for s in (1, -1):
    scap.fin([(0.42, 1.25), (0.25, 1.05), (0.33, 0.9), (0.5, 1.02)], s * 0.14, 0.03)

# ---------------------------------------------------------------- skull
skull = Geo()
skull.ellipsoid((0, 1.62, 0.95), (0.1, 0.11, 0.14))                       # braincase
sk_path = bez((0, 1.62, 1.0), (0, 1.56, 1.16), (0, 1.42, 1.3), (0, 1.3, 1.42), 12)
skull.tube(sk_path, np.linspace(0.1, 0.06, 12), sides=12, squash=(1.05, 1.1))   # rostrum (down-angled, grazing)
jaw = Geo().tube(bez((0, 1.52, 0.98), (0, 1.44, 1.12), (0, 1.32, 1.26), (0, 1.24, 1.4), 12), np.linspace(0.05, 0.035, 12), sides=10, squash=(1.1, 0.8))
for s in (1, -1):
    skull.ellipsoid((s * 0.085, 1.58, 1.08), (0.028, 0.03, 0.03), 10, 6)  # orbits
teeth = Geo()
for i in range(6):
    z = 1.14 + i * 0.04
    for s in (1, -1):
        teeth.tube([(s * 0.045, 1.37 - 0.012 * i, z), (s * 0.045, 1.33 - 0.012 * i, z)], 0.012, sides=6)

# ---------------------------------------------------------------- legs, each with three toes (digit III largest)
legs = Geo(); toes = Geo()


def leg(x, z_top, y_top, front):
    # upper (femur / humerus), lower (tibia / radius), cannon (metapodial III), pastern, hoof
    if front:
        pts = [(x, y_top, z_top), (x, 0.78, z_top - 0.05), (x, 0.45, z_top + 0.02), (x, 0.16, z_top + 0.04), (x, 0.07, z_top + 0.08)]
    else:
        pts = [(x, y_top, z_top), (x, 0.8, z_top + 0.18), (x, 0.42, z_top - 0.02), (x, 0.15, z_top + 0.04), (x, 0.07, z_top + 0.08)]
    radii = [0.045, 0.035, 0.028, 0.022, 0.02]
    for i in range(len(pts) - 1):
        legs.tube([pts[i], pts[i + 1]], [radii[i], radii[i + 1]], sides=10)
        legs.ellipsoid(pts[i + 1], (radii[i + 1] * 1.4, radii[i + 1] * 1.1, radii[i + 1] * 1.4), 10, 6)
    # three toes: central hoof + two side toes set higher
    fx, fy, fz = pts[-1]
    toes.tube([(fx, fy, fz), (fx, 0.0, fz + 0.06)], [0.022, 0.03], sides=10, squash=(1.1, 0.8))
    for s in (1, -1):
        toes.tube([(fx + s * 0.028, 0.2, fz - 0.01), (fx + s * 0.04, 0.09, fz + 0.01), (fx + s * 0.045, 0.045, fz + 0.03)], [0.011, 0.01, 0.012], sides=7)
    return pts


for s in (1, -1):
    leg(s * 0.13, 0.28, 1.02, True)       # forelimbs from the shoulder
    leg(s * 0.12, -0.78, 1.0, False)      # hindlimbs from the hip
# stand / base plate like a museum mount
base = Geo().plate([(-0.38, -0.02, 1.6), (0.38, -0.02, 1.6), (0.38, -0.02, -1.35), (-0.38, -0.02, -1.35)])
base_mat = g.material("base", "#9a917f", rough=0.9, double=True)
rods = Geo()
for z in (0.25, -0.75):
    rods.tube([(0, -0.02, z), (0, 0.9, z)], 0.012, sides=6)

m = g.mesh("Skeleton", [(spine, bone), (proc, dark), (ribs, bone), (sternum, dark), (pelvis, dark), (scap, dark), (skull, bone), (jaw, bone), (teeth, tooth), (legs, bone), (toes, bone)])
m2 = g.mesh("Mount", [(base, base_mat), (rods, base_mat)])
g.node("Hippotherium skeleton", m, root=True)
g.node("Mount", m2, root=True)
g.save(OUT / "hippotherium_skeleton.glb")
HOT = [
    {"id": "skull", "pos": [0.1, 1.55, 1.1], "normal": [1, 0, 0]},
    {"id": "teeth", "pos": [0.06, 1.32, 1.3], "normal": [1, 0, 0]},
    {"id": "threetoes", "pos": [0.19, 0.08, 0.36], "normal": [1, 0, 0]},
    {"id": "cannon", "pos": [0.17, 0.3, 0.3], "normal": [1, 0, 0]},
    {"id": "spine", "pos": [0.05, 1.42, 0.0], "normal": [0, 1, 0]},
    {"id": "hindlimb", "pos": [0.17, 0.62, -0.68], "normal": [1, 0, 0]},
]
hp = OUT / "hotspots.json"
h = json.loads(hp.read_text()) if hp.exists() else {}
h["EX02"] = HOT
hp.write_text(json.dumps(h, indent=1))
print("ok", (OUT / "hippotherium_skeleton.glb").stat().st_size // 1024, "KB")
