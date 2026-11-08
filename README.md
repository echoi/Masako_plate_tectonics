# Pacific plate birth at an FFF triple junction: DynEarthSol tests

Tests the physical plausibility of Boschman & van Hinsbergen (2016, Sci. Adv. 2,
e1600022, doi:10.1126/sciadv.1600022), Fig. 3: an unstable transform-transform-transform
(FFF) triple junction opens a triangular gap that three new ridges fill, giving birth to
the Pacific plate.

Stage 1 (this directory) starts directly from the FFF junction (Fig. 3B-C). The question
is not whether a gap opens (that follows from the kinematics) but how lithosphere fills
it: three localized ridges around a rigid new microplate, as the paper draws, or some
other partitioning (one ridge plus leaky transforms, distributed thinning, ...).

## Setup (`make_fff.py`)

- Rectangular box (`meshing_option = 1`), 120 km deep.
- The configuration is rotated so that the three transforms end exactly at three box
  corners (NE, NW, SW). Each wall then belongs to one plate and is driven by that
  plate's full horizontal velocity (type 6, z free): top plate on `y1`, west plate on
  `x0`, southeast plate on `y0` and `x1`. There is no open wall. The rays must fall in
  (0, 90), (90, 180) and (180, 270) deg; the rotation maximizes the smallest margin to
  those limits. The junction is `--near` (250 km) from the north and west walls. The
  script checks that the net flux through the walls is zero.
- Corner buffers: each transform end sits where two wall velocities meet. Weak 150 km
  blocks along the transforms at the three corners absorb the mismatch (`--buffer 0` to
  test). Surface diffusion (`--surf_diff`, 1e-3 m^2/s) keeps the corner nodes from
  spiking (without it the SW corner node rose 50 m/kyr). On a 200 km ridge this acts on
  a ~1 Myr timescale, so ridge relief is damped; the test is about strain localization.
- `remeshing_option = 13` restores all walls and the base, and gives material entering
  through a wall the profile recorded there.
- `control.characteristic_speed` is set to the fastest plate speed (see the
  `find_max_vbc()` issue below).
- Transforms and buffers are `weakzone_option = 5` segments (multi-segment;
  `--help` wrongly lists this as option 4).
- Single mantle material, elasto-visco-plastic, dry-olivine dislocation creep, cohesion
  40 -> 4 MPa and friction 30 -> 5 deg over plastic strain 0 -> 0.1, viscosity
  1e19-1e24 Pa s; half-space cooling for a 30 Myr plate; Winkler foundation.
- Isostatic balance: `ref_pressure_option = 0` takes the reference density from
  `mattype_ref` with no thermal expansion, so a hot column is lighter than the reference
  and the base pushes the whole model up at m/yr (and `remeshing_option` 11/13 keeps
  resetting the base, so it never settles). Material 1 is a reference-only material, never
  placed, whose `rho0` is the column-averaged density of the initial geotherm
  (3208.5 kg/m^3 for 30 Myr, 120 km).

### Why not an open wall

An earlier layout put the third transform through an open south wall (type 0). It
failed three ways: the deep mantle leaked out of that wall at m/yr (see the issues
below), which forced a remesh every ~2,000 steps and made the two plates beside it stall;
with a 1e21 Pa s viscosity floor the leak stopped, but those two plates, each pushed
from one side wall with a free southern edge, rotated rigidly about vertical axes
(~1.7 deg/Myr), so their transform slipped at 1.8 instead of 5 cm/yr. In the corner
layout all three plates follow their walls (97%, 98% and 89% and rising after 100 kyr).

## Geometries (`--geom`)

- `sym`: 120 deg sectors, equal pairwise rates (5 cm/yr). Rotated 45 deg: rays at 15,
  135, 255 deg; A on the north wall, B west, C south and east; box 1183 x 1183 km.
- `bh16`: the paper's Fig. 2. Plate velocities are the vertices of the relative motion
  diagram, read from the PDF's vector paths (page 3), expressed in the PAC frame so a
  Pacific plate that forms stays at the junction. Transforms are parallel to the
  triangle's sides, as drawn at the junction in Fig. 3B: before rotation IZA|FAR at
  -4.8 deg (east), IZA|PHO at 125.2 deg (northwest), FAR|PHO at 261.4 deg (south).
  Sectors: IZA 130, PHO 136, FAR 94 deg. Rotated by 121.7 deg: rays at 23.1, 116.9,
  246.9 deg; FAR on the north wall, IZA west, PHO south and east; box 1406 x 1080 km.
  Pairwise rates keep Fig. 2's proportions (IZA-FAR : IZA-PHO : FAR-PHO =
  4.23 : 6.10 : 4.68 cm/yr at a 5 cm/yr mean). Fig. 2 has no scale, so the absolute
  rate is an assumption.

