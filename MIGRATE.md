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

- [ ] SSH access from the laptop
- [ ] Repo cloned on the workstation
- [ ] DynEarthSol 68cc2a0 built and checked
- [ ] Laptop runs stopped at fff20 frame ?, bh20 frame ?
- [ ] Run directories copied
- [ ] Runs restarted on the workstation
- [ ] Claude memory copied
