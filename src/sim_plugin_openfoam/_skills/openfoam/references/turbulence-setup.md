# Turbulence Setup

The single largest source of "case won't converge / blows up at startup"
errors. Pick the model + wall treatment + inlet values + wall functions
together — they couple.

## Decision: which turbulence model?

```
Is the flow turbulent at all? (Re_characteristic > ~2300 for pipe; > 10⁴ for free flows)
├── No → laminar → don't add a turbulence model; `turbulenceProperties.simulationType = laminar`
└── Yes:
    ├── Need time-resolved eddies (DNS / LES)?
    │   ├── Strict DNS → `dnsFoam`, periodic box, no model. Need very fine mesh.
    │   └── LES → simulationType LES, model Smagorinsky / oneEqEddy / dynamicKEqn
    └── RANS (steady or transient ensemble-average)?
        ├── Standard incompressible workhorse → kOmegaSST (best general-purpose)
        ├── External aero / wall-bounded boundary layers → kOmegaSST or SpalartAllmaras
        ├── Confined flows / industrial → kEpsilon (cheap, robust, less accurate near walls)
        ├── Strong adverse pressure gradient (separation) → kOmegaSST
        ├── Free shear / jets → realizableKE
        └── Heavily separated bluff body → consider DES/IDDES (advanced)
```

When in doubt, **`kOmegaSST`** is the safest first pick for generic
external/internal flow. `kEpsilon` is fine for ducted/confined flows
where wall y+ ≥ 30 is achievable.

## RANS configuration

In `constant/turbulenceProperties` (ESI) or `constant/momentumTransport`
(Foundation v11):

```c++
simulationType  RAS;

RAS
{
    RASModel        kOmegaSST;       // or kEpsilon, realizableKE, SpalartAllmaras
    turbulence      on;
    printCoeffs     on;
}
```

Required `0/` fields (see `field-and-dictionary-matrix.md`):

- k-ε family: `k`, `epsilon`, `nut`
- k-ω family: `k`, `omega`, `nut`
- Spalart-Allmaras: `nuTilda`, `nut`

## Wall treatment: high-Re vs low-Re

You have a choice based on first-cell-center y+:

| Mesh y+ at wall | Wall treatment | `nut` BC | Notes |
|---|---|---|---|
| 30 ≤ y+ ≤ 300 | High-Re wall function | `nutkWallFunction` (k-ε) or `nutUSpaldingWallFunction` (k-ω SST) | Standard industrial. Mesh first cell in log layer. |
| 1 ≤ y+ ≤ 30 | "Buffer-layer trouble zone" | Same as above; results sensitive | Avoid this band |
| y+ < 1 | Low-Re (wall-resolved) | `nutLowReWallFunction` or `fixedValue 0` | Need 5+ layers below y+ = 5 |

Wall-function variants in OpenFOAM:

- `nutkWallFunction` — standard k-ε, log-law for `nut`
- `nutUSpaldingWallFunction` — Spalding's continuous formula; behaves
  better in the buffer layer (y+ ≈ 5–30); good default for k-ω SST
- `nutkAtmRoughWallFunction` — for atmospheric BL with roughness
- `nutLowReWallFunction` — auto-switch based on y+

For `epsilon` and `omega` at walls, always use the matching wall function:

- `epsilonWallFunction` (k-ε)
- `omegaWallFunction` (k-ω SST — auto-switches with y+)

For `k`:

- `kqRWallFunction` — high-Re; sets a near-wall production-equilibrium k
- `kLowReWallFunction` — low-Re

## Estimating y+ before running

You can't measure y+ until after the first solve. Estimate from
boundary-layer correlations:

```
For a flat plate at Re_L = U·L/ν:
  Cf  ≈ 0.026 / Re_x^(1/7)               (turbulent BL skin friction)
  τw  = (1/2) · ρ · U² · Cf
  uτ  = sqrt(τw / ρ)
  y_first_cell = (y+ · ν) / uτ
```

For a target y+ = 50 in air at 10 m/s along a 1 m plate:

