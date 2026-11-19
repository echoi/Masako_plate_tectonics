#!/usr/bin/env python3
"""Generate the DynEarthSol .cfg for an FFF triple-junction test in a rectangular box.

The configuration is rotated so that the three transforms end exactly at three box
corners: NE, NW and SW. Each wall then belongs to a single plate and drives it with
that plate's full horizontal velocity (type 6, z free):
    top plate       (between the NE and NW transforms) -> y1 (north)
    west plate      (between the NW and SW transforms) -> x0 (west)
    southeast plate (between the SW and NE transforms) -> y0 (south) and x1 (east)
There is no open wall. (An earlier version had the third transform leave through an
open south wall; the deep mantle leaked out of it, and plates driven from one side only
pivoted about vertical axes.)

The rays need NE in (0, 90), NW in (90, 180) and SW in (180, 270) deg; the rotation
maximizes the smallest margin to those limits. The junction is --near from the nearer of
the north and west walls.

Why a box: DynEarthSol's 3D slant walls (n0-n3) with gravity slide spuriously at m/yr
(type-1 walls get no support pressure, and damping_option 1 damps each Cartesian
component separately, which turns the unbalanced normal force on a slanted wall into a
tangential one). Axis-aligned walls do not have this problem.

Angles are counterclockwise from +x, in degrees. Plate velocities are scaled so the
mean pairwise rate is --rate_cm_yr.

Geometries (--geom):
  sym   120-deg sectors, plates A, B, C, all pairwise rates equal.
  bh16  Boschman & van Hinsbergen (2016) Fig. 2: plate velocities are the vertices of
        the relative motion diagram (read from the PDF's vector paths), expressed in the
        PAC frame, so a Pacific plate that forms stays at the junction. Transforms are
        parallel to the triangle's sides, as in Fig. 3B (before rotation: IZA|FAR east,
        IZA|PHO northwest, FAR|PHO south).
"""
import argparse
import math

p = argparse.ArgumentParser()
p.add_argument("--name", default="fff")
p.add_argument("--geom", choices=["sym", "bh16"], default="sym")
p.add_argument("--top", default=None, help="plate on the north wall (default: best margin)")
p.add_argument("--near", type=float, default=250e3, help="junction to the nearer of N and W walls (m)")
p.add_argument("--depth", type=float, default=120e3)
p.add_argument("--res", type=float, default=15e3)
p.add_argument("--rate_cm_yr", type=float, default=5.0, help="mean pairwise relative rate")
p.add_argument("--age_yr", type=float, default=30e6, help="lithosphere age")
p.add_argument("--tf_halfwidth", type=float, default=1.5, help="in units of res")
p.add_argument("--buffer", type=float, default=150e3,
               help="size of weak blocks at the transform ends in the corners; 0 disables")
p.add_argument("--alpha", type=float, default=3e-5, help="thermal expansivity")
p.add_argument("--min_visc", type=float, default=1e19, help="viscosity floor (Pa s)")
p.add_argument("--surf_diff", type=float, default=1e-3,
               help="surface diffusivity (m^2/s); flattens the spikes where two wall velocities meet at a corner")
p.add_argument("--max_time_yr", type=float, default=10e6)
p.add_argument("--out_dt_yr", type=float, default=0.5e6)
p.add_argument("--chkpt_every", type=int, default=1, help="write a checkpoint every N output frames")
p.add_argument("--max_steps", type=int, default=0, help="0 = unlimited")
args = p.parse_args()

def ang(v):
    return math.degrees(math.atan2(v[1], v[0]))

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])

def rot(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])

# ---- geometry before rotation: plate velocities (arbitrary units) and transform rays.
# sectors: plate -> (start ray angle, end ray angle), counterclockwise.
if args.geom == "sym":
    vel = {"A": (math.cos(math.radians(120)), math.sin(math.radians(120))),
           "B": (math.cos(math.radians(240)), math.sin(math.radians(240))),
           "C": (1.0, 0.0)}
    sectors = {"A": (-30, 90), "B": (90, 210), "C": (210, 330)}
