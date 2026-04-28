# Heat Transfer (Single-Region)

Buoyancy-driven and forced-convection cases with temperature. For
fluid + solid coupling, see `references/conjugate-heat-transfer.md`.

## Decision: Boussinesq vs full compressible

| Path | When |
|---|---|
| **Boussinesq** (`buoyantBoussinesqSimpleFoam`/`buoyantBoussinesqPimpleFoam`) | Small ΔT (< ~50 K) where ρ ≈ ρ_ref + small correction. Cheap, robust, classical natural-convection cases. |
| **Compressible** (`buoyantSimpleFoam`/`buoyantPimpleFoam`) | Large ΔT, density variation > 10% of mean, or coupling with compressible flow. Solves real ρ(p,T) via the equation of state. |

For most "room-scale" thermal cases (heated walls, hot patches, plumes
with ΔT < 30 K): Boussinesq is the right choice and 5× faster.

## Boussinesq setup

The Boussinesq approximation:

```
ρ(T) = ρ_ref · (1 − β · (T − T_ref))
```

Pressure variable: `p_rgh` (kinematic, in m²/s²; despite the name).

### Required fields

- `0/U` (vector)
- `0/p_rgh` (scalar; modified pressure)
- `0/T` (scalar; temperature in K)
- `0/alphat` (scalar; turbulent thermal diffusivity, only with RANS)
- `0/k`, `0/epsilon` (or `omega`), `0/nut` (RANS turbulence)

### `constant/transportProperties` (Boussinesq, ESI)

```c++
transportModel  Newtonian;

nu              [0 2 -1 0 0 0 0]    1.5e-5;     // kinematic viscosity of air
beta            [0 0 0 -1 0 0 0]    3.0e-3;     // thermal expansion 1/K
TRef            [0 0 0 1 0 0 0]     300;        // reference temperature
Pr              [0 0 0 0 0 0 0]     0.7;        // molecular Prandtl
Prt             [0 0 0 0 0 0 0]     0.85;       // turbulent Prandtl
```

Defaults for **air** at room temperature:
- `nu = 1.5e-5 m²/s`
- `beta = 1/T_ref ≈ 3.3e-3 1/K` (ideal gas approximation)
- `Pr = 0.7`
- `Prt = 0.85`

For **water** at room temperature:
- `nu = 1e-6 m²/s`
- `beta = 2.1e-4 1/K`
- `Pr = 7`

### `constant/turbulenceProperties` (RANS)

```c++
simulationType  RAS;
RAS
{
    RASModel        kEpsilon;        // or kOmegaSST
    turbulence      on;
    printCoeffs     on;
}
```

### `constant/g`

```c++
dimensions      [0 1 -2 0 0 0 0];
value           (0 -9.81 0);
```

### `0/T`

```c++
dimensions      [0 0 0 1 0 0 0];
internalField   uniform 300;        // ambient

boundaryField
{
    floor
    {
        type        fixedValue;
        value       uniform 300;     // cold floor
    }
    hotPatch
    {
        type        fixedValue;
        value       uniform 600;     // heated patch
    }
    ceiling
    {
        type        fixedValue;
        value       uniform 300;
    }
    sideWalls
    {
        type        zeroGradient;    // adiabatic side walls
    }
    frontAndBack
    {
        type        empty;
    }
}
```

### `0/p_rgh`

```c++
dimensions      [1 -1 -2 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    floor       { type fixedFluxPressure; value uniform 0; }
    ceiling     { type fixedFluxPressure; value uniform 0; }
    sideWalls   { type fixedFluxPressure; value uniform 0; }
    hotPatch    { type fixedFluxPressure; value uniform 0; }
    frontAndBack { type empty; }
}
```

For a closed domain (no inlet/outlet), all walls use `fixedFluxPressure`
and the solver anchors pressure via `pRefCell` in `fvSolution`.

### `0/U`

All walls = `noSlip`; front/back = `empty`.

### `0/alphat`

```c++
dimensions      [0 2 -1 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    floor   { type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 0; }
    // similar for other walls...
    frontAndBack { type empty; }
}
```

`alphatJayatillekeWallFunction` for high-Re wall functions; for low-Re,
just `fixedValue uniform 0`.

## Compressible thermal setup

Use when ΔT > 50 K or when you need real density variation.

