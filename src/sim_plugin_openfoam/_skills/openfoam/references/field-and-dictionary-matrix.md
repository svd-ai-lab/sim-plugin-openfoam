# Field & Dictionary Matrix

Lookup tables for "what files do I need given solver X and turbulence
model Y?". When in doubt, start here before authoring.

## Solver → required fields in `0/`

| Solver | Required fields |
|---|---|
| `icoFoam` | `U`, `p` |
| `pimpleFoam` (laminar) | `U`, `p` |
| `pimpleFoam` (RANS k-ε) | `U`, `p`, `k`, `epsilon`, `nut` |
| `pimpleFoam` (RANS k-ω SST) | `U`, `p`, `k`, `omega`, `nut` |
| `pimpleFoam` (LES) | `U`, `p`, `k` (sub-grid), `nut` |
| `simpleFoam` (laminar) | `U`, `p` |
| `simpleFoam` (RANS k-ε) | `U`, `p`, `k`, `epsilon`, `nut` |
| `simpleFoam` (RANS k-ω SST) | `U`, `p`, `k`, `omega`, `nut` |
| `simpleFoam` (RANS Spalart-Allmaras) | `U`, `p`, `nuTilda`, `nut` |
| `interFoam` | `U`, `p_rgh`, `alpha.water` |
| `dnsFoam` | `U`, `p` |
| `buoyantBoussinesqSimpleFoam` | `U`, `p_rgh`, `T`, `alphat`, `k`, `epsilon`, `nut` (if RANS) |
| `buoyantBoussinesqPimpleFoam` | same as above |
| `buoyantSimpleFoam` (compressible) | `U`, `p`, `p_rgh`, `T`, `alphat`, `k`, `epsilon`, `nut` |
| `rhoSimpleFoam` | `U`, `p`, `T`, `k`, `epsilon`/`omega`, `nut` |
| `chtMultiRegionFoam` (per fluid region) | `U`, `p_rgh`, `T`, `alphat`, `k`, `epsilon` |
| `chtMultiRegionFoam` (per solid region) | `T` only |
| `reactingFoam` | `U`, `p`, `T`, `k`, `epsilon`/`omega`, plus species `Yi` |

`alphat` (turbulent thermal diffusivity) is needed whenever you have a
turbulence model AND a temperature field. It's a derived field initialized
to 0 with wall functions.

## Turbulence model → required fields

| Model | Fields | `RAS { RASModel ... }` value |
|---|---|---|
| Laminar | none extra | `laminar` |
| k-ε standard | `k`, `epsilon`, `nut` | `kEpsilon` |
| k-ε realizable | `k`, `epsilon`, `nut` | `realizableKE` |
| k-ε RNG | `k`, `epsilon`, `nut` | `RNGkEpsilon` |
| k-ω SST | `k`, `omega`, `nut` | `kOmegaSST` |
| k-ω | `k`, `omega`, `nut` | `kOmega` |
| Spalart-Allmaras | `nuTilda`, `nut` | `SpalartAllmaras` |
| LES Smagorinsky | `nut`, `k` (sub-grid) | `LES` mode + `LESModel Smagorinsky` |
| LES one-equation | `k` (sgs), `nut` | `LES` + `kEqn` |
| DNS | none | run `dnsFoam` directly, no model |

## Required dictionaries in `constant/`

| Dictionary | Always? | Used by |
|---|---|---|
| `polyMesh/boundary` | Yes | All (written by `blockMesh` / `snappyHexMesh`) |
| `transportProperties` (ESI) / `physicalProperties` (Found v11) | Yes (single-phase) | All incompressible single-phase |
| `turbulenceProperties` (ESI) / `momentumTransport` (Found v11) | Yes (always — even for laminar) | All flow solvers |
| `thermophysicalProperties` | Yes (compressible / heat) | `rhoSimpleFoam`, `buoyantSimpleFoam`, `chtMultiRegionFoam`, ... |
| `g` | Yes (buoyant / VOF) | `buoyant*Foam`, `interFoam` |
| `MRFProperties` | Optional | Multiple Reference Frame (rotating zones) |
| `dynamicMeshDict` | Optional | Moving mesh |
| `radiationProperties` | Optional | Radiation models |

