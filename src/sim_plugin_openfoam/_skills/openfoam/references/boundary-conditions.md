# Boundary Conditions

For every patch on every field. Pick the right BC type, write the right
syntax, set physically reasonable values.

## The decision: type per (patch role, field)

A 2x2 mental table for any case:

|  | Velocity field `U` | Pressure field `p` / `p_rgh` |
|---|---|---|
| **Inlet** | `fixedValue` (prescribed velocity) | `zeroGradient` |
| **Outlet** | `zeroGradient` (or `inletOutlet` for backflow) | `fixedValue` (set the gauge pressure, often 0) |
| **No-slip wall** | `noSlip` (or `fixedValue (0 0 0)`) | `zeroGradient` |
| **Slip wall** | `slip` | `zeroGradient` |
| **Symmetry plane** | `symmetryPlane` | `symmetryPlane` |
| **2D front/back** | `empty` | `empty` |
| **Periodic** | `cyclic` (paired) | `cyclic` |
| **Moving wall (lid-driven)** | `fixedValue (1 0 0)` (or whatever lid velocity) | `zeroGradient` |

For scalar fields (T, k, epsilon, omega, alpha):

| Patch role | T | k / ε / ω | alpha |
|---|---|---|---|
| **Inlet** | `fixedValue 300` | `fixedValue` (computed from I, L) | `fixedValue 1` (incoming water) |
| **Outlet** | `inletOutlet inletValue 300` | `inletOutlet` | `zeroGradient` |
| **No-slip wall (smooth)** | `zeroGradient` (adiabatic) or `fixedValue 350` (heated) | wall functions: `kqRWallFunction`, `epsilonWallFunction`, `omegaWallFunction` | `zeroGradient` |
| **Symmetry / empty / cyclic** | match `U`'s choice | match | match |

## Concrete syntax — common types

### `fixedValue` (Dirichlet)
Force the field to a specific value on the patch.

```c++
inlet
{
    type        fixedValue;
    value       uniform (1 0 0);   // for vectors
    // value    uniform 300;       // for scalars
}
```

### `zeroGradient` (Neumann ∂φ/∂n = 0)

```c++
outlet
{
    type        zeroGradient;
}
```

### `inletOutlet` (mixed: outflow until backflow detected)
Critical for outlets that may experience reverse flow (recirculation).

```c++
outlet
{
    type        inletOutlet;
    inletValue  uniform (0 0 0);   // value during backflow
    value       uniform (0 0 0);   // initial guess
}
```

For scalars at outlet: `inletOutlet inletValue 300; value 300;`.

### `noSlip` (= `fixedValue (0 0 0)` for U)

```c++
walls
{
    type        noSlip;
}
```

### `slip` (free-slip wall: zero normal velocity, free tangential)

```c++
slipWall
{
    type        slip;
}
```

### `symmetryPlane`

```c++
symLR
{
    type        symmetryPlane;
}
```

### `empty` (2D dimension reduction)

```c++
frontAndBack
{
    type        empty;
}
```

Both the patch in `constant/polyMesh/boundary` AND every field in `0/`
must declare type `empty`. Use only on faces that are normal to the
"flat" dimension of a quasi-2D case.

### `cyclic` (periodic)

The two halves of a periodic pair must be set up at mesh-creation time
(via `blockMeshDict` or `createPatch`). Once paired, just:

```c++
periodic1
{
    type        cyclic;
}
periodic2
{
    type        cyclic;
}
```

Field BCs use `cyclic` on both halves.

### `totalPressure` (open atmosphere outlet for VOF, compressible)

```c++
atmosphere
{
    type        totalPressure;
    p0          uniform 0;
    rho         rho;
    psi         none;
    gamma       1;
    value       uniform 0;
}
```

### `pressureInletOutletVelocity` (paired with totalPressure for VOF)

For the velocity field on a `totalPressure` patch:

```c++
atmosphere
{
    type        pressureInletOutletVelocity;
    value       uniform (0 0 0);
}
```

## Wall functions for turbulence

When using RANS with high-Re wall functions:

| Field | Wall BC |
|---|---|
| `k` | `kqRWallFunction` |
| `epsilon` | `epsilonWallFunction` |
| `omega` | `omegaWallFunction` |
| `nut` | `nutkWallFunction` (k-ε) or `nutUSpaldingWallFunction` (k-ω SST, low-Re flexible) |
| `nuTilda` | `fixedValue uniform 0` (Spalart-Allmaras) |
| `T` (with turbulence) | depending on heat BC; `fixedValue` for known wall T |
| `alphat` | `compressible::alphatJayatillekeWallFunction` or `compressible::alphatWallFunction` |

For low-Re wall-resolved RANS (y+ < 5):

- `nut`: `nutLowReWallFunction` or `fixedValue uniform 0`
- `omega`: `omegaWallFunction` (it auto-switches based on y+)

## Inlet turbulence value estimation

Inlet `k`, `epsilon`, `omega` aren't free parameters — estimate from
turbulence intensity `I` and length scale `L`:

```
k       = (3/2) · (I · |U|)²
epsilon = Cμ^(3/4) · k^(3/2) / L
omega   = k^(1/2) / (Cμ^(1/4) · L)
```

Where `Cμ = 0.09` (k-ε constant). Choose:

- **`I`** (turbulence intensity): 0.05 (5%) for free-stream, 0.1 (10%) for
  swirl/jet, 0.01 (1%) for very clean inlet.
- **`L`** (length scale): a fraction of the inlet hydraulic diameter,
  typically `L ≈ 0.07 · D_h` for fully developed pipe flow, or just the
  characteristic geometric length for general flow.

For `|U| = 10 m/s`, `I = 0.05`, `D_h = 0.1 m`, `L = 0.007`:

```
k       = 1.5 × (0.05 × 10)² = 0.375 m²/s²
epsilon = 0.09^0.75 × 0.375^1.5 / 0.007 ≈ 1.27 m²/s³
omega   = 0.375^0.5 / (0.09^0.25 × 0.007) ≈ 159 1/s
```

`nut` at inlet: `fixedValue 0` is fine; the turbulence model will
populate it after the first iteration.

## Example: complete `0/U` for a 2D channel with k-ε

```c++
FoamFile { version 2.0; format ascii; class volVectorField; object U; }

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);

boundaryField
{
    inlet
    {
        type        fixedValue;
        value       uniform (10 0 0);
    }
    outlet
    {
        type        inletOutlet;
        inletValue  uniform (0 0 0);
        value       uniform (0 0 0);
    }
    upperWall
    {
        type        noSlip;
    }
    lowerWall
    {
        type        noSlip;
    }
    frontAndBack
    {
        type        empty;
    }
}
```

## Example: `0/k` matching the above (I=5%, L=0.007 m)

```c++
FoamFile { version 2.0; format ascii; class volScalarField; object k; }

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0.375;

boundaryField
{
    inlet
    {
        type        fixedValue;
        value       uniform 0.375;
    }
    outlet
    {
        type        inletOutlet;
        inletValue  uniform 0.375;
        value       uniform 0.375;
    }
    upperWall
    {
        type        kqRWallFunction;
        value       uniform 0.375;
    }
    lowerWall
    {
        type        kqRWallFunction;
        value       uniform 0.375;
    }
    frontAndBack
    {
        type        empty;
    }
}
```

## Common BC mistakes

- **Velocity `fixedValue` at outlet**: enforces a specific outflow velocity,
  but pressure now has nothing to fix it → solver picks a constant offset
  freely → unphysical. Use `zeroGradient` for `U` at outlet, `fixedValue` for `p`.
- **Pressure `fixedValue` at every patch**: over-determined. Pick exactly
  one patch where you set pressure (typically the outlet), and use
  `zeroGradient` everywhere else.
- **`noSlip` on a non-wall patch**: causes a hidden `fixedValue (0 0 0)`
  velocity that the inlet/outlet was supposed to manage. Use only on
  walls.
- **Wall functions with too-fine mesh** (y+ < 1): the wall-function
  formulas blow up as y+ → 0. Use low-Re BCs (`nutLowReWallFunction`)
  or coarsen the wall layer.
- **Forgetting `empty` on a 2D case**: solver treats it as 3D, takes
  forever to "converge", and gives wrong answers. The mesh AND fields
  both need `empty`.
- **Mismatched `value` and `inletValue` for `inletOutlet`**: when backflow
  occurs, `inletValue` kicks in; setting it differently from steady inlet
  causes oscillations.
