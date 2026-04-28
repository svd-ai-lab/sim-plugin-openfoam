# Conjugate Heat Transfer (Multi-Region)

Cases with both fluid and solid regions, coupled across shared
interfaces. Heavy setup but mandatory for many electronics-cooling and
process-engineering problems.

## Solver

`chtMultiRegionFoam` is the standard choice. It handles both steady and
transient — controlled via `controlDict`.

For Foundation v11+: `foamRun -solver multiRegionFluid` for steady fluid +
`solid` regions.

## Directory structure

```
<case>/
├── 0/                           # NOT used directly; per-region 0 dirs below
├── constant/
│   ├── regionProperties         # lists which regions are fluid vs solid
│   ├── air/                     # fluid region named "air"
│   │   ├── polyMesh/
│   │   ├── transportProperties (or thermophysicalProperties)
│   │   ├── turbulenceProperties
│   │   └── g
│   ├── solid/                   # solid region named "solid"
│   │   ├── polyMesh/
│   │   └── thermophysicalProperties
│   └── ... (one constant/<region>/ per region)
├── system/
│   ├── controlDict              # global timing + region list
│   ├── decomposeParDict         # global decomposition
│   ├── air/                     # per-region fvSchemes / fvSolution
│   │   ├── fvSchemes
│   │   └── fvSolution
│   └── solid/
│       ├── fvSchemes
│       └── fvSolution
└── 0.orig/ or 0/                # per-region: 0/<region>/<field> files
    ├── air/
    │   ├── U, p_rgh, T, alphat, k, epsilon
    │   └── ...
    └── solid/
        └── T
```

## `constant/regionProperties`

```c++
regions
(
    fluid       (air)
    solid       (solid)
);
```

Lists region names by category. Names must match the subdirectory names.

## Per-region setup

Each region has its own mesh + properties + numerics. Use OpenFOAM's
`-region` flag for region-aware commands:

```bash
blockMesh -region air
blockMesh -region solid
checkMesh -region air
checkMesh -region solid

decomposePar -allRegions
mpirun -np 4 chtMultiRegionFoam -parallel
reconstructPar -allRegions
```

## Solid region

### `0/solid/T`

```c++
dimensions      [0 0 0 1 0 0 0];
internalField   uniform 300;

boundaryField
{
    sides
    {
        type        zeroGradient;          // insulated
    }
    base
    {
        type        fixedValue;
        value       uniform 350;           // heat source
    }
    interface_solid_to_air
    {
        type        compressible::turbulentTemperatureCoupledBaffleMixed;
        Tnbr        T;
        kappaMethod lookup;
        kappa       k;                      // solid thermal conductivity
        value       uniform 300;
    }
}
```

The interface BC `turbulentTemperatureCoupledBaffleMixed` is the magic.
It exchanges T continuity and heat flux across the fluid/solid boundary
each iteration.

### `constant/solid/thermophysicalProperties`

```c++
thermoType
{
    type            heSolidThermo;
    mixture         pureMixture;
    transport       constIso;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}

mixture
{
    specie         { molWeight 100; }
    transport      { kappa 200; }            // [W/(m·K)] thermal conductivity
    thermodynamics { Hf 0; Cp 900; }         // [J/(kg·K)] specific heat
    equationOfState { rho 8000; }            // [kg/m³] density
}
```

Common solid materials:

| Material | ρ [kg/m³] | Cp [J/(kg·K)] | κ [W/(m·K)] |
|---|---|---|---|
| Aluminum | 2700 | 900 | 200 |
| Copper | 8960 | 385 | 400 |
| Steel | 7800 | 460 | 50 |
| Silicon | 2330 | 700 | 150 |
| FR4 (PCB) | 1850 | 1300 | 0.3 |
| Air (still) | 1.2 | 1005 | 0.026 |

## Fluid region

### `0/air/T`