## Required dictionaries in `system/`

| Dictionary | Always? | Notes |
|---|---|---|
| `controlDict` | Yes | Run timing, write controls, application name |
| `fvSchemes` | Yes | Discretization choices |
| `fvSolution` | Yes | Linear solvers + algorithm controls (SIMPLE/PISO/PIMPLE) |
| `blockMeshDict` | If using `blockMesh` | Geometry definition |
| `decomposeParDict` | Parallel only | MPI decomposition |
| `snappyHexMeshDict` | If using snappy | STL-based meshing |
| `surfaceFeatureExtractDict` | snappy with edges | Feature extraction pre-step |
| `setFieldsDict` | If using `setFields` | Initialize phase fraction / scalars regionally |
| `sampleDict` | Optional post | Sampling lines / planes — also via `postProcess -func sample` |
| `topoSetDict` | Optional | Cell zone selection |
| `createPatchDict` | Optional | Re-patching boundaries (cyclic AMI etc.) |

## File ↔ key fast lookups

### `transportProperties` (ESI single-phase, Newtonian)

```c++
transportModel  Newtonian;
nu              1e-5;       // [m²/s]; wrap in [0 2 -1 0 0 0 0] dims if strict
```

For non-Newtonian, change `transportModel` to `BirdCarreau`, `CrossPowerLaw`,
`HerschelBulkley`, etc. — each requires its own coefficients block.

### `physicalProperties` (Foundation v11 single-phase)

```c++
viscosityModel  constant;
nu              [0 2 -1 0 0 0 0] 1e-5;
```

Same physical content, different file name and slightly different syntax.

### `turbulenceProperties` (ESI)

```c++
simulationType  RAS;        // or laminar, LES, DNS

RAS
{
    RASModel        kEpsilon;
    turbulence      on;
    printCoeffs     on;
}
```

### `momentumTransport` (Foundation v11 equivalent)

```c++
simulationType  RAS;
RAS
{
    model           kEpsilon;
    turbulence      on;
    printCoeffs     on;
}
```

### `g` (buoyant / VOF)

```c++
dimensions      [0 1 -2 0 0 0 0];
value           (0 -9.81 0);
```

The orientation matters: `(0 -9.81 0)` = gravity in -y direction. Match
to your geometry.

### `thermophysicalProperties` (compressible single-phase)

```c++
thermoType
{
    type            heRhoThermo;          // or heHePsiThermo for psi-based
    mixture         pureMixture;
    transport       const;                // const / sutherland / polynomial
    thermo          hConst;               // hConst / janaf / hPolynomial
    equationOfState perfectGas;           // perfectGas / Boussinesq / rhoConst
    specie          specie;
    energy          sensibleEnthalpy;     // or sensibleInternalEnergy
}

mixture
{
    specie     { molWeight 28.96; }
    thermodynamics { Cp 1005; Hf 0; }
    transport  { mu 1.8e-5; Pr 0.7; }
}
```

### `thermophysicalProperties` (Boussinesq, simpler)

```c++
thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState Boussinesq;
    specie          specie;
    energy          sensibleEnthalpy;
}

mixture
{
    specie     { molWeight 28.96; }
    thermodynamics { Cp 1005; Hf 0; }
    transport  { mu 1.8e-5; Pr 0.7; }
    equationOfState
    {
        rho0    1.0;          // reference density
        T0      300;          // reference temperature
        beta    3e-3;         // thermal expansion 1/K
    }
}
```

## Sanity sequence before solver run

1. `foamDictionary -entry boundary -keywords constant/polyMesh/boundary` — list patches
2. `for f in 0/*; do echo "$f:"; foamDictionary -entry boundaryField -keywords "$f"; done` — patches per field
3. Set difference should be empty: every patch defined in mesh appears in every field, and no field references an undefined patch.
4. `foamDictionary -entry RAS/RASModel constant/turbulenceProperties` — confirm turbulence model
5. Cross-reference the model with the table at the top of this file: do you have all the required `0/` fields?

If steps 3 or 5 fail, fix before running.
