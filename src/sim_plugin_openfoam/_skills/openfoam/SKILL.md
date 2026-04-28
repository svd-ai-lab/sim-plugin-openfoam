---
name: openfoam-sim
description: Use when authoring or running OpenFOAM cases through sim-cli. Covers case structure, solver selection, boundary conditions, turbulence/multiphase/heat-transfer setup, mesh generation, numerics, parallel execution, log diagnosis, post-processing, and recovery from common failures. Designed for both ESI v2406+ and OpenFOAM Foundation v11+ unless noted.
---

# openfoam-sim

You are driving **OpenFOAM** through **sim-cli**. This file is the **index**.
Detail lives in `references/` — load progressively, only what the task needs.

---

## How to load this skill

Don't read every reference up front — context is precious. Walk this list:

1. **Always** read `references/case-setup.md` before authoring any case.
2. Pick a solver via `references/solver-selection.md`.
3. Look up the fields & dictionaries you'll need in `references/field-and-dictionary-matrix.md`.
4. For boundary conditions: `references/boundary-conditions.md`.
5. If the case has turbulence: `references/turbulence-setup.md`.
6. If the case is multiphase / VOF: `references/multiphase-vof.md`.
7. If the case has heat or buoyancy: `references/heat-transfer.md` (and `references/conjugate-heat-transfer.md` for solid+fluid).
8. For mesh generation: `references/mesh-and-blockmesh.md`.
9. For schemes / solvers / relaxation: `references/numerics-and-schemes.md`.
10. For runtime monitors / probes / forces: `references/function-objects.md`.
11. For parallel execution and decomposition: `references/parallel-execution.md`.
12. For runtime log diagnosis: `references/log-parsing-and-residuals.md`.
13. For post-processing (sample lines, point queries, integrals): `references/post-processing.md`.
14. For complete case skeletons by scenario: `references/case-recipes.md`.
15. **When something fails**: `references/error-recovery.md` — decision tree + fix sequences.

---

## sim-cli integration (one-shot mode)

Most benchmark/single-shot use is one-shot:

```bash
# 1. Write your driver script. Conventionally `solve.py`.
#    The script invokes blockMesh / solver / postProcess via subprocess,
#    parses the result, and writes the answer to disk.

# 2. Run via sim-cli:
sim run solve.py --solver openfoam

# sim wraps the script in a RunResult (exit_code, stdout, stderr, duration,
# errors) and stores it under `.sim/runs/`. Browse with:
sim logs                     # list runs
sim logs last                # full last RunResult
sim logs last --field exit_code
```

Persistent-session mode (`sim serve` + `sim connect/exec/inspect/disconnect`)
is supported when sim-server is reachable, but is **not** required for
typical case authoring.

---

## Work sequence (the protocol)

Before writing any OpenFOAM file, classify the case:

- **Time**: steady or transient?
- **Compressibility**: incompressible or compressible?
- **Phases**: single-phase, two-phase (VOF), or multi-region?
- **Turbulence**: laminar, RANS (k-ε / k-ω SST / SpalartAllmaras), or LES/DNS?
- **Heat/buoyancy**: isothermal, forced convection, or buoyancy-driven?

This classification fixes the solver family (see `solver-selection.md`),
the required field set (see `field-and-dictionary-matrix.md`), and the
turbulence boundary recipe (see `turbulence-setup.md`).

Then, in this order:

1. **Mesh** (`blockMesh` or `snappyHexMesh`); validate with `checkMesh`.
2. **Fields** in `0/`: one per required field; consistent patch names with the mesh.
3. **Properties** in `constant/`: transport, turbulence, thermophysical (when relevant).
4. **Numerics** in `system/`: `controlDict`, `fvSchemes`, `fvSolution`. Start
   conservative (upwind, low CFL, tight relaxation) and upgrade after the
   case is stable.
5. **Run** the chosen solver; tail the log; check the convergence signals
   (`references/log-parsing-and-residuals.md`).
6. **Post-process** to extract the requested KPI.

