# Notes for Claude Code

Read `README.md` first: it has the science question, the setup, and the DynEarthSol
issues found so far. This file holds working rules and current state.

## Working rules

- "Pause" a run means `kill -STOP <pid>` (resume with `kill -CONT <pid>`). Never kill a
  run unless the user explicitly says to stop it for good.
- Before stopping a run for good, wait until it has just written a frame (new
  `<run>.chkpt.N.vtkhdf`), so little work is lost.
- Never run the same model on two machines at once.
- Commit or push only when asked.

## Running DynEarthSol

- The production runs use the build from DynEarthSol commit `68cc2a0`
  (GeoFLAC/DynEarthSol, `master`), built with `ndims=3 opt=2 openmp=1 hdf5=1 usemmg=1`.
  Continue existing runs with that build; the log header (`[build][code] rev=`) records
  the commit of each run.
- Launch from inside the run directory:
  `OMP_NUM_THREADS=2 nohup <path>/dynearthsol3d <run>.cfg > <run>.log 2>&1 &`.
  The log is block-buffered and lags; track progress with `<run>.info` (columns: frame,
  step, time in s, dt, wall time in s, nnode, nelem, nseg) and the `save.*` files.
- Every frame has a checkpoint (`checkpoint_frame_interval = 1`). To resume from frame
  N, add to `[sim]`: `is_restarting = yes`, `restarting_from_modelname = <run>`,
  `restarting_from_frame = N`. It needs `<run>.save.N.vtkhdf`, `<run>.chkpt.N.vtkhdf` and
  `<run>.info` in the run directory. Keeping the same `modelname` is fine.
- A log search for "nan" matches "nano-kdtree"; search for `NaN|Error|Abort` instead.
- Plotting uses Python with numpy, h5py, matplotlib, scipy (laptop: the `gospl` conda
  env; numpy 1.26, h5py 3.11, matplotlib 3.10, scipy 1.17).

## Current state (update as it changes)

- The work now lives on the workstation nefertiti.ceri.memphis.edu (128 cores), in
  `~/projects/Masako_plate_tectonics`; the laptop copy is no longer running anything.
  `MIGRATE.md` records the move.
- DynEarthSol for these runs on nefertiti: `~/opt/DynEarthSol-68cc2a0/dynearthsol3d`
  (mmg configured with `-DUSE_SCOTCH=OFF`; see `MIGRATE.md`). Leave
  `~/opt/DynEarthSol` there alone; it is a separate checkout.
- fff20 and bh20 (3 Myr, 20 km): started on the laptop on 2026-11-17, restarted on
  nefertiti on 2026-11-19 from frames 5 and 4 (`<run>.restart<N>.cfg`, 16 threads each,
  about 16 min per 0.1 Myr frame, about 7 h to finish). The first attempt, stopped on
  2026-11-10, is in `<run>/stopped_2026-11-10/`.
- To restart again from frame N, copy `<run>.cfg` to `<run>.restart<N>.cfg` and add the
  three restart lines; keep the original `.cfg` unchanged.
