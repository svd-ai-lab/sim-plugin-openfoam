# Multiphase / VOF (`interFoam`)

Two-phase, immiscible, incompressible flows with sharp interfaces.
Specifics that don't apply to single-phase cases.

## Phase fraction `alpha.water`

`alpha.water` is the volume fraction of water (or the "first" phase) in
each cell. By construction:

- `alpha.water = 1` → cell is fully water
- `alpha.water = 0` → cell is fully air
- `0 < alpha.water < 1` → cell contains the interface

The solver advects this scalar with a **bounded** scheme + interface
compression. If the scheme is unbounded (`linear` etc.), `alpha.water`
goes negative or > 1 and the simulation explodes.

## Initial condition: `setFields`

You can write `0/alpha.water` by hand for trivial cases, but it's easier
to use `setFields`:

```c++
// system/setFieldsDict
defaultFieldValues
(
    volScalarFieldValue alpha.water 0          // air everywhere by default
);

regions
(
    boxToCell
    {
        box (0 0 -10) (0.146 0.292 10);        // water column region
        fieldValues
        (
            volScalarFieldValue alpha.water 1
        );
    }
);
```

Then run:

```bash
cp -r 0/alpha.water.orig 0/alpha.water    # if there's a .orig file
setFields
```

This sets `alpha.water = 1` inside the box, `0` outside.

## Required fields

Minimum:

- `0/U`           — velocity (vector)
- `0/p_rgh`       — modified pressure (`p − ρgh`)
- `0/alpha.water` — phase fraction
- `0/k`, `0/epsilon` (or `omega`) — if turbulence enabled

`p` itself is **not** in `0/`; the solver derives it from `p_rgh`.

## Phase properties: `constant/transportProperties`

```c++
phases (water air);

water
{
    transportModel  Newtonian;
    nu              1e-6;             // [m²/s] kinematic viscosity
    rho             1000;             // [kg/m³] density
}

air
{
    transportModel  Newtonian;
    nu              1.48e-5;
    rho             1;
}

sigma           0.07;                  // [N/m] surface tension at the water/air interface
```

Other immiscible pairs (oil/water, mercury/air, etc.): change `nu` and
`rho` for each phase, set sigma appropriately.

## Gravity: `constant/g`

```c++
dimensions      [0 1 -2 0 0 0 0];
value           (0 -9.81 0);          // gravity in -y direction
```

## controlDict for transient VOF

```c++
application     interFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         1.0;                  // physical seconds
deltaT          0.001;                // small initial timestep

writeControl    adjustableRunTime;
writeInterval   0.05;
purgeWrite      0;

runTimeModifiable   yes;

adjustTimeStep      yes;              // CRITICAL: lets the solver shrink dt as needed
maxCo               1.0;              // CFL ceiling for U
maxAlphaCo          1.0;              // CFL ceiling for alpha — usually want 0.5–1.0
maxDeltaT           0.01;
```

## fvSchemes for VOF

```c++
ddtSchemes
{
    default         Euler;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(rhoPhi,U)   Gauss linearUpwind grad(U);
    div(phi,alpha)  Gauss vanLeer;                          // BOUNDED scheme — required
    div(phirb,alpha) Gauss linear;                          // compressive flux
    div(phi,k)      Gauss upwind;
    div(phi,epsilon) Gauss upwind;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}
```

`vanLeer`, `MUSCL`, `vanAlbada` are all valid bounded TVD schemes for
alpha. `vanLeer` is a safe default.

## fvSolution for VOF

```c++
solvers
{
    "alpha.water.*"
    {
        nAlphaCorr      1;
        nAlphaSubCycles 3;            // sub-cycle alpha within each timestep
        cAlpha          1;             // interface compression coefficient
        MULESCorr       yes;
        nLimiterIter    10;

        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0;
    }

    p_rgh
    {
        solver          GAMG;
        smoother        DIC;
        tolerance       1e-7;
        relTol          0.05;
    }

    p_rghFinal
    {
        $p_rgh;
        relTol          0;
    }

    "(U|k|epsilon|omega)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0.1;
    }

    "(U|k|epsilon|omega)Final"
    {
        $U;
        relTol          0;
    }
}

PIMPLE
{
    momentumPredictor       no;       // false for VOF — interface drives pressure
    nOuterCorrectors        1;
    nCorrectors             3;
    nNonOrthogonalCorrectors 0;
}
```

