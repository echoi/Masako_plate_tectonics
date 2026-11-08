#!/usr/bin/env python3
"""Mean surface velocity in 120x120 km boxes inside each plate (at the probe points in the
cfg header), vs. the prescribed plate velocity. usage: plate_speeds.py <run_dir> <model> [frames]"""
import glob, math, os, sys
import h5py, numpy as np
YR = 365.2422 * 86400
run_dir, model = sys.argv[1], sys.argv[2]
hdr = {}
for line in open(os.path.join(run_dir, f"{model}.cfg")):
    if line.startswith("# probe points (km):"):
        probes = {}
        for tok in line.split(":", 1)[1].split("),"):
            k, xy = tok.split("(")
            probes[k.strip()] = [float(q) for q in xy.strip(" )\n").split(",")]
    if line.startswith("# plate velocities (cm/yr):"):
        for tok in line.split(":", 1)[1].split("),"):
            k, xy = tok.split("(")
            hdr[k.strip()] = np.array([float(s) for s in xy.strip(" )\n").split(",")])
frames = [int(a) for a in sys.argv[3:]] or sorted(
    int(f.split(".")[-2]) for f in glob.glob(os.path.join(run_dir, f"{model}.save.*.vtkhdf")))
for fr in frames:
    f = h5py.File(os.path.join(run_dir, f"{model}.save.{fr:06d}.vtkhdf"), "r")
    x = f["coordinate"][()] / 1e3; v = f["velocity"][()] * YR * 100; b = f["bcflag"][()]
    top = (b & 32) > 0; xt, vt = x[top], v[top]
    out = [f"t={f['time_yr'][0]/1e6:.3f} Myr"]
    for k, (cx, cy) in probes.items():
        m = (abs(xt[:, 0] - cx) < 60) & (abs(xt[:, 1] - cy) < 60)
        vm = vt[m, :2].mean(axis=0)
        out.append(f"{k}: ({vm[0]:+.2f},{vm[1]:+.2f}) of ({hdr[k][0]:+.2f},{hdr[k][1]:+.2f}) = "
                   f"{np.dot(vm, hdr[k]) / np.dot(hdr[k], hdr[k]):.0%}")
    out.append(f"topo {x[top, 2].min():.1f}..{x[top, 2].max():.1f} km")
    print("  ".join(out))
