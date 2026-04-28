# Mesh & blockMesh

Most "solver crashes immediately" failures are mesh issues. Treat mesh
as a first-class concern, validate before solving, fix what `checkMesh`
flags.

## Two meshing paths

| Tool | When |
|---|---|
| `blockMesh` | Structured / hex-dominant, simple geometry definable as a few hex blocks |
| `snappyHexMesh` | Complex geometry from STL; produces a mostly-hex mesh that snaps to the surface |

For benchmark / canonical cases, almost everything is `blockMesh`.

## `blockMeshDict` anatomy

A complete minimal example for a 0.1 × 0.1 × 0.01 m cavity with 20×20×1
cells:

```c++
FoamFile { version 2.0; format ascii; class dictionary; object blockMeshDict; }

scale   1;            // multiplier for vertex coordinates (1 = m, 0.001 = mm)

vertices
(
    (0    0    0)     // 0
    (0.1  0    0)     // 1
    (0.1  0.1  0)     // 2
    (0    0.1  0)     // 3
    (0    0    0.01)  // 4
    (0.1  0    0.01)  // 5
    (0.1  0.1  0.01)  // 6
    (0    0.1  0.01)  // 7
);

blocks
(
    hex (0 1 2 3 4 5 6 7) (20 20 1) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
    movingWall
    {
        type wall;
        faces ((3 7 6 2));
    }
    fixedWalls
    {
        type wall;
        faces
        (
            (0 4 7 3)
            (2 6 5 1)
            (1 5 4 0)
        );
    }
    frontAndBack
    {
        type empty;
        faces
        (
            (0 3 2 1)
            (4 5 6 7)
        );
    }
);
```

## Vertex ordering rules (the hex block)

For each hex block `(v0 v1 v2 v3 v4 v5 v6 v7)`:

```
        7---------6
       /|        /|
      4---------5 |
      | |       | |
      | 3-------|-2          y
      |/        |/           ↑
      0---------1            └→ x
                            z (out of page)
```

- v0..v3 form the bottom face (z = const lower), counterclockwise looking
  down z+
- v4..v7 form the top face (z = const upper), v4 above v0, etc.
- The "right-hand rule" applied to (v0→v1→v2→v3) must point in +z

Get this wrong and `blockMesh` either fails ("invalid face") or produces
inverted (negative-volume) cells.

## Cell counts: `(nx ny nz) simpleGrading (gx gy gz)`

- `(20 20 1)` = 20 cells in x, 20 in y, 1 in z (the "1" makes it 2D-ready)
- `simpleGrading (1 1 1)` = uniform spacing
- `simpleGrading (1 5 1)` = expand factor 5× from low-y to high-y in y direction

For boundary-layer resolution, use a small grading near the wall:
`simpleGrading (1 0.2 1)` = first cell at high-y is 1/5 the size of last
cell at low-y.

For more control, use `multiGradingPair` (multi-segment grading):

```c++
hex (0 1 2 3 4 5 6 7) (50 30 1)
    simpleGrading
    (
        1
        (
            (0.2 0.5 5)        // first 20% of cells, 50% of length, expansion 5
            (0.6 0.0 1)        // middle 60% of cells, 0% (auto), uniform
            (0.2 0.5 0.2)      // last 20% of cells, 50% of length, expansion 1/5
        )
        1
    );
```

## Boundary face notation

Each face is `(v0 v1 v2 v3)` — the four vertex indices going around the
quad. Order: counterclockwise looking from OUTSIDE the cell (so the
outward normal points away from the domain).

For the cavity example above, `movingWall` is the top face (y = 0.1):
the four vertices on that face are 3, 7, 6, 2 (going around). The order
`(3 7 6 2)` is correct — counterclockwise looking from above.

`(2 6 7 3)` would also describe the same face geometrically but with
opposite orientation → outward normal pointing INTO the domain → solver
gets confused. Stick to outward-normal convention.

## Patch types in the boundary block