`cAlpha`:
- 1.0 = standard interface compression
- 0.5 = milder
- 1.5 = more aggressive (sharper interface but can introduce parasitic currents)

## Boundary conditions for VOF

### `0/alpha.water`

```c++
dimensions      [0 0 0 0 0 0 0];
internalField   uniform 0;            // initialized by setFields

boundaryField
{
    inletWater
    {
        type        fixedValue;
        value       uniform 1;
    }
    inletAir
    {
        type        fixedValue;
        value       uniform 0;
    }
    atmosphere
    {
        type        inletOutlet;
        inletValue  uniform 0;
        value       uniform 0;
    }
    walls
    {
        type        zeroGradient;
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
    atmosphere
    {
        type        totalPressure;
        p0          uniform 0;
        rho         rho;
        psi         none;
        gamma       1;
        value       uniform 0;
    }
    walls
    {
        type        fixedFluxPressure;
        value       uniform 0;
    }
    frontAndBack
    {
        type        empty;
    }
}
```

### `0/U` for an open atmosphere

```c++
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);

boundaryField
{
    atmosphere
    {
        type        pressureInletOutletVelocity;        // pairs with totalPressure on p_rgh
        value       uniform (0 0 0);
    }
    walls
    {
        type        noSlip;
    }
    frontAndBack
    {
        type        empty;
    }
}
```

## Run sequence

```bash
blockMesh
cp -r 0.orig 0      # if shipped as 0.orig
setFields           # apply setFieldsDict
interFoam           # or `foamRun -solver incompressibleVoF` on Foundation v11
```

For Foundation v11, `interFoam` doesn't exist as a binary — use
`foamRun -solver incompressibleVoF` and put `solver incompressibleVoF`
in `controlDict`.

## Common VOF mistakes

- **Using `linear` for `div(phi,alpha)`**: alpha unbounded → solver
  blows up within a few timesteps. Use `vanLeer`/`MUSCL` always.
- **`maxAlphaCo` not set**: alpha CFL exceeds 1, interface destabilizes.
  Always set `maxAlphaCo 1.0` (or lower for fine interfaces).
- **`maxCo` ceiling too high**: `maxCo 5` works for ordinary PIMPLE but
  is dangerous for VOF — keep it ≤ 1 unless you've validated stability.
- **Forgetting `g`**: solver uses `(0 0 0)` → no gravity → static water
  column doesn't fall. Always set `constant/g`.
- **Wrong pressure field**: writing `0/p` instead of `0/p_rgh` → solver
  ignores your p file and derives from `p_rgh = 0` everywhere.
- **`atmosphere` patch as `wall`**: water can't escape → backflow,
  oscillation, divergence. Use `patch` type with `totalPressure`.
- **`pRefCell` set in PIMPLE block** for an open-atmosphere case: redundant
  (atmosphere already anchors pressure). Set only for closed domains.

## Validation indicators

Healthy VOF run log:

```
Time = 0.05
Courant Number mean: 0.05 max: 0.42
Interface Courant Number mean: 0.001 max: 0.18
deltaT = 0.001
PIMPLE: iteration 1
smoothSolver:  Solving for alpha.water, Initial residual = 1e-3, Final residual = 1e-7
MULES: Solving for alpha.water
Phase-1 volume fraction = 0.0625  Min(alpha.water) = 0  Max(alpha.water) = 1
...
End
```

What to watch:

- `Phase-1 volume fraction` should be **constant** ± numerical noise (mass
  conservation). If it drifts > 1%, something is wrong.
- `Min(alpha.water)` should be `0` and `Max` should be `1` (or extremely
  close). Values like -0.05 or 1.05 = unboundedness, scheme issue.
- `Interface Courant Number max` should be < 1; if > 1 reduce `maxAlphaCo`.