### Solver

`buoyantSimpleFoam` (steady) or `buoyantPimpleFoam` (transient).

### Required fields

- Same as Boussinesq, plus `0/p` (real thermodynamic pressure in Pa).

### `constant/thermophysicalProperties`

```c++
thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState perfectGas;        // or Boussinesq
    specie          specie;
    energy          sensibleEnthalpy;  // or sensibleInternalEnergy
}

mixture
{
    specie       { molWeight 28.96; }      // air
    thermodynamics { Cp 1005; Hf 0; }
    transport    { mu 1.8e-5; Pr 0.7; }
}
```

### `0/p`

```c++
dimensions      [1 -1 -2 0 0 0 0];      // Pa
internalField   uniform 1e5;            // 100 kPa
```

For compressible-buoyant cases, you typically want `0/p_rgh` as well
for the BC; the solver derives `0/p` from it.

## SIMPLE convergence for buoyant steady

```c++
// fvSolution
SIMPLE
{
    nNonOrthogonalCorrectors 1;
    pRefCell        0;                  // anchor pressure for closed domain
    pRefValue       0;
    consistent      yes;
    residualControl
    {
        p_rgh       1e-3;
        U           1e-3;
        T           1e-3;
        "(k|epsilon|omega)" 1e-3;
    }
}

relaxationFactors
{
    fields { p_rgh 0.3; rho 0.05; }
    equations
    {
        U     0.7;
        T     0.7;                       // T can take more aggressive relaxation
        "(k|epsilon|omega)" 0.7;
    }
}
```

The `rho 0.05` relaxation (compressible only) is critical — too-aggressive
density updates cause oscillation.

## Common heat-transfer mistakes

- **Boussinesq case set up with `p` instead of `p_rgh`**: solver aborts.
  Fix: rename and use Boussinesq pressure convention.
- **Forgetting `0/T` BCs that match all the walls**: solver complains
  about missing patches in the field. T file must list every patch.
- **`adiabatic` boundary spelled wrong**: use `zeroGradient` for `T` (not
  the literal word "adiabatic"). It implies zero temperature gradient =
  zero heat flux.
- **Missing `0/alphat`**: required when turbulence is on. Solver aborts.
- **Wrong sign on `g`**: gravity vector must point DOWN. `(0 -9.81 0)` if
  y is the vertical axis.
- **Closed domain without `pRefCell`**: solver can't anchor absolute
  pressure → divergence or unphysical bulk shift.
- **`beta` set wrong**: for air at 300 K, β = 1/T = 3.3e-3 / K. For water,
  it's 2.1e-4 / K. Wrong value → wrong buoyancy magnitude → wrong plume.
- **Initial T uniform = wall T**: nothing drives convection. Initial T
  should differ from the boundary heat sources or include a thermal
  perturbation (`setFields`).

## Sanity checks before solving

```bash
# Confirm thermophysical model loaded
foamDictionary -entry thermoType constant/thermophysicalProperties 2>&1

# Confirm gravity orientation
cat constant/g

# Confirm Pr, Prt match the solver expectations
foamDictionary -entry Pr constant/transportProperties 2>&1

# Sanity-check inlet T (if any)
foamDictionary -entry boundaryField/inlet/value 0/T 2>&1
```

## Relevant non-dimensional groups

For natural convection in a box of height L heated by ΔT:

```
Ra (Rayleigh) = g · β · ΔT · L³ / (ν · α)        where α = ν/Pr
Pr            = ν / α
Gr            = Ra / Pr
```

Ra = 10⁴ → laminar steady plume
Ra = 10⁶ → laminar transient
Ra = 10⁸ → transitional
Ra > 10⁹ → turbulent (need RANS or LES)

For our 5 × 10 × 10 m room with ΔT = 300 K, β = 3.3e-3, ν = 1.5e-5, Pr = 0.7:

```
α = 1.5e-5 / 0.7 ≈ 2.1e-5 m²/s
Ra = 9.81 × 3.3e-3 × 300 × 5³ / (1.5e-5 × 2.1e-5) ≈ 4 × 10¹³
```

→ Highly turbulent → MUST use RANS or LES, not laminar. Plain
`buoyantBoussinesqSimpleFoam` with `simulationType laminar` would
under-predict mixing badly.