Validate at every layer — don't push to "run solver" before `checkMesh` is
clean and the field files reference patches that exist in the mesh.

---

## Hard guardrails

These are mistakes LLMs make often. Don't.

- **Don't invent dictionary keys, patch types, or solver names.** Every key
  in `controlDict` / `fvSchemes` / `fvSolution` / `transportProperties` /
  field files comes from a closed vocabulary. If you're not sure the key
  exists, look it up rather than guess.
- **Don't mix turbulence-model fields.** k-ε needs `k` + `epsilon` + `nut`;
  k-ω SST needs `k` + `omega` + `nut`; Spalart-Allmaras needs `nuTilda` +
  `nut`. Mixing fields across models causes solver to abort at startup.
- **Don't use `p` when the solver expects `p_rgh`.** Buoyant solvers
  (`buoyantBoussinesqSimpleFoam`, `buoyantSimpleFoam`, `chtMultiRegionFoam`)
  and VOF (`interFoam`) want `p_rgh`. Pure incompressible (`icoFoam`,
  `simpleFoam`, `pimpleFoam`) want `p`.
- **Don't use `linear` (central differencing) for `alpha.water` convection
  in VOF.** It's unbounded; `alpha` will blow past [0,1]. Use `vanLeer`
  or `MUSCL` via the `interfaceCompression` family.
- **Don't set relaxation factors to 1.0 in steady-state SIMPLE without
  `consistent yes` (SIMPLEC).** It's a recipe for divergence on most cases.
- **Don't keep aggressive second-order convection schemes on a fragile
  case.** Stabilize with `upwind` first, upgrade to `linearUpwind` once
  residuals are well-behaved.
- **Don't treat `checkMesh` warnings as optional if the log is already
  diverging.** Most divergence on a fresh case is a mesh-quality issue.
- **Don't assume `0/` exists.** Many tutorials ship `0.orig/` and rely on
  `Allrun` to copy it; if you skip Allrun, do it yourself: `cp -r 0.orig 0`.
- **Don't run on more MPI ranks than `numberOfSubdomains` in
  `decomposeParDict`.** They must match, or `mpirun` will hang or crash.

---

## Output expected

When you finish, produce a short summary that states:

- Solver and physics family chosen
- Required fields and dictionaries authored
- Turbulence model + wall treatment (if any) + estimated inlet turbulence
- Numerical schemes used and any relaxation choices
- Convergence signal observed (`End` reached? final residuals? continuity errors?)
- The requested KPI value, with units
- Any stability concerns or follow-up recommendations

For benchmark/grader contexts, this summary is implicit in the produced
`/tmp/agent/result.json` — you still benefit from doing the mental
checklist before submitting.

---

## Reference index

| File | When to read |
|---|---|
| `references/case-setup.md` | Always, first |
| `references/solver-selection.md` | Picking a solver / pressure convention |
| `references/field-and-dictionary-matrix.md` | "What files do I need?" lookup |
| `references/boundary-conditions.md` | Concrete BC syntax per type |
| `references/turbulence-setup.md` | Any turbulent case |
| `references/mesh-and-blockmesh.md` | Mesh generation, `blockMesh`, `checkMesh` |
| `references/numerics-and-schemes.md` | `fvSchemes`, `fvSolution`, relaxation, algorithm controls |
| `references/multiphase-vof.md` | Two-phase / VOF cases |
| `references/heat-transfer.md` | Buoyant or compressible-thermal |
| `references/conjugate-heat-transfer.md` | Multi-region fluid + solid |
| `references/parallel-execution.md` | `decomposePar`, MPI, `reconstructPar` |
| `references/log-parsing-and-residuals.md` | Diagnosing solver progress + convergence |
| `references/post-processing.md` | `postProcess`, `sample`, point queries |
| `references/function-objects.md` | Runtime monitors (probes, forces, yPlus) |
| `references/case-recipes.md` | Complete skeletons by scenario |
| `references/error-recovery.md` | Failure decision tree + fix sequences |
| `references/failure_patterns.md` | Catalog of historical failures (legacy) |
