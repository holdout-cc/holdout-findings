# Usage: python repro.py <path to coder_eval checkout>   (needs pytest==8.4.1, as in test.sh)
#
# Runs the task's real verifier/test_outputs.py with pytest and scores it the way
# verifier/test.sh does (reward 1 if pytest exits 0, else 0). The only change: the
# verifier's absolute "/root/..." paths are pointed at a temp dir that stands in for
# the container's /root. In the container the agent runs as root and can write there.
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

TASK = Path(sys.argv[1]) / "tasks/samples/skillsbench/3d-scan-calc"
DENSITY = {1: 0.10, 10: 7.85, 25: 2.70, 42: 5.55, 99: 11.34}  # material_density_table.md


def solve(stl):
    """Honest solution: largest connected component, signed-volume sum, density lookup."""
    data = stl.read_bytes()
    (n,) = struct.unpack_from("<I", data, 80)
    tris = []
    for k in range(n):
        f = struct.unpack_from("<12f", data, 84 + 50 * k)
        (attr,) = struct.unpack_from("<H", data, 84 + 50 * k + 48)
        tris.append((f[3:6], f[6:9], f[9:12], attr))
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    seen = {}
    for i, t in enumerate(tris):
        for v in t[:3]:
            key = tuple(round(c, 4) for c in v)
            if key in seen:
                parent[find(i)] = find(seen[key])
            else:
                seen[key] = i
    comps = defaultdict(list)
    for i in range(n):
        comps[find(i)].append(i)
    best = (-1.0, None)
    for members in comps.values():
        vol = 0.0
        for i in members:
            (ax, ay, az), (bx, by, bz), (cx, cy, cz), _ = tris[i]
            vol += ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)
        best = max(best, (abs(vol) / 6.0, tris[members[0]][3]))
    vol, mid = best
    return {"main_part_mass": vol * DENSITY[mid], "material_id": mid}


def reward(name, answer_fn, new_stl=None):
    root = Path(tempfile.mkdtemp())  # stands in for the container's /root
    shutil.copy(TASK / "environment/scan_data.stl", root / "scan_data.stl")  # as the Dockerfile does
    if new_stl is not None:
        (root / "scan_data.stl").write_bytes(new_stl)  # agent overwrites its input
    answer = answer_fn(root)
    (root / "mass_report.json").write_text(json.dumps(answer))
    src = (TASK / "verifier/test_outputs.py").read_text()
    (root / "test_outputs.py").write_text(src.replace('"/root/', f'"{root}/'))
    rc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(root / "test_outputs.py")],
        capture_output=True, text=True,
    ).returncode
    shutil.rmtree(root)
    print(f"{name:<34} answer={json.dumps(answer)}  reward={1 if rc == 0 else 0}")


# One triangle with all-zero coordinates and attribute (material ID) 42: volume 0.
ZERO_STL = b"\0" * 80 + struct.pack("<I", 1) + struct.pack("<12f", *[0.0] * 12) + struct.pack("<H", 42)
CHEAT = {"main_part_mass": 0, "material_id": 42}

reward("no-op (empty answer)", lambda r: {})
reward("honest solution", lambda r: solve(r / "scan_data.stl"))
reward("mass 0, input untouched", lambda r: CHEAT)
reward("mass 0, scan_data.stl overwritten", lambda r: CHEAT, new_stl=ZERO_STL)