```
Re_L = 10 · 1 / 1.5e-5 = 6.7e5
Cf   ≈ 0.026 / (6.7e5)^(1/7) ≈ 0.0029
τw   = 0.5 · 1.2 · 100 · 0.0029 ≈ 0.174 Pa
uτ   = sqrt(0.174 / 1.2) ≈ 0.38 m/s
y_first_cell = 50 · 1.5e-5 / 0.38 ≈ 2.0e-3 m  (2 mm)
```

So mesh the first cell about 2 mm thick; expand by ~20% per layer.

After the first run, check actual y+:

```bash
postProcess -func 'yPlus' -latestTime
```

Or as a function object during the run (see
`references/function-objects.md`).

## Inlet `k`, `epsilon`, `omega` values

Don't make these up. Compute from inlet turbulence intensity `I` and
turbulence length scale `L`:

```
k       = (3/2) · (I · U_inlet)²
epsilon = Cμ^(3/4) · k^(3/2) / L         where Cμ = 0.09
omega   = k^(1/2) / (Cμ^(1/4) · L)
```

Typical `I`:
- 0.01–0.02 (1–2%): wind tunnel quality
- 0.05 (5%): generic free-stream / inlet
- 0.10 (10%): high-turbulence inlet (after a swirler)

Typical `L`:
- 0.07 · `D_h` for fully developed pipe flow (D_h = hydraulic diameter)
- A geometric length for confined flows (e.g., the inlet height)
- Smaller (mm scale) for fine-scale turbulence inlet

For `U = 10 m/s`, `I = 0.05`, `D_h = 0.0254 m`, `L = 0.0018 m` (BFS-style):
- k = 0.375 m²/s²
- ε = 11.6 m²/s³
- ω = 1080 1/s (you'd choose either ε or ω based on model)

Boundary file for inlet then sets `fixedValue` to those numbers.

## Steady RANS convergence pattern

Healthy `simpleFoam` + RANS log over iterations:

```
Time = 1
smoothSolver:  Solving for Ux, Initial residual = 1, Final residual = 0.001
smoothSolver:  Solving for Uy, Initial residual = 1, Final residual = 0.001
smoothSolver:  Solving for k, Initial residual = 1, Final residual = 0.05
smoothSolver:  Solving for epsilon, Initial residual = 1, Final residual = 0.1
GAMG:          Solving for p, Initial residual = 1, Final residual = 0.001
...
Time = 500
smoothSolver:  Solving for Ux, Initial residual = 1e-4, Final residual = 1e-7
...
SIMPLE solution converged in 723 iterations
End
```

What to watch for:

- Residuals dropping ~2 orders / 100 iterations early on; flatter later
- `Ux`, `Uy`, `Uz` similar magnitudes (asymmetric residuals → mesh issue)
- `k` and `ε` (or `ω`) following `U` — if they shoot up while `U` drops,
  turbulence is exploding (see error-recovery)
- "bounding k/epsilon/omega" warnings: turbulence quantities going
  negative are being clipped to a floor — your inlet values may be too
  low or too high

## Common turbulence mistakes

- **Mixing models' fields**: writing `0/k` and `0/epsilon` then setting
  `RAS.RASModel = kOmegaSST` (which wants `omega`, not `epsilon`). The
  solver demands what the model declares; extra files are tolerated but
  missing ones abort.
- **Wall functions on no-slip wall but `nutLowReWallFunction` config
  pointing at low-Re mesh**: mismatch between mesh and BC. Decide your
  y+ target FIRST, mesh accordingly, then pick wall function.
- **`omega = 0` or `epsilon = 0` on a wall as `fixedValue`**: divergence
  by division-by-zero. Always use the matching `*WallFunction` BC, never
  a literal `fixedValue 0`.
- **Forgetting to set `turbulence on`**: model is loaded but production /
  destruction terms are zero → laminar effective. Check
  `turbulenceProperties` block.
- **`k` BC at outlet = `zeroGradient`** when there's recirculation: you'll
  pull the (large) interior k back into the domain. Use `inletOutlet`.

## Foundation v11 differences

- Selection is in `constant/momentumTransport`, key is `model` (not `RASModel`):

```c++
simulationType  RAS;
RAS
{
    model           kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
```

- Otherwise field set + wall functions are essentially the same.