## Usage

    python3 make_fff.py --geom bh16 --name bh20 --res 20e3 --max_time_yr 3e6 --out_dt_yr 0.1e6
    dynearthsol3d bh20.cfg
    ~/miniforge3/envs/gospl/bin/python plot_fff.py <run_dir> bh20 [frames]
    python3 plate_speeds.py <run_dir> bh20 [frames]

`plot_fff.py` makes map views of strain rate and plastic strain (top 15 km), temperature at
about 20 km depth, and colours each surface node by which far-field plate it moves with
(within 0.25 of the mean plate speed). Nodes following none of the three are candidate
new-plate material. `plate_speeds.py` compares the surface velocity at each plate's probe
point with its prescribed velocity. Both read the config header.

## Runs

`probe/` holds the open-wall probes and null tests (p5-p8, n7-n9); `corner/` the corner
layout (c1: 100 kyr, no surface diffusion; c2: 30 kyr with it).

| dir   | geom | res   | time  | notes |
|-------|------|-------|-------|-------|
| fff20 | sym  | 20 km | 3 Myr | 30 Myr plates, 150 km buffers, surf_diff 1e-3, started 2026-11-08 |
| bh20  | bh16 | 20 km | 3 Myr | same |

Both run at the same time with `OMP_NUM_THREADS=2`; dt is about 0.7 yr. 3 Myr rather
than 5 because the junction is only 250 km from the north and west walls.

## DynEarthSol issues found on the way (not fixed here)

- `--help` for `ic.weakzone_option` lists multi-segment planar zones as 4; the code
  (`ic.cxx`, `input.cxx`) uses 5, and 4 is the Gaussian planar zone.
- 3D slant walls (`n0`-`n3`, type 1) with gravity slide along the wall at about 10 m/yr
  even with all wall velocities zero. A rectangular box, meshed either way, stays below
  0.1 cm/yr. Mechanism: `apply_stress_bcs` gives type-1 walls no lithostatic support,
  so their nodes carry the full lithostatic force (~1e18 N per node at 20 km
  resolution), and `damping_option = 1` damps each Cartesian component separately.
  On an axis-aligned wall the normal force is a single component and the BC removes it;
  on a slanted wall the component-wise damping leaves a large tangential part.
- `find_max_vbc()` (`bc.cxx`) counts only odd wall types and type 4, so type-6 (and 7)
  walls are ignored. With only type-6 walls the inferred speed is the 1e-12 m/s floor,
  the inertial scaling makes the domain far too heavy, and the interior barely follows
  its walls (a uniformly translating box was still at rest beyond 100 km from the walls
  after 30 kyr). `examples/oblique-rift-3d.cfg` uses type 6 walls too. Workaround here:
  set `control.characteristic_speed` to the fastest wall speed.
- Side-wall support on open (type 0) walls is `ref_pressure()`, i.e. one density
  (`rho0` of `mattype_ref`) at all depths. With thermal expansion the cold top of the
  column is denser than that, so the interior pressure exceeds the support by 10-16 MPa at
  mid-depth and the weak mantle leaves through the open wall at 1-4 m/yr. Here that wall
  drifted 5 km in about 1,200 yr, so the run remeshed every 2,000 steps, and plates B and
  C stalled after each remesh (0-117% of their wall speed). `--alpha 0` removes the mismatch
  (temperature-dependent viscosity stays, thermal buoyancy goes), but it is not enough: a zero-velocity null test with `alpha = 0` still leaks
  0.6-0.9 m/yr at the bottom of the open wall (0.3 m/yr with a free-slip base instead of
  Winkler), probably because the facet support is evaluated at the facet centre while each element
  carries one stress, and nothing resists the residual on an open wall. At 1e19 Pa s the
  mantle creeps under it steadily. `--min_visc 1e21` cuts it to 1-2 cm/yr,
  decaying, within 150 km of the wall, with no remeshing in 10 kyr. The corner layout
  avoids open walls altogether, so the defaults are back to 3e-5 and 1e19.
- Where two type-1 walls meet, the non-PT path of `apply_vbcs` projects the velocity
  onto the shared edge (vertical for two vertical walls), so polygon corners lose their
  prescribed horizontal motion.

## Next

- Sensitivity: `--buffer 0`, plate age, transform weakness, absolute rate.
- Stage 2: the FFT -> FFF transition (Fig. 3A), which needs a 3D slab.
