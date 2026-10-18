"""Make quaternion keyframes sign-continuous in a GLB (fixes flips from near-180° rest bones)."""
import json, struct, sys, numpy as np
src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
f = bytearray(open(src, 'rb').read())
L = struct.unpack('<I', f[12:16])[0]; j = json.loads(f[20:20 + L]); base = 20 + L + 8
fixed = 0
for an in j.get('animations', []):
    for ch in an['channels']:
        if ch['target']['path'] != 'rotation': continue
        a = j['accessors'][an['samplers'][ch['sampler']]['output']]; bv = j['bufferViews'][a['bufferView']]
        off = base + bv['byteOffset'] + a.get('byteOffset', 0); n = a['count'] * 16
        q = np.frombuffer(bytes(f[off:off + n]), dtype=np.float32).reshape(-1, 4).copy()
        for i in range(1, len(q)):
            if np.dot(q[i], q[i - 1]) < 0: q[i] *= -1; fixed += 1
        f[off:off + n] = q.astype(np.float32).tobytes()
open(dst, 'wb').write(f); print('flipped', fixed)