else:
    # Fig. 2 vertices in PDF page coordinates (y down), page 3 vector paths
    pdf = {"IZA": (97.6, 99.2), "FAR": (244.2, 111.6), "PHO": (219.9, 272.6),
           "PAC": (198.4, 186.2)}
    V = {k: (x, -y) for k, (x, y) in pdf.items()}
    vel = {k: sub(V[k], V["PAC"]) for k in ("IZA", "FAR", "PHO")}
    t_if = ang(sub(V["FAR"], V["IZA"]))          # ~ -5: east
    t_ip = ang(sub(V["IZA"], V["PHO"]))          # ~ 125: northwest
    t_fp = ang(sub(V["PHO"], V["FAR"])) % 360    # ~ 261: south
    sectors = {"IZA": (t_if, t_ip), "PHO": (t_ip, t_fp), "FAR": (t_fp, t_if + 360)}

def margin(phi, top):
    """smallest distance (deg) of the rotated NE/NW/SW rays from their allowed ranges"""
    order = sorted(sectors, key=lambda k: (sectors[k][0] - sectors[top][0]) % 360)
    a = [(sectors[k][0] + phi) % 360 for k in order]      # NE, NW, SW rays
    lims = [(0, 90), (90, 180), (180, 270)]
    return min(min(t - lo, hi - t) for t, (lo, hi) in zip(a, lims)), order, a

best = max(((margin(phi / 10, k)[0], phi / 10, k) for k in ([args.top] if args.top else sectors)
            for phi in range(-1800, 1800)), key=lambda c: c[0])
mg, phi, top = best
_, (top, west, se), (ray_ne, ray_nw, ray_sw) = margin(phi, top)
assert mg > 5, f"no rotation puts the rays at three corners (best margin {mg:.1f} deg)"

vel = {k: rot(v, phi) for k, v in vel.items()}
names = list(vel)
pairs = [(names[i], names[j]) for i in range(3) for j in range(i + 1, 3)]
yr = 365.2422 * 86400
mean_rel = sum(math.hypot(*sub(vel[a], vel[b])) for a, b in pairs) / 3
scale = args.rate_cm_yr / 100 / yr / mean_rel
vel = {k: (v[0] * scale, v[1] * scale) for k, v in vel.items()}

# corners relative to the junction, for unit distance to the north wall
cot = lambda t: 1 / math.tan(math.radians(t))
dN, dE, dW = 1.0, cot(ray_ne), -cot(ray_nw)
dS = dW * math.tan(math.radians(ray_sw))
k = args.near / min(dN, dW)
dN, dE, dW, dS = dN * k, dE * k, dW * k, dS * k
H, res = args.depth, args.res
Lx, Ly = dW + dE, dN + dS
xc, yc = dW, dS

# a piecewise-rigid field with transforms parallel to the relative motions has no net flux
vt, vw, vs = vel[top], vel[west], vel[se]
flux = Lx * (vt[1] - vs[1]) + Ly * (vs[0] - vw[0])
assert abs(flux) < 1e-9 * (Lx + Ly) * max(math.hypot(*v) for v in vel.values())

# ---- velocity BCs: type 6 sets the normal and the horizontal shear component, z free
bc = [f"vbc_x0 = 6", f"vbc_val_x0 = {vw[0]:.6e}  # {west} vx", f"vbc_val_x0_l = {vw[1]:.6e}  # {west} vy",
      f"vbc_x1 = 6", f"vbc_val_x1 = {vs[0]:.6e}  # {se} vx", f"vbc_val_x1_l = {vs[1]:.6e}  # {se} vy",
      f"vbc_y0 = 6", f"vbc_val_y0 = {vs[1]:.6e}  # {se} vy", f"vbc_val_y0_l = {vs[0]:.6e}  # {se} vx",
      f"vbc_y1 = 6", f"vbc_val_y1 = {vt[1]:.6e}  # {top} vy", f"vbc_val_y1_l = {vt[0]:.6e}  # {top} vx"]

