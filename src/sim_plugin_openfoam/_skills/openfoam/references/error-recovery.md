# Error Recovery

When OpenFOAM fails, work the decision tree from the **first** error
signal — don't shotgun fixes. Most failures fall into a small number of
categories with well-known recovery moves.

## The five-second triage

When a solver crashes, run these five commands first:

```bash
# 1. Last 50 lines of the solver log
tail -50 log.<solver>

# 2. Look for any error / fatal / NaN flags
grep -iE "error|fatal|exception|nan|sigfpe|diverge" log.<solver> log.* 2>&1 | head -20

# 3. Mesh quality — fast retest
checkMesh -latestTime 2>&1 | grep -iE "fail|error|\\*\\*\\*"

# 4. Last few CFL numbers — were we stable?
grep "Courant Number" log.<solver> | tail -5

# 5. Bounding warnings — turbulence quantities being clipped?
grep "bounding" log.<solver> | tail -10
```

These five give you 80% of "what just happened?" answers in seconds.
Don't skip them.

## Decision tree

```
Crashes IMMEDIATELY at solver launch?
├── "FOAM FATAL ERROR: cannot find patch <name>"
│   → Patch in 0/<field> doesn't match constant/polyMesh/boundary
│   → Fix: rename field-side patch OR add patch to mesh boundary
├── "FOAM FATAL ERROR: cannot find file <path>"
│   → Missing 0/, 0/.orig not copied, or geometry file absent
│   → Fix: cp -r 0.orig 0; check constant/triSurface/ if STL-based
├── "dimensions mismatch"
│   → 0/<field> dimension row wrong; field doesn't match operator
│   → Fix: see references/case-setup.md "dimensions" table
├── "RAS model 'X' not found"
│   → Typo in turbulenceProperties/momentumTransport
│   → Fix: check spelling vs references/turbulence-setup.md
├── "MPI: numberOfSubdomains mismatch"
│   → -np N != decomposeParDict.numberOfSubdomains
│   → Fix: edit dict OR re-decompose with correct N
├── "processor boundary mismatch"
│   → Stale processor*/ from a previous decompose
│   → Fix: rm -rf processor*; decomposePar -force
└── "Cannot find PIMPLE entry" (or SIMPLE/PISO)
    → Wrong algorithm block in fvSolution for the chosen solver
    → Fix: see references/numerics-and-schemes.md per-solver patterns

Crashes after a few timesteps?
├── "Floating point exception (core dumped)" / SIGFPE
│   → NaN somewhere. Three usual causes:
│   ├── Courant number very high → reduce deltaT or enable adjustTimeStep
│   ├── checkMesh shows non-orth > 80° → fix mesh; add nNonOrthogonalCorrectors
│   └── Aggressive schemes (linearUpwind too soon) → switch to upwind temporarily
├── "Maximum number of iterations exceeded"
│   → Linear solver not converging on a step
│   → Fix: tighten/loosen relTol; add nNonOrthogonalCorrectors
├── "bounding k/epsilon/omega"
│   → Turbulence quantity went negative; was clipped
│   ├── Check inlet turbulence values (reasonable I and L?)
│   ├── Use upwind for div(phi,k), div(phi,epsilon)
│   └── Check wall function on every wall patch
└── Sudden divergence (residuals climb)
    ├── Initial conditions far from steady state
    │   → Use potentialFoam for initial U field, then start
    ├── Relaxation too aggressive
    │   → Drop p to 0.3, U to 0.5, restart
    └── BCs over-constrained
        → Check exactly one patch sets pressure; rest zeroGradient

Steady-state residuals NOT converging?
├── Residuals oscillating
│   → Relaxation too aggressive; reduce
├── Residuals plateau at 1e-3 / 1e-4
│   ├── Mesh quality (check skewness, non-orth)
│   ├── Try better convection scheme (upgrade upwind → linearUpwind)
│   ├── Add nNonOrthogonalCorrectors
│   └── Refine mesh in regions with high gradient
├── Residuals plateau at 1e-1 (very early)
│   → BCs probably wrong; case may be ill-posed
│   → Check dimensions, check inlet/outlet pressure pairing
├── Continuity errors growing
│   → Pressure-velocity coupling failing; usually mesh
│   → Add nNonOrthogonalCorrectors (1, then 2)
│   → Tighten p tolerance
└── Very slow but steady drop
    → Just slow convergence; bump relaxation gradually after stability

Transient simulation diverges?
├── CFL > 1 with explicit-style schemes (icoFoam, dnsFoam)
│   → Reduce deltaT
├── PIMPLE with nOuterCorrectors=1 at high CFL
│   → Increase nOuterCorrectors to 50; enable momentumPredictor
├── Multiphase interface explodes
│   → Reduce maxAlphaCo to 0.5
│   → Confirm div(phi,alpha) is bounded (vanLeer/MUSCL)
│   → Reduce cAlpha if interface is too sharp
└── Unbounded T or species
    → Add bounded scheme on div(phi,T) or div(phi,Yi)
    → Sanity-check thermophysical properties (Cp, Pr)
```

