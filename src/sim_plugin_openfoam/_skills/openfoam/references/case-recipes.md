# Case Recipes

Skeleton scaffolds by physical scenario. None are complete answers — each
requires you to fill in geometry-specific values and BC details. They
exist to anchor your decisions on file structure and key choices, not to
copy verbatim.

## 1. Steady incompressible internal flow (RANS k-ω SST)

**Use when**: ducts, channels, valves, internal aerodynamics.

```
case/
├── 0/                       U   p   k   omega   nut
├── constant/                transportProperties   turbulenceProperties
└── system/                  controlDict   fvSchemes   fvSolution   blockMeshDict   decomposeParDict
```

Key choices:
- **Solver**: `simpleFoam`
- **Turbulence**: `kOmegaSST` in `turbulenceProperties`
- **Inlet**: `U fixedValue`, `p zeroGradient`, `k`/`omega` from `(I, L)` formulas
- **Outlet**: `U inletOutlet`, `p fixedValue 0`
- **Walls**: `U noSlip`, `p zeroGradient`, `k kqRWallFunction`, `omega omegaWallFunction`, `nut nutUSpaldingWallFunction`
- **fvSchemes**: `linearUpwind grad(U)` for momentum; `upwind` for k, omega
- **fvSolution**: SIMPLEC (`consistent yes`), `nNonOrthogonalCorrectors 1`, residualControl thresholds 1e-4 to 1e-5

Run sequence:
```bash
blockMesh && checkMesh
[ ! -d 0 ] && cp -r 0.orig 0 || true
simpleFoam | tee log.simpleFoam
```

## 2. Steady incompressible external aerodynamics (RANS, snappyHexMesh)

**Use when**: vehicles, wings, buildings — STL geometry.

```
case/
├── 0/                       U   p   k   omega   nut
├── constant/
│   ├── triSurface/          object.stl
│   ├── transportProperties
│   └── turbulenceProperties
└── system/
    ├── blockMeshDict        background mesh
    ├── snappyHexMeshDict    snap-and-layer config
    ├── surfaceFeatureExtractDict
    ├── controlDict
    ├── fvSchemes
    └── fvSolution
```

Key choices:
- **Mesh**: background `blockMesh` covering domain, then `snappyHexMesh -overwrite`
- **Layers**: 5+ prismatic layers near the surface for boundary layer
- **Turbulence**: `kOmegaSST` (best for adverse pressure gradients)
- **Wall functions**: `nutUSpaldingWallFunction` (handles y+ in buffer layer)
- **Function object**: `forceCoeffs` to track Cd/Cl during the run

Run sequence:
```bash
surfaceFeatureExtract        # if dict present
blockMesh
snappyHexMesh -overwrite
checkMesh -allTopology
[ ! -d 0 ] && cp -r 0.orig 0 || true
simpleFoam
```

## 3. Transient incompressible laminar (`pimpleFoam` or `icoFoam`)

**Use when**: laminar transient flow without turbulence model. Lid-driven
cavity, low-Re channels, oscillatory flow.

```
case/
├── 0/                       U   p
├── constant/                transportProperties   turbulenceProperties (laminar)
└── system/                  controlDict   fvSchemes   fvSolution   blockMeshDict
```

Key choices:
- **Solver**: `icoFoam` (PISO, simpler) or `pimpleFoam` (PIMPLE, allows higher CFL)
- **`controlDict`**: `endTime` long enough for the flow to settle; `deltaT` gives Co < 1
- **`turbulenceProperties.simulationType = laminar`**
- **fvSchemes**: `Euler` for ddt; `linear` for div(phi,U) is OK at low Re; `linearUpwind` for stability
- **fvSolution**: `nCorrectors 2`, `nNonOrthogonalCorrectors 0` (orthogonal mesh)

Run sequence:
```bash
blockMesh && checkMesh
[ ! -d 0 ] && cp -r 0.orig 0 || true
icoFoam | tee log.icoFoam
```

## 4. Two-phase VOF (`interFoam`)

**Use when**: free-surface flow, sloshing, dam break, water-air interface.

```
case/
├── 0/                       U   p_rgh   alpha.water
├── constant/
│   ├── transportProperties  (with phases ( water air ); blocks)
│   └── g
└── system/
    ├── controlDict          (adjustTimeStep yes; maxAlphaCo 1.0)
    ├── fvSchemes            (vanLeer for div(phi,alpha))
    ├── fvSolution           (PIMPLE; nAlphaSubCycles 3)
    ├── blockMeshDict
    └── setFieldsDict        (define water region)
```

Key choices:
- **Solver**: `interFoam`
- **Pressure variable**: `p_rgh` (NOT `p`)
- **`maxAlphaCo`**: 1.0; lower (0.5) for sharper interfaces
- **`div(phi,alpha)`**: `vanLeer` (or `MUSCL`); never `linear`
- **PIMPLE**: `momentumPredictor no`, `nCorrectors 3`

Run sequence:
```bash
blockMesh && checkMesh
[ ! -d 0 ] && cp -r 0.orig 0 || true
setFields
interFoam | tee log.interFoam
```

## 5. Buoyant natural convection (Boussinesq, steady)

**Use when**: heated cavity, natural convection in a room, solar chimney
with small ΔT (< 50 K).

