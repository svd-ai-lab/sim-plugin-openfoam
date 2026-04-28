# Numerics and Schemes

`fvSchemes` selects discretization, `fvSolution` selects linear solvers
and algorithm controls. Wrong choices here cause divergence, slow
convergence, or unphysical results — but the configuration space is
small once you know the patterns.

## `fvSchemes`: the seven blocks

```c++
ddtSchemes        { ... }      // time derivative ∂/∂t
gradSchemes       { ... }      // gradient ∇φ
divSchemes        { ... }      // convection ∇·(Uφ)
laplacianSchemes  { ... }      // diffusion ∇·(ν∇φ)
interpolationSchemes { ... }   // face-value interpolation
snGradSchemes     { ... }      // surface-normal gradient
fluxRequired      { ... }      // (rare) tells solver which fields require flux
```

## Recommended starting point — steady, RANS

```c++
ddtSchemes
{
    default         steadyState;
}

gradSchemes
{
    default         Gauss linear;
    grad(U)         cellLimited Gauss linear 1;     // limit gradient to cell range; helps stability
}

divSchemes
{
    default         none;                            // be explicit; no silent defaults
    div(phi,U)      bounded Gauss linearUpwind grad(U);
    div(phi,k)      bounded Gauss upwind;
    div(phi,epsilon) bounded Gauss upwind;
    div(phi,omega)  bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
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

For mesh non-orthogonality > 65°: replace `corrected` with `limited 0.5`
in `laplacianSchemes` and `snGradSchemes` to tame skewness errors.

## Recommended starting point — transient (PIMPLE)

```c++
ddtSchemes
{
    default         Euler;                  // first-order, robust
    // default      backward;               // second-order, more accurate, less stable
    // default      CrankNicolson 0.9;      // blended, second-order
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(phi,U)      Gauss linearUpwind grad(U);
    div(phi,k)      Gauss upwind;
    div(phi,epsilon) Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
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

## Recommended starting point — VOF (interFoam)

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
    div(phi,alpha)  Gauss vanLeer;                          // bounded scheme; CRITICAL for alpha
    div(phirb,alpha) Gauss linear;                          // compressive flux for sharpness
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

**Critical**: `div(phi,alpha)` MUST be a bounded scheme (`vanLeer`,
`MUSCL`, `vanAlbada`). `linear` (central differencing) on alpha causes
unbounded values — alpha goes negative or > 1 — and the case blows up.

## Convection scheme ladder (stability ↔ accuracy)

From most stable / least accurate → least stable / most accurate:

| Scheme | When |
|---|---|
| `upwind` | First-order. Always stable. Use for first-pass stability. |
| `linearUpwind grad(U)` | Second-order, blended. Good default for momentum. |
| `linearUpwindV grad(U)` | Vector form of linearUpwind. Slightly different blending. |
| `LUST grad(U)` | Linear-Upwind Stabilized Transport. Even sharper. |
| `linear` | Central differencing. Second-order. Can oscillate without limiter. |
| `vanLeer`, `MUSCL`, `SuperBee`, `Minmod` | TVD bounded schemes. Use for `alpha` (VOF) and any field that should stay bounded. |

**Strategy**: start with `upwind` everywhere when stabilizing. Once the
case runs to ~50 iterations without divergence, upgrade `div(phi,U)` to
`linearUpwind grad(U)`. Leave turbulence convection (`div(phi,k)`,
`div(phi,epsilon)`) on `upwind` — it's almost always fine and keeps
turbulence quantities positive.

## `fvSolution`: solver and algorithm

### Solver block (linear-system solvers per field)

```c++
solvers
{
    p
    {
        solver          GAMG;                  // multigrid; fast for pressure
        smoother        GaussSeidel;
        tolerance       1e-7;
        relTol          0.05;                  // intermediate tightness
        nCellsInCoarsestLevel 200;
    }

    pFinal
    {
        $p;
        relTol          0;                     // tight on the final corrector
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
```

Choices:
- `GAMG` for pressure (best for elliptic problems on most meshes)
- `PCG` (preconditioned conjugate gradient) for pressure on small meshes
- `smoothSolver` with `symGaussSeidel` for momentum / scalars
- `PBiCGStab` with `DILU` preconditioner for asymmetric / hard problems

### Algorithm block (depends on solver)

#### `simpleFoam` — SIMPLE (steady)

```c++
SIMPLE
{
    nNonOrthogonalCorrectors 1;       // 0 if mesh non-orth < 35°; 2 if > 65°
    consistent      yes;              // SIMPLEC; allows higher relaxation
    residualControl
    {
        p                   1e-4;
        U                   1e-5;
        "(k|epsilon|omega)" 1e-5;
    }
}

relaxationFactors
{
    fields { p 0.3; }                 // SIMPLEC allows higher: 0.5–0.7
    equations
    {
        U                   0.7;
        "(k|epsilon|omega)" 0.7;
    }
}
```

#### `pimpleFoam` — PIMPLE (transient)

```c++
PIMPLE
{
    nOuterCorrectors    1;            // 1 = pure PISO; >1 = PIMPLE, robust at high CFL
    nCorrectors         2;            // pressure correctors per outer pass
    nNonOrthogonalCorrectors 1;
    momentumPredictor    yes;
    pRefCell             0;            // anchor pressure (closed domain)
    pRefValue            0;
    consistent          no;
}
```

For high-CFL PIMPLE, set `nOuterCorrectors 50` and `momentumPredictor yes`;
the solver iterates SIMPLE-like within each timestep until convergence.

#### `icoFoam` — PISO (transient laminar)

```c++
PISO
{
    nCorrectors         2;
    nNonOrthogonalCorrectors 0;
    pRefCell            0;
    pRefValue           0;
}
```

#### `interFoam` — PIMPLE + alpha-MULES

```c++
PIMPLE
{
    momentumPredictor       no;       // VOF surfaces respond to pressure
    nOuterCorrectors        1;
    nCorrectors             3;
    nNonOrthogonalCorrectors 0;

    nAlphaCorr              1;
    nAlphaSubCycles         3;        // sub-cycle alpha to keep CFL_α < 1
    cAlpha                  1;        // interface compression coefficient

    nLimiterIter            10;
}
```

## Relaxation factor strategy

Relaxation = `φ_new = φ_old + α · (φ_solved − φ_old)`. Lower α = more
under-relaxation = slower but more stable.

For SIMPLE / SIMPLEC starting points (default: `consistent yes`):

| Field | Cold start | Stable | Aggressive |
|---|---|---|---|
| `p` | 0.3 | 0.5 | 0.7 (SIMPLEC only) |
| `U` | 0.5 | 0.7 | 0.9 |
| `k`, `ε`, `ω`, `T` | 0.5 | 0.7 | 0.9 |

Strategy: start cold (column 1), wait for residuals to drop 2 orders,
then bump to "stable" column. Don't go aggressive without watching for
oscillations.

## Algorithm controls — `nOuterCorrectors`, `nCorrectors`, `nNonOrthogonalCorrectors`

| Control | Where it lives | What it does |
|---|---|---|
| `nNonOrthogonalCorrectors` | SIMPLE / PIMPLE / PISO | Extra pressure correction passes for skewed meshes. 0 if non-orth < 35°. |
| `nCorrectors` | PISO / PIMPLE | Number of pressure corrector loops per momentum pass. Typically 2. |
| `nOuterCorrectors` | PIMPLE only | Number of outer (SIMPLE-like) loops per timestep. 1 = PISO; 50+ for high-CFL stability. |

## Common numerics mistakes

- **Setting `default` in any scheme block to `none` and then forgetting
  to specify a derivative** that does appear in the equations: solver
  aborts with `cannot find scheme for ...`. List every term explicitly,
  or fall back to a sensible `default`.
- **`cellLimited` gradient with limiter > 1**: limiter > 1 disables the
  cell-limit, so it's useless. Use 0.5 or 1.0.
- **`nNonOrthogonalCorrectors > 0` on a perfectly orthogonal mesh**: harmless
  but wastes 20-30% wall time per iteration. Drop to 0 for clean meshes.
- **Aggressive relaxation (α=1) on cold start**: classic divergence.
  Start cold, ramp up.
- **Setting `tolerance` very tight (1e-12) on `p`**: solver hits machine
  precision before reaching it, generates NaN. Stay above 1e-8 for `p`
  and 1e-9 for `U`.
- **`linear` for VOF alpha** — see VOF block above. Use bounded scheme.

## Convergence patterns

A "converged" steady-state run:

```
SIMPLE solution converged in 723 iterations
Time = 723
End
```

Or via residualControl: when all listed residuals are below the
threshold, SIMPLE exits.

A "diverging" run:

```
Time = 50
smoothSolver:  Solving for Ux, Initial residual = 1e10, ...    ← residuals SHOULD decrease
```

Diverging residuals usually mean: bad initial conditions, too-aggressive
schemes, mesh quality issue, or wrong BCs. See `error-recovery.md`.