| Type | When |
|---|---|
| `wall` | Solid no-slip wall. Most BC types apply (noSlip, fixedValue, wall functions). |
| `patch` | Generic open boundary. Use for inlets, outlets, free outflows. |
| `symmetryPlane` | Symmetry plane: zero normal flux, free tangential. |
| `empty` | 2D / 1D dimension reduction. The solver collapses this dimension. |
| `cyclic` | Periodic. Must be paired and have matching geometry. |
| `wedge` | Axisymmetric wedge case. Two patches < 5° apart in θ. |

`empty` is an OpenFOAM convention: front and back of a "2D" slab. The
solver treats fields as 2D in that plane.

## Validation: `checkMesh`

After running `blockMesh`:

```bash
checkMesh -allTopology -allGeometry > log.checkMesh 2>&1
```

What matters in the output:

```
Checking topology...
    Boundary definition OK.
    Cell to face addressing OK.
    Point usage OK.
    Upper triangular ordering OK.
    Face vertices OK.
    Number of regions: 1 (OK).

Checking patch topology for multiply connected surfaces...
    Patch               Faces    Points   Surface topology
    movingWall          20       42       ok (non-closed singly connected)
    fixedWalls          60       82       ok (non-closed singly connected)
    frontAndBack        800      441      ok (non-closed singly connected)

Checking geometry...
    ...
    Mesh non-orthogonality Max: 0 average: 0
    Non-orthogonality check OK.
    ...

Mesh OK.
```

Critical lines:

- `Mesh OK.` (last) → mesh is usable
- `***` prefix anywhere → blocking error, fix before solving
- `Mesh non-orthogonality Max:` → see thresholds below
- `Max skewness` → < 4 generally; > 6 problematic

### Non-orthogonality thresholds

| Max non-orth (degrees) | Action |
|---|---|
| 0–35 | Excellent. Default `nNonOrthogonalCorrectors = 0` is fine. |
| 35–65 | Acceptable. Set `nNonOrthogonalCorrectors = 1` in `fvSolution`. |
| 65–80 | Marginal. Set `nNonOrthogonalCorrectors = 2`, watch for instability. |
| > 80 | Problematic. Mesh quality issue; may need to remesh. |
| > 90 | Unsolvable. Cells are inverted or near-degenerate. |

### Skewness thresholds

| Max skewness | Action |
|---|---|
| < 4 | OK |
| 4–6 | May need lower-order schemes (`upwind` instead of `linearUpwind`) |
| > 6 | Likely divergence; remesh or coarsen |

### Aspect ratio

High aspect-ratio cells (> 1000) near walls are often required for
boundary layers. They're tolerable IF the long axis is along the flow
and not across high-gradient directions.

## Common mesh mistakes

- **Inverted vertex ordering** in the `hex (...)` line → negative-volume
  cells → `checkMesh` fails. Re-check the right-hand rule.
- **Empty `frontAndBack` not declared as type `empty`**: solver runs in 3D
  mode on a 1-cell slab → wrong physics + extreme cost.
- **`scale` set wrong**: vertices in mm but `scale 1` → 1000× bigger
  domain → physics still works but Re is 1000× higher than intended.
  Always check the resulting domain size after `blockMesh`:
  `checkMesh | grep "Overall domain bounding box"`.
- **Patch in `boundary` block doesn't match patch in field files**: solver
  startup fails with "patch <name> not found". Patch names must match
  byte-for-byte (case-sensitive).
- **One block adjacent to another with non-matching face vertices**:
  blocks must share faces exactly (same vertex indices). Otherwise mesh
  has hanging nodes → solver chaos.
- **Skipping `checkMesh`** → wasting hours debugging a divergence that
  was a mesh issue all along.

## When to use `snappyHexMesh`

For STL-based geometry (e.g., motorbike, vehicle, complex internal
ducts). Workflow:

1. Place STL files at `constant/triSurface/`.
2. Run `surfaceFeatureExtract` to extract sharp edges.
3. Run `blockMesh` to create a background mesh covering the STL extent.
4. Run `snappyHexMesh -overwrite` with `snappyHexMeshDict` configured.
5. Validate with `checkMesh`.

See `references/case-recipes.md` for snappy examples.

For simple geometries (cavity, channel, BFS, simple cylinder), stick
with `blockMesh` — it's deterministic and you can hand-write the dict.