```
case/
├── 0/                       U   p_rgh   T   alphat   k   epsilon   nut
├── constant/
│   ├── transportProperties  (Newtonian + beta + TRef + Pr + Prt)
│   ├── turbulenceProperties
│   └── g
└── system/                  controlDict   fvSchemes   fvSolution   blockMeshDict
```

Key choices:
- **Solver**: `buoyantBoussinesqSimpleFoam`
- **Pressure variable**: `p_rgh`
- **`T` BC**: `fixedValue` on heat sources/sinks; `zeroGradient` on adiabatic walls
- **`pRefCell` 0**: closed domain anchoring
- **Relaxation**: `p_rgh 0.3`, `U 0.7`, `T 0.7`

Run sequence:
```bash
blockMesh && checkMesh
[ ! -d 0 ] && cp -r 0.orig 0 || true
buoyantBoussinesqSimpleFoam | tee log.buoyant
```

## 6. PIMPLE high-CFL transient (Sub-cycled momentum)

**Use when**: transient case where natural CFL would force tiny dt; you
want to subcycle to stay stable at higher dt.

Key changes vs basic transient:
- **`controlDict`**: `adjustTimeStep yes`, `maxCo 5–10`
- **fvSolution**: `PIMPLE { nOuterCorrectors 50; nCorrectors 2; momentumPredictor yes; }`
- **Convergence inside outer loop**: add `outerCorrectorResidualControl` block

```c++
PIMPLE
{
    nOuterCorrectors                50;
    nCorrectors                     2;
    nNonOrthogonalCorrectors        1;
    momentumPredictor               yes;
    outerCorrectorResidualControl
    {
        U   { tolerance 1e-5; relTol 0; }
        p   { tolerance 1e-4; relTol 0; }
    }
}
```

PIMPLE with high `nOuterCorrectors` essentially runs SIMPLE within each
timestep — you trade per-step cost for larger dt.

## 7. DNS isotropic turbulence (`dnsFoam`)

**Use when**: studying decaying or forced isotropic turbulence in a
periodic box.

```
case/
├── 0/                       U   p
├── constant/                transportProperties   turbulenceProperties (laminar — DNS resolves)
└── system/
    ├── controlDict          (small deltaT, write times)
    ├── fvSchemes            (linear/cubic — no diffusion)
    ├── fvSolution
    ├── blockMeshDict        (periodic cyclic patches)
    └── boxTurbDict          (initial spectrum)
```

Key choices:
- **Solver**: `dnsFoam`
- **Mesh**: cubic, fully periodic, all faces `cyclic`
- **`turbulenceProperties.simulationType = laminar`** (no model — DNS resolves all scales)
- **fvSchemes**: high-order central (`cubic` or `linear`), no upwinding
- **Initial condition**: `boxTurb` utility generates synthetic Pope-style turbulence

Run sequence:
```bash
blockMesh && checkMesh
[ ! -d 0 ] && cp -r 0.orig 0 || true
boxTurb                       # generate initial spectrum
dnsFoam | tee log.dnsFoam
```

## 8. Conjugate heat transfer (`chtMultiRegionFoam`)

**Use when**: fluid flowing past a heated solid. Electronics cooling,
heat exchangers (single side).

See `references/conjugate-heat-transfer.md` for the full multi-region
setup. Recipe-level summary:

- One `constant/<region>/` per region (fluid, solid)
- One `system/<region>/{fvSchemes,fvSolution}` per region
- One `0/<region>/<fields>` per region
- Interface BC: `compressible::turbulentTemperatureCoupledBaffleMixed`
- Run: `mpirun -np N chtMultiRegionFoam -parallel`

## 9. MRF (Multiple Reference Frame) — rotating zones

**Use when**: rotating impeller / fan modeled as a rotating zone within
an otherwise stationary domain (steady).

Key additions to a `simpleFoam` case:

- `constant/MRFProperties`:

```c++
MRF1
{
    cellZone        rotor;
    active          yes;
    nonRotatingPatches ();
    origin          (0 0 0);
    axis            (0 0 1);
    omega           constant 100;        // rad/s
}
```

- The rotor cells need to belong to a `cellZone` (defined via
  `topoSet` from a region selection).

The same case otherwise: `simpleFoam` + RANS + standard BCs.

## 10. Atmospheric boundary layer (ABL)

**Use when**: wind around buildings, terrain, wind farm site assessment.

Key choices:
- **Inlet**: log-law profile via `atmBoundaryLayerInletVelocity`
- **Wall function**: `nutkAtmRoughWallFunction` (with z0 surface roughness)
- **Sky**: `slip` or `zeroGradient` for U; `fixedValue` for p
- **Convergence**: typically slow due to scale separation; budget many SIMPLE iterations

```c++
inlet
{
    type        atmBoundaryLayerInletVelocity;
    Uref        10.0;
    Zref        100;
    flowDir     (1 0 0);
    zDir        (0 0 1);
    z0          uniform 0.1;
    zGround     uniform 0;
    value       uniform (0 0 0);
}
```

---

## Cross-recipe rules

- **Always** validate mesh first (`checkMesh`).
- **Always** restore `0/` before solving (some tutorials need
  `cp -r 0.orig 0`).
- **Always** start with conservative numerics (`upwind`), upgrade after
  the case is stable.
- **Always** match `numberOfSubdomains` and MPI rank count for parallel.
- **Never** skip the `Allrun` script for cases shipped with one — it
  embeds non-obvious pre-steps (mesh manipulation, field generation).
