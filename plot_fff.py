#!/usr/bin/env python3
"""Map-view diagnostics of an FFF run: strain rate, plastic strain, temperature and
surface velocity, plus which far-field plate each surface node is moving with.

usage: python plot_fff.py <run_dir> <modelname> [frame ...]   (default: all frames)
Run with the gospl env's python (needs h5py, numpy, matplotlib).
"""
import glob
import math
import os
import sys

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np

YR = 365.2422 * 86400
run_dir, model = sys.argv[1], sys.argv[2]
frames = [int(a) for a in sys.argv[3:]] or sorted(
    int(f.split(".")[-2]) for f in glob.glob(os.path.join(run_dir, f"{model}.save.*.vtkhdf")))


def read(frame):
    f = h5py.File(os.path.join(run_dir, f"{model}.save.{frame:06d}.vtkhdf"), "r")
    d = {k: f[k][()] for k in ("coordinate", "connectivity", "velocity", "temperature", "bcflag",
                               "strain-rate", "plastic strain", "time_yr")}
    return d


def eii(sr):
    xx, yy, zz, xy, xz, yz = sr.T
    m = (xx + yy + zz) / 3
    return np.sqrt(0.5 * ((xx - m) ** 2 + (yy - m) ** 2 + (zz - m) ** 2)
                   + xy ** 2 + xz ** 2 + yz ** 2)


def plate_velocities():
    """Plate velocities (m/s) from the '# plate velocities (cm/yr):' line make_fff.py writes;
    configs older than that line are the symmetric case at 5 cm/yr."""
    for line in open(os.path.join(run_dir, f"{model}.cfg")):
        if line.startswith("# plate velocities (cm/yr):"):
            vp = {}
            for tok in line.split(":", 1)[1].split("),"):
                k, xy = tok.split("(")
                vx, vy = (float(s) for s in xy.strip(" )\n").split(","))
                vp[k.strip()] = np.array([vx, vy]) / 100 / YR
            break
    else:
        u = 5.0 / math.sqrt(3) / 100 / YR
        vp = {"A": u * np.array([math.cos(math.radians(120)), math.sin(math.radians(120))]),
              "B": u * np.array([math.cos(math.radians(240)), math.sin(math.radians(240))]),
              "C": u * np.array([1.0, 0.0])}
    u = np.mean([np.hypot(*v) for v in vp.values()])
    return u, vp


for fr in frames:
    d = read(fr)
    x, c = d["coordinate"], d["connectivity"]
    t_myr = d["time_yr"][0] / 1e6
    cen = x[c].mean(axis=1)
    sr = np.log10(eii(d["strain-rate"]) + 1e-25)
    ps = d["plastic strain"]

    shallow = cen[:, 2] > -15e3           # elements in the top 15 km
    top = (d["bcflag"] & 32) > 0          # top-surface nodes (BOUNDZ1)
    xt, yt = x[top, 0] / 1e3, x[top, 1] / 1e3
    vt = d["velocity"][top, :2]

    # temperature at 20 km depth from nodes within +-6 km of it
    band = np.abs(x[:, 2] + 20e3) < 6e3

    u, vp = plate_velocities()
    labels = np.array(list(vp))
    mis = np.stack([np.hypot(*(vt - vp[k]).T) for k in labels])  # (3, ntop)
    best = mis.argmin(axis=0)
    coherent = mis.min(axis=0) < 0.25 * u
    group = np.where(coherent, best, 3)   # 3 = follows none of A, B, C

    fig, ax = plt.subplots(2, 2, figsize=(12, 11), constrained_layout=True)
    a = ax[0, 0]
    s = a.scatter(cen[shallow, 0] / 1e3, cen[shallow, 1] / 1e3, c=sr[shallow], s=6,
                  cmap="inferno", vmin=-16, vmax=-13)
    fig.colorbar(s, ax=a, label="log10 strain rate II (1/s), top 15 km")
    a = ax[0, 1]
    s = a.scatter(cen[shallow, 0] / 1e3, cen[shallow, 1] / 1e3, c=ps[shallow], s=6,
                  cmap="viridis", vmin=0, vmax=1.0)
    fig.colorbar(s, ax=a, label="plastic strain, top 15 km")
    a = ax[1, 0]
    if band.sum() > 3:
        tr = mtri.Triangulation(x[band, 0] / 1e3, x[band, 1] / 1e3)
        s = a.tripcolor(tr, d["temperature"][band] - 273, cmap="RdYlBu_r", vmin=200, vmax=1300,
                        shading="gouraud")
        fig.colorbar(s, ax=a, label="T (C) at ~20 km depth")
    a = ax[1, 1]
    cmap = matplotlib.colors.ListedColormap(["tab:blue", "tab:orange", "tab:green", "0.15"])
    a.scatter(xt, yt, c=group, cmap=cmap, vmin=-0.5, vmax=3.5, s=10)
    sk = max(1, top.sum() // 600)
    a.quiver(xt[::sk], yt[::sk], vt[::sk, 0], vt[::sk, 1], scale=30 * u, width=0.002)
    a.set_title("surface nodes by plate followed (" + ", ".join(f"{c}={k}" for c, k in zip(["blue", "orange", "green"], labels)) + ", black=none)")
    for a in ax.flat:
        a.set_aspect("equal")
        a.set_xlabel("x (km)")
        a.set_ylabel("y (km)")
    fig.suptitle(f"{model} frame {fr}: t = {t_myr:.2f} Myr, u = {u * YR * 100:.2f} cm/yr; "
                 f"surface nodes following no plate: {(group == 3).sum()}")
    out = os.path.join(run_dir, f"{model}_map_{fr:03d}.png")
    fig.savefig(out, dpi=90)
    plt.close(fig)
    print(out, f"t={t_myr:.2f} Myr", "nodes per group A,B,C,none:", np.bincount(group, minlength=4))