## Specific failure recipes

### CFL / timestep failure

```
Courant Number mean: 608.234 max: 48546.7
```

Recovery sequence:

1. Reduce `deltaT` by 10×.
2. Enable adaptive timestepping in `controlDict`:
   ```c++
   adjustTimeStep  yes;
   maxCo           0.9;
   maxDeltaT       0.01;
   ```
3. For multiphase: also `maxAlphaCo 0.5;`
4. For PIMPLE at unavoidably-high CFL: `nOuterCorrectors 50` and `momentumPredictor yes`.

Root cause check:
```bash
grep "Courant Number" log.* | awk '{print $NF}' | sort -n | tail -5
# Max Co >> 1 → deltaT too large OR mesh has tiny cells
```

### Floating point exception (NaN)

```
[*] #0  Foam::error::printStack(...)
[*] #1  Foam::sigFpe::sigHandler(int)
Floating point exception (core dumped)
```

Recovery:

1. Find which field went NaN — look at the LAST `Solving for X` line; X is the culprit.
2. Drop CFL: reduce `deltaT` by 10× and re-run. If NaN still happens at the SAME timestep, it's not a CFL issue.
3. Check mesh: `checkMesh -allTopology`. If non-orth > 70° → add `nNonOrthogonalCorrectors`. If > 85° → remesh.
4. Switch convection scheme to `upwind` for ALL fields temporarily. If that runs, gradually upgrade per-field.
5. Check BCs match initial field: an inlet `fixedValue 1000 m/s` but `internalField uniform (0 0 0)` is a discontinuity that takes many iterations to relax.

### Bounding warnings

```
bounding k, min: -0.0023 max: 0.0123 average: 0.005
bounding epsilon, min: -0.001 max: 0.034 average: 0.012
```

The solver is clipping negative turbulence quantities to a floor. Recovery:

1. Check inlet turbulence values are physical (positive, sane magnitude — see `references/turbulence-setup.md`).
2. Check wall functions on every wall (k=`kqRWallFunction`, epsilon=`epsilonWallFunction`, etc.). A wall with `zeroGradient` for k near a strong gradient generates negative values.
3. Switch `div(phi,k)` and `div(phi,epsilon)` to `upwind` (always positive); `linearUpwind` can go negative.
4. If your inlet ε / ω is much larger than near-wall production, the model may be unstable. Reduce inlet I or increase L.

### Linear solver "Max iterations exceeded"

```
DICPCG: Solving for p, Initial residual = 1, Final residual = 0.5, No Iterations 1000
DICPCG: Solving for p, ... Maximum number of iterations exceeded
```

Pressure solver couldn't reduce residual within budget. Recovery:

1. Switch `p` solver to `GAMG` (multigrid; usually 10-100× faster on pressure):
   ```c++
   p
   {
       solver          GAMG;
       smoother        DICGaussSeidel;
       tolerance       1e-7;
       relTol          0.05;
       nCellsInCoarsestLevel 200;
   }
   ```
2. Loosen `relTol` from 0.01 → 0.05 (pressure rarely needs tight intermediate relTol).
3. Add `nNonOrthogonalCorrectors 1` (or 2 if mesh non-orth > 65°).
4. If issue persists: mesh quality is likely the culprit; remesh.

### Continuity errors growing

```
time step continuity errors : sum local = 1e-3, global = 8e-4, cumulative = 0.05
```

Cumulative growing past 1e-3 = mass conservation failing. Recovery:

1. Add or increase `nNonOrthogonalCorrectors` in fvSolution.
2. Check `nCorrectors` on PISO/PIMPLE — bump from 2 to 3.
3. Tighten `p` (or `p_rgh`) tolerance from 1e-6 to 1e-8.
4. Check mesh non-orthogonality and skewness; if high, more correctors won't fix; remesh.

### Initial-condition shock

Symptom: solver runs the first few steps fine, then residuals balloon. Often happens when initial U field is far from boundary-condition flow.

Recovery: pre-solve with `potentialFoam` to get a sane U initial field:

```bash
potentialFoam        # writes 0/U with potential-flow estimate
simpleFoam            # then run the real solver
```

`potentialFoam` is fast (a few iterations of Laplace solve) and produces
a divergence-free U that satisfies the BCs.

### Wrong patch type for the BC type chosen

```
FOAM FATAL ERROR: BC noSlip cannot be applied to patch of type symmetryPlane
```

Recovery: change the patch type in `constant/polyMesh/boundary`:

```c++
walls
{
    type            wall;        // not patch / symmetryPlane / etc.
    nFaces          200;
    startFace       3800;
}
```

Or change the BC in the field file to one compatible with the patch type:

```c++
symPlane
{
    type            symmetryPlane;       // matches the patch type
}
```

For 2D `empty` patches: BOTH the mesh patch type AND every field's BC
must say `empty`. Mismatch → solver runs in 3D mode.

### Tutorial/init pre-step missing

Symptom: error like `cannot find file 0/p` at startup.

Recovery: check if there's a `0.orig/` directory:

```bash
ls -la
[ -d 0.orig ] && cp -r 0.orig 0
```

Almost every tutorial relies on `Allrun` calling `restore0Dir` to set up
`0/`. If you skip Allrun, do it yourself.

For tutorials with shared geometry:

```bash
mkdir -p constant/geometry
cp $FOAM_TUTORIALS/resources/geometry/<file>.vtk.gz constant/geometry/
```

For combustion / chemistry:

```bash
chemkinToFoam chemkin/chem.inp chemkin/therm.dat \
              chemkin/transportProperties \
              constant/reactions constant/thermo
```

For molecular dynamics:

```bash
mdInitialise
```

These are documented in the original tutorial's `Allrun` script.

## Verify the recovery before claiming victory

After applying a fix:

```bash
# Run a short test (e.g. endTime = 0.05 instead of 2.0)
# Then check the FULL diagnostic suite:

tail -20 log.<solver>                     # End reached?
grep "Final residual" log.<solver> | tail -5     # residuals dropping?
grep "bounding" log.<solver>              # any new clipping?
grep "Courant Number" log.<solver> | tail -3
checkMesh -latestTime | tail -10
```

If all five pass on the short run, run the full case.

## When to give up and ask for help

- If you've tried 3 different scheme combinations and none converge.
- If `checkMesh` reports issues you can't fix without remeshing.
- If the case is ill-posed (you can't tell which BC is "right").
- If the physical problem is outside the model's validity (e.g.,
  applying RANS to a transitional flow regime).

In those cases, document what you tried (commands + log excerpts),
state the hypothesis you have for the cause, and escalate. Don't keep
running iterations of the same broken setup.