# probe points for plate_speeds.py: along each sector bisector, 60% of the way to the wall
def to_wall(t):
    c, s_ = math.cos(math.radians(t)), math.sin(math.radians(t))
    d = [(Lx - xc) / c if c > 1e-12 else math.inf, -xc / c if c < -1e-12 else math.inf,
         (Ly - yc) / s_ if s_ > 1e-12 else math.inf, -yc / s_ if s_ < -1e-12 else math.inf]
    return min(d)
probes = {}
for kk, (a, b) in ((top, (ray_ne, ray_nw)), (west, (ray_nw, ray_sw)), (se, (ray_sw, ray_ne + 360))):
    t = (a + b) / 2
    r = min(0.6 * to_wall(t), 400e3)
    probes[kk] = (xc + r * math.cos(math.radians(t)), yc + r * math.sin(math.radians(t)))

# ---- weak zones (weakzone_option 5): transforms + optional end buffers
def bounds_toward(t, x0, y0, reach):
    """x/y bounds selecting the part of a line at angle t, from (x0, y0) outward by reach."""
    c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
    xmin, xmax, ymin, ymax = 0.0, Lx, 0.0, Ly
    if abs(c) >= abs(s):
        xmin, xmax = (x0, x0 + reach) if c > 0 else (x0 - reach, x0)
    else:
        ymin, ymax = (y0, y0 + reach) if s > 0 else (y0 - reach, y0)
    return (max(xmin, 0) / Lx, min(xmax, Lx) / Lx, max(ymin, 0) / Ly, min(ymax, Ly) / Ly)

rays = [ray_ne, ray_nw, ray_sw]
seg = []  # (xc, yc, az, halfwidth[res], xmin, xmax, ymin, ymax), normalized
for t in rays:
    seg.append((xc / Lx, yc / Ly, (90 - t) % 360, args.tf_halfwidth)
               + bounds_toward(t, xc, yc, 2 * max(Lx, Ly)))
if args.buffer > 0:
    b = args.buffer
    for t, (tx, ty) in ((ray_ne, (Lx, Ly)), (ray_nw, (0.0, Ly)), (ray_sw, (0.0, 0.0))):
        seg.append((tx / Lx, ty / Ly, (90 - t) % 360, b / 2 / res)
                   + bounds_toward(t + 180, tx, ty, b))

def arr(k, fmt="{:.6g}"):
    return "[" + ", ".join(fmt.format(s[k]) for s in seg) + "]"

n = len(seg)

# Reference density for the Winkler base (ref_pressure_option 0
# uses rho0 of mattype_ref with no thermal expansion). Material 1 is never placed in the
# mesh; its rho0 is the column average of rho0*(1 - alpha*T_C) for the initial geotherm,
# so the base is in isostatic balance at t = 0.
rho0, alpha, k_th, cp = 3300.0, args.alpha, 3.3, 1000.0
kappa = k_th / (rho0 * cp)
L = math.sqrt(4 * kappa * args.age_yr * yr)
nz = 2000
rho_ref = sum(rho0 * (1 - alpha * 1300.0 * math.erf((i + 0.5) * H / nz / L))
              for i in range(nz)) / nz