```c++
dimensions      [0 0 0 1 0 0 0];
internalField   uniform 300;

boundaryField
{
    inlet
    {
        type        fixedValue;
        value       uniform 300;
    }
    outlet
    {
        type        inletOutlet;
        inletValue  uniform 300;
        value       uniform 300;
    }
    sides
    {
        type        zeroGradient;
    }
    interface_air_to_solid
    {
        type        compressible::turbulentTemperatureCoupledBaffleMixed;
        Tnbr        T;
        kappaMethod fluidThermo;
        value       uniform 300;
    }
}
```

Note: `kappaMethod fluidThermo` for the fluid side; `kappaMethod lookup`
+ explicit `kappa` for the solid side.

### `0/air/p_rgh`, `0/air/U`, `0/air/k`, `0/air/epsilon`, `0/air/alphat`

Standard Boussinesq or compressible-thermal setup (see
`references/heat-transfer.md`).

## `system/controlDict`

```c++
application     chtMultiRegionFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         100;                 // for steady, this is iteration count
deltaT          1;                   // dummy for steady
writeControl    timeStep;
writeInterval   10;
runTimeModifiable yes;
adjustTimeStep  no;                  // for steady; yes for transient
maxCo           0.5;
maxDi           1.0;                 // diffusion CFL ceiling for solid
```

## Algorithm controls — per region

`system/air/fvSolution`:

```c++
solvers
{
    "rho.*"        { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0; }
    p_rgh          { solver GAMG; smoother DIC; tolerance 1e-7; relTol 0.01; }
    p_rghFinal     { $p_rgh; relTol 0; }
    "(U|h|k|epsilon)"      { solver PBiCGStab; preconditioner DILU; tolerance 1e-7; relTol 0.1; }
    "(U|h|k|epsilon)Final" { $U; relTol 0; }
}

PIMPLE
{
    momentumPredictor   yes;
    nOuterCorrectors    1;
    nCorrectors         2;
    nNonOrthogonalCorrectors 0;
}

relaxationFactors
{
    fields  { rho 0.1; p_rgh 0.7; }
    equations { U 0.3; h 0.3; "(k|epsilon)" 0.7; }
}
```

`system/solid/fvSolution`:

```c++
solvers
{
    h
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-6;
        relTol          0;
    }
}

PIMPLE
{
    nNonOrthogonalCorrectors 0;
}

relaxationFactors
{
    equations { h 0.7; }
}
```

The solid region only solves the energy equation `h` (enthalpy → T).

## Run sequence

```bash
# Per-region mesh
blockMesh -region air
blockMesh -region solid

# Quick check
checkMesh -region air -allTopology
checkMesh -region solid -allTopology

# Single-host run
chtMultiRegionFoam

# Parallel
decomposePar -allRegions
mpirun -np 4 chtMultiRegionFoam -parallel
reconstructPar -allRegions
```

## Common CHT mistakes

- **Interface patch names not matching across the two regions**: the
  fluid side calls it `air_to_solid` but the solid side calls it
  `solid_to_air`. They MUST be set up with the `mergeMeshes` /
  `splitMeshRegions` workflow so the patches share the same face data.
- **Wrong `kappaMethod`**: `lookup` for solid (with explicit `kappa`),
  `fluidThermo` for fluid. Mixing them causes wrong heat flux.
- **Solid region with `U` field**: solid doesn't have flow. Don't add
  `0/solid/U`. Solver will complain.
- **Forgetting per-region `fvSchemes` and `fvSolution`**: each region
  needs its own. The solid case only needs an `h` solver block.
- **`-allRegions` flag missing on `decomposePar`**: only the master region
  gets decomposed; mpirun fails on the others.
- **Mismatched mesh resolution at the interface**: the solid and fluid
  meshes must have **matching face counts** at the shared interface
  (or use the `cyclicAMI` BC variant). Mismatch causes interpolation
  errors.

## When NOT to use CHT

If the solid is just a thin baffle that doesn't conduct significantly
(e.g. a sheet of fabric), use a `baffle` BC in a single fluid region
instead. CHT is overkill for purely-thermal-interface cases that don't
need to track conduction inside the solid.

If you can specify the solid temperature as a boundary condition (e.g.
"the floor is at 350 K"), do that instead — it's 5× simpler and almost
as accurate when the solid is at quasi-steady state.
