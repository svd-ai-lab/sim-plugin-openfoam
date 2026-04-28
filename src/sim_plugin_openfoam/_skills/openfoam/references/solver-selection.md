# OpenFOAM Solver Selection

Choosing the right solver is the highest-leverage decision in case
authoring. Wrong solver → no amount of fvScheme tuning helps.

## Decision tree

```
Is the flow steady-state or transient?
├── Steady (you only care about the final converged state):
│   ├── Incompressible single-phase:
│   │   └── simpleFoam              (any RANS turbulence; default workhorse)
│   ├── Incompressible buoyant (Boussinesq):
│   │   └── buoyantBoussinesqSimpleFoam
│   ├── Compressible buoyant (full ρ(T)):
│   │   └── buoyantSimpleFoam
│   ├── Conjugate heat transfer (fluid + solid):
│   │   └── chtMultiRegionFoam (handles both steady and transient)
│   └── Compressible single-phase:
│       └── rhoSimpleFoam / sonicFoam (Mach-dependent)
│
└── Transient (time history matters):
    ├── Incompressible laminar:
    │   ├── icoFoam                 (PISO, simple BCs, classic cavity)
    │   └── pimpleFoam              (PIMPLE, larger CFL allowed)
    ├── Incompressible RANS/LES:
    │   └── pimpleFoam (with turbulence model in turbulenceProperties)
    ├── Multiphase (two immiscible fluids, free-surface):
    │   └── interFoam                (VOF + alpha transport)
    ├── DNS isotropic turbulence:
    │   └── dnsFoam                  (periodic, no model)
    ├── Buoyancy + transient (Boussinesq):
    │   └── buoyantBoussinesqPimpleFoam
    ├── Compressible transient + heat:
    │   └── rhoPimpleFoam / sonicFoam
    └── Combustion / chemistry:
        └── reactingFoam / chemFoam (CHEMKIN inputs required)
```

## Pressure convention by solver

OpenFOAM uses two pressure variables. Pick the right one and your `p`
field type / dimensions / BCs cascade correctly.

| Solver class | Field | Dimensions | Notes |
|---|---|---|---|
| Incompressible isothermal (`icoFoam`, `simpleFoam`, `pimpleFoam`, `interFoam` — wait, see below) | `p` | `[0 2 -2 0 0 0 0]` (m²/s²) | Kinematic pressure (`p/ρ`) |
| Buoyant (`buoyant*SimpleFoam`, `buoyant*PimpleFoam`) | `p_rgh` | `[1 -1 -2 0 0 0 0]` (Pa) — but in Boussinesq still kinematic | `p_rgh = p − ρgh`; let solver compute `p` from it |
| VOF (`interFoam`, `compressibleInterFoam`) | `p_rgh` | `[1 -1 -2 0 0 0 0]` (Pa) | Same trick: handles density jumps cleanly |
| Compressible (`rhoSimpleFoam`, `sonicFoam`, `rhoPimpleFoam`) | `p` | `[1 -1 -2 0 0 0 0]` (Pa) | Real thermodynamic pressure |
| CHT (`chtMultiRegionFoam`) | `p_rgh` per region | varies | Each region's own pressure file |

**Common error**: putting `p` (with kinematic dimensions) into a buoyant
case. Solver aborts at startup. Fix: rename file to `p_rgh` AND put the
correct compressible / Boussinesq dimensions on it.

## Algorithm by solver family

| Solver | Algorithm | Outer/inner loop |
|---|---|---|
| `simpleFoam` | SIMPLE (steady) | One outer pass per iteration; `nNonOrthogonalCorrectors` for skewed meshes |
| `pimpleFoam` | PIMPLE (transient pseudo-steady) | `nOuterCorrectors` (PISO-like) + `nCorrectors` (pressure) |
| `icoFoam` | PISO | `nCorrectors` (typically 2), `nNonOrthogonalCorrectors` |
| `interFoam` | PIMPLE + alpha-MULES | Plus `nAlphaSubCycles` for sharp interface |
| `buoyantBoussinesqSimpleFoam` | SIMPLE + extra T equation | Same SIMPLE controls |
| `dnsFoam` | Explicit | No outer corrector; CFL governs stability |

The algorithm shapes which keys live in `fvSolution`:

```c++
// fvSolution for simpleFoam (steady)
SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent      yes;          // SIMPLEC; allows higher relaxation
    residualControl
    {
        p           1e-4;
        U           1e-5;
        "(k|epsilon|omega)" 1e-5;
    }
}
relaxationFactors
{
    fields { p 0.3; }
    equations { U 0.7; "(k|epsilon|omega)" 0.7; }
}
```

```c++
// fvSolution for pimpleFoam (transient)
PIMPLE
{
    nOuterCorrectors 2;            // 1 = PISO; >1 = "PIMPLE", more stable at high CFL
    nCorrectors      2;            // pressure correctors per outer pass
    nNonOrthogonalCorrectors 1;
    momentumPredictor    yes;
    pRefCell             0;
    pRefValue            0;
}
```

See `references/numerics-and-schemes.md` for full schemes/solver block recipes.

## Solver-binary availability

ESI ships every solver as a separate binary in `$FOAM_APPBIN`:

```bash
ls $FOAM_APPBIN | grep -iE "foam$" | head -20
```

Foundation v11+ went modular: only `foamRun` exists, and you select the
algorithm via `system/controlDict`:

```c++
solver          incompressibleFluid;     // module name, not binary name
```

Then run `foamRun` (no `-solver` flag in the basic case; the flag
`-solver <module>` is used to override). Modules in v11:
`incompressibleFluid`, `incompressibleVoF`, `compressibleFluid`,
`incompressibleDenseParticleFluid`, `multiphaseEuler`, etc.

Probe before running:

```bash
which icoFoam pimpleFoam simpleFoam interFoam dnsFoam buoyantSimpleFoam 2>&1
which foamRun 2>&1
```

If `icoFoam` exists, ESI-style invocation works directly. Otherwise prefer
`foamRun` and verify the requested module loads:

```bash
foamRun -listSolvers 2>&1 | grep incompressible
```

## Common selection mistakes

- Using `simpleFoam` for a transient problem (cavity startup, dam break) —
  it'll converge to nothing because the steady SIMPLE pressure-velocity
  coupling can't capture transient dynamics. Use `pimpleFoam` or
  `icoFoam`.
- Using `pimpleFoam` for a steady-state heat problem — it'll work but
  burn a lot of CPU integrating to false equilibrium. Use a SIMPLE-family
  steady solver.
- Picking `interFoam` for a non-multiphase case — it'll demand
  `alpha.water` and a phase-properties dictionary you don't have.
- Picking `chtMultiRegionFoam` for a single-region problem — it expects
  region directories under `constant/` and demands per-region setup that
  vastly outweighs the value.

When unsure, default to the simplest solver that fits the physics:
`simpleFoam` for steady-incompressible, `pimpleFoam` for transient
incompressible, `interFoam` for two-phase, `chtMultiRegionFoam` only when
solid + fluid are both present.