vtxt = ", ".join(f"{k} ({v[0]*yr*100:.2f}, {v[1]*yr*100:.2f})" for k, v in vel.items())
rtxt = ", ".join(f"{a}-{b} {math.hypot(*sub(vel[a], vel[b]))*yr*100:.2f}" for a, b in pairs)
cfg = f"""# FFF triple junction (Boschman & van Hinsbergen 2016, Fig. 3B-C), geometry '{args.geom}'.
# Generated by make_fff.py; edit the script, not this file.
# box {Lx/1e3:.0f} x {Ly/1e3:.0f} x {H/1e3:g} km, junction at ({xc/1e3:.0f}, {yc/1e3:.0f}) km, res = {res/1e3:g} km,
# lithosphere age = {args.age_yr/1e6:g} Myr, corner buffers = {args.buffer/1e3:g} km.
# rotated by {phi:.1f} deg: top {top} (y1), west {west} (x0), southeast {se} (y0, x1);
# transforms at {ray_ne:.1f} (NE corner), {ray_nw:.1f} (NW corner), {ray_sw:.1f} (SW corner) deg.
# probe points (km): {", ".join(f"{kk} ({x/1e3:.0f}, {y/1e3:.0f})" for kk, (x, y) in probes.items())}
# plate velocities (cm/yr): {vtxt}
# pairwise rates (cm/yr): {rtxt}

[sim]
modelname = {args.name}
max_time_in_yr = {args.max_time_yr:g}
output_time_interval_in_yr = {args.out_dt_yr:g}
checkpoint_frame_interval = {args.chkpt_every}
{"max_steps = %d" % args.max_steps if args.max_steps else "#max_steps"}
is_outputting_averaged_fields = no

[mesh]
meshing_option = 1
xlength = {Lx:.3f}
ylength = {Ly:.3f}
zlength = {H:.3f}
resolution = {res:g}
quality_check_step_interval = 500
remeshing_option = 13
mmg_hausd_factor = 0.1   # help: 0.1 on top/wall ridges next to restored side walls

[control]
ref_pressure_option = 0
# find_max_vbc() ignores type-6 walls, so the inferred speed would be the 1e-12 m/s floor
# and the inertial scaling would make the plates too heavy to follow their walls.
characteristic_speed = {max(math.hypot(*v) for v in vel.values()):.4e}
surface_process_option = {1 if args.surf_diff > 0 else 0}
surface_diffusivity = {args.surf_diff:g}

[bc]
surface_temperature = 273
mantle_temperature = 1573
has_water_loading = yes
vbc_z0 = 0
vbc_z1 = 0
{chr(10).join(bc)}

[ic]
temperature_option = 0
oceanic_plate_age_in_yr = {args.age_yr:g}
weakzone_option = 5
weakzone_plstrain = 0.1
weakzone_num_segments = {n}
weakzone_segments_xcenter = {arr(0)}
weakzone_segments_ycenter = {arr(1)}
weakzone_segments_zcenter = [{", ".join(["0.5"] * n)}]
weakzone_segments_azimuth = {arr(2)}
weakzone_segments_inclination = [{", ".join(["90"] * n)}]
weakzone_segments_halfwidth = {arr(3)}
weakzone_segments_x_min = {arr(4)}
weakzone_segments_x_max = {arr(5)}
weakzone_segments_y_min = {arr(6)}
weakzone_segments_y_max = {arr(7)}
weakzone_segments_depth_min = [{", ".join(["0"] * n)}]
weakzone_segments_depth_max = [{", ".join(["1"] * n)}]

[mat]
rheology_type = elasto-visco-plastic
num_materials = 2   # 1 = reference only, never placed (see rho_ref in make_fff.py)
mattype_ref = 1
rho0 = [3300, {rho_ref:.1f}]
alpha = [{alpha:g}]
bulk_modulus = [128.2e9]
shear_modulus = [80.5e9]
visc_exponent = [3.05]
visc_coefficient = [1.25e-1]
visc_activation_energy = [3.76e5]
heat_capacity = [1000]
therm_cond = [3.3]
pls0 = [0]
pls1 = [0.1]
cohesion0 = [4e7]
cohesion1 = [4e6]
friction_angle0 = [30]
friction_angle1 = [5]
dilation_angle0 = [0]
dilation_angle1 = [0]
max_viscosity = 1e24
min_viscosity = {args.min_visc:g}
"""
with open(f"{args.name}.cfg", "w") as f:
    f.write(cfg)
print(f"wrote {args.name}.cfg ({args.geom}); box {Lx/1e3:.0f} x {Ly/1e3:.0f} km, junction"
      f" ({xc/1e3:.0f}, {yc/1e3:.0f}) km, rotated {phi:.1f} deg, top {top}, west {west},"
      f" southeast {se}; rays {ray_ne:.1f} {ray_nw:.1f} {ray_sw:.1f} (margin {mg:.1f})")
print("  velocities cm/yr:", vtxt)
print("  pairwise cm/yr:", rtxt)
