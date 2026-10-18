"""Tiny glTF 2.0 (GLB) writer + procedural mesh helpers. No dependencies beyond numpy."""
import json, math, struct
import numpy as np

# ---------------------------------------------------------------- math helpers

def quat_axis_angle(axis, deg):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis)
    h = math.radians(deg) / 2
    s = math.sin(h)
    return [float(axis[0] * s), float(axis[1] * s), float(axis[2] * s), float(math.cos(h))]  # x,y,z,w


def _normalize(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    n[n == 0] = 1
    return v / n


def smooth_normals(pos, idx):
    tri = idx.reshape(-1, 3)
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    fn = np.cross(b - a, c - a)
    nrm = np.zeros_like(pos)
    for k in range(3):
        np.add.at(nrm, tri[:, k], fn)
    zero = np.linalg.norm(nrm, axis=1) < 1e-12
    if zero.any():  # pole / unused vertices: point away from the part's centre
        d = pos[zero] - pos.mean(0)
        d[np.linalg.norm(d, axis=1) < 1e-12] = (0, 1, 0)
        nrm[zero] = d
    return _normalize(nrm).astype(np.float32)


class Geo:
    """Accumulates triangles for one mesh/material."""

    def __init__(self):
        self.p, self.i = [], []
        self.n = 0

    def add(self, pos, idx):
        pos = np.asarray(pos, np.float32)
        self.p.append(pos)
        self.i.append(np.asarray(idx, np.uint32) + self.n)
        self.n += len(pos)
        return self

    def arrays(self):
        return np.concatenate(self.p), np.concatenate(self.i)

    # --- primitives -------------------------------------------------------
    def ellipsoid(self, c, r, seg=28, rings=16):
        c, r = np.asarray(c, float), np.asarray(r, float)
        pts, idx = [], []
        for j in range(rings + 1):
            v = math.pi * j / rings
            for k in range(seg + 1):
                u = 2 * math.pi * k / seg
                pts.append(c + r * [math.sin(v) * math.cos(u), math.cos(v), math.sin(v) * math.sin(u)])
        for j in range(rings):
            for k in range(seg):
                a = j * (seg + 1) + k; b = a + seg + 1
                idx += [a, a + 1, b, a + 1, b + 1, b]
        return self.add(pts, idx)

    def tube(self, path, radii, sides=14, squash=(1.0, 1.0), cap=True, up=(0, 1, 0)):
        """Swept circle along a polyline. squash scales the (side, up) axes of the cross-section."""
        path = np.asarray(path, float)
        radii = np.broadcast_to(np.asarray(radii, float), (len(path),))
        T = np.gradient(path, axis=0); T = _normalize(T)
        upv = np.asarray(up, float)
        pts, idx = [], []
        for m, (p, t, r) in enumerate(zip(path, T, radii)):
            side = np.cross(t, upv)
            if np.linalg.norm(side) < 1e-6:
                side = np.cross(t, [1, 0, 0])
            side /= np.linalg.norm(side)
            nup = np.cross(side, t)
            for k in range(sides):
                a = 2 * math.pi * k / sides
                pts.append(p + r * (math.cos(a) * side * squash[0] + math.sin(a) * nup * squash[1]))
        M = len(path)
        for m in range(M - 1):
            for k in range(sides):
                a = m * sides + k; b = m * sides + (k + 1) % sides
                c = a + sides; d = b + sides
                idx += [a, c, b, b, c, d]
        if cap:
            for end, flip in ((0, True), (M - 1, False)):
                ci = len(pts); pts.append(path[end])
                for k in range(sides):
                    a = end * sides + k; b = end * sides + (k + 1) % sides
                    idx += [ci, b, a] if flip else [ci, a, b]
        return self.add(pts, idx)

    def plate(self, poly, normal_offset=0.0):
        """Flat convex polygon (fan). Use a double-sided material."""
        poly = np.asarray(poly, float)
        idx = []
        for k in range(1, len(poly) - 1):
            idx += [0, k, k + 1]
        return self.add(poly, idx)

    def fin(self, poly_zy, x0, thick):
        """Extrude a convex polygon given in the (z, y) plane, centred at x0, with thickness."""
        poly = np.asarray(poly_zy, float); n = len(poly)
        L = np.c_[np.full(n, x0 - thick / 2), poly[:, 1], poly[:, 0]]
        R = np.c_[np.full(n, x0 + thick / 2), poly[:, 1], poly[:, 0]]
        pts = np.r_[L, R]
        idx = []
        for k in range(1, n - 1):
            idx += [0, k + 1, k, n, n + k, n + k + 1]
        for k in range(n):
            a, b = k, (k + 1) % n
            idx += [a, b, n + a, b, n + b, n + a]
        return self.add(pts, idx)


# ---------------------------------------------------------------- GLB builder

class GLB:
    def __init__(self, generator="Museum Explorer Karlsruhe procedural builder"):
        self.g = {"asset": {"version": "2.0", "generator": generator},
                  "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
                  "materials": [], "accessors": [], "bufferViews": [], "buffers": []}
        self.bin = bytearray()

    def _view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin += b"\0"
        off = len(self.bin); self.bin += data
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target: bv["target"] = target
        self.g["bufferViews"].append(bv)
        return len(self.g["bufferViews"]) - 1

    def _acc(self, arr, ctype, typ, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        v = self._view(arr.tobytes(), target)
        count = arr.shape[0]
        a = {"bufferView": v, "componentType": ctype, "count": int(count), "type": typ}
        if minmax:
            a["min"] = [float(x) for x in arr.reshape(count, -1).min(0)]
            a["max"] = [float(x) for x in arr.reshape(count, -1).max(0)]
        self.g["accessors"].append(a)
        return len(self.g["accessors"]) - 1

    def material(self, name, rgb, rough=0.8, metal=0.0, double=False, alpha=None):
        c = [int(rgb[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [(x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": lin + [1.0 if alpha is None else alpha],
                                                     "metallicFactor": metal, "roughnessFactor": rough}}
        if double: m["doubleSided"] = True
        if alpha is not None: m["alphaMode"] = "BLEND"
        self.g["materials"].append(m)
        return len(self.g["materials"]) - 1

    def mesh(self, name, prims):
        """prims: list of (Geo, material)."""
        out = []
        for geo, mat in prims:
            pos, idx = geo.arrays()
            nrm = smooth_normals(pos, idx)
            out.append({"attributes": {"POSITION": self._acc(pos.astype(np.float32), 5126, "VEC3", 34962, True),
                                       "NORMAL": self._acc(nrm, 5126, "VEC3", 34962)},
                        "indices": self._acc(idx.astype(np.uint32), 5125, "SCALAR", 34963), "material": mat})
        self.g["meshes"].append({"name": name, "primitives": out})
        return len(self.g["meshes"]) - 1

    def node(self, name, mesh=None, t=None, r=None, s=None, children=None, root=False):
        n = {"name": name}
        if mesh is not None: n["mesh"] = mesh
        if t is not None: n["translation"] = [float(x) for x in t]
        if r is not None: n["rotation"] = [float(x) for x in r]
        if s is not None: n["scale"] = [float(x) for x in s]
        if children: n["children"] = children
        self.g["nodes"].append(n)
        i = len(self.g["nodes"]) - 1
        if root: self.g["scenes"][0]["nodes"].append(i)
        return i

    def animation(self, name, channels):
        """channels: list of (node, path, times[list], values[list of lists])."""
        anim = {"name": name, "samplers": [], "channels": []}
        for node, path, times, values in channels:
            ti = self._acc(np.asarray(times, np.float32), 5126, "SCALAR", None, True)
            typ = {"rotation": "VEC4", "translation": "VEC3", "scale": "VEC3"}[path]
            vi = self._acc(np.asarray(values, np.float32), 5126, typ)
            anim["samplers"].append({"input": ti, "output": vi, "interpolation": "LINEAR"})
            anim["channels"].append({"sampler": len(anim["samplers"]) - 1, "target": {"node": node, "path": path}})
        self.g.setdefault("animations", []).append(anim)

    def save(self, path):
        while len(self.bin) % 4:
            self.bin += b"\0"
        self.g["buffers"] = [{"byteLength": len(self.bin)}]
        js = json.dumps(self.g, separators=(",", ":")).encode()
        while len(js) % 4:
            js += b" "
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        with open(path, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, total))
            f.write(struct.pack("<I4s", len(js), b"JSON")); f.write(js)
            f.write(struct.pack("<I4s", len(self.bin), b"BIN\0")); f.write(self.bin)
        return total
