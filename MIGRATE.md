# Moving to the workstation (nefertiti)

From the laptop to `nefertiti.ceri.memphis.edu` (user `echoi2`), started 2026-11-19.
The laptop has a `Host nefertiti` entry in `~/.ssh/config`. In the commands below,
`<proj>` is the project path on the workstation (for example
`~/projects/Masako_plate_tectonics`).

## 1. Code (git)

On the workstation:

    git clone https://github.com/echoi/Masako_plate_tectonics.git <proj>

## 2. DynEarthSol at the production commit

    git clone --recursive https://github.com/GeoFLAC/DynEarthSol.git ~/opt/DynEarthSol-68cc2a0
    cd ~/opt/DynEarthSol-68cc2a0
    git checkout 68cc2a0 && git submodule update --init --recursive
    make ndims=3 opt=2 openmp=1 hdf5=1 usemmg=1

It needs a C++17 compiler (the laptop used g++ 13.3), HDF5 (1.10.10 on the laptop) and
CMake for mmg; Boost is not needed (CLI11 is vendored). Check the build with `./dynearthsol3d --help`.

Python for the plots: numpy, h5py, matplotlib, scipy (conda or pip).

## 3. Running models (fff20, bh20)

1. On the laptop, right after both runs have written a new frame, stop them for good
   and note the last frame N of each (the last line of `<run>.info`; `chkpt.N` must
   exist).
2. Copy the run directories (from the laptop):

       rsync -av fff20 bh20 nefertiti:<proj>/

   Optional, about 2.3 GB of older tests: `rsync -av probe corner nefertiti:<proj>/`.
3. On the workstation, in each run directory, add the restart lines under `[sim]`
   (here for fff20 at frame N):

       sed -i '/^\[sim\]/a is_restarting = yes\nrestarting_from_modelname = fff20\nrestarting_from_frame = N' fff20.cfg

4. Launch (raise `OMP_NUM_THREADS` if the workstation has cores to spare):

       cd <proj>/fff20
       OMP_NUM_THREADS=2 nohup ~/opt/DynEarthSol-68cc2a0/dynearthsol3d fff20.cfg > fff20.restart.log 2>&1 &

   Check that the log says `restarting=yes` and that frame N+1 appears.

## 4. Claude Code context

- `CLAUDE.md` in this repo travels with git and is read automatically.
- The laptop's project memory is in
  `~/.claude/projects/-home-echoi2-projects-Masako-plate-tectonics/memory/`. Copy it to
  `~/.claude/projects/<slug>/memory/` on the workstation, where `<slug>` is the
  workstation project path with every `/` replaced by `-`.

## Status

- [x] SSH access from the laptop (2026-11-19)
- [x] Repo on the workstation: the April clone at `~/projects/Masako_plate_tectonics`,
      fast-forwarded to 88b4bc3
- [x] DynEarthSol 68cc2a0 built in `~/opt/DynEarthSol-68cc2a0`. The workstation has
      SCOTCH, which mmg picks up and DynEarthSol does not link, so mmg was configured
      with `-DUSE_SCOTCH=OFF` (as on the laptop) before `make`. fff20 frame 0 is
      bit-identical to the laptop's (only `walltime_sec` differs).
- [x] Laptop runs stopped (2026-11-19 11:05) at fff20 frame 5, bh20 frame 4
- [x] Run directories copied (674 MB)
- [x] Runs restarted on the workstation (2026-11-19 11:09) with 16 threads each, from
      `fff20/fff20.restart5.cfg` and `bh20/bh20.restart4.cfg` (the original `.cfg` plus
      the three restart lines); logs in `<run>.restart<N>.log`
- [x] Claude memory copied (same path, so same slug)
- [x] `probe/` and `corner/` outputs copied (2.4 GB)

## Speed on the workstation

128 cores. Per-step cost for fff20 at 20 km (laptop: about 44 ms with 2 threads):

| threads | ms/step |
|---------|---------|
| 2       | 26      |
| 8       | 7.6     |
| 16      | 4.2     |

At 16 threads a 0.1 Myr frame (about 230,000 steps) takes about 16 min instead of
2.75 h, so a full 3 Myr run takes about 8 h.
