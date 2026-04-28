# Post-Processing

After the solver finishes, you usually need to extract a quantity:
velocity at a point, force on a wall, integrated mass flow, sample line
through the domain. OpenFOAM has structured tools for all of this.

## The `postProcess` utility

```bash
postProcess -func <name> [-latestTime | -time T1:T2]
```

`-latestTime` operates only on the latest written time directory; useful
when you want a single snapshot.

Common `-func` values:

| Function | Purpose |
|---|---|
| `sample` | Sample fields along lines, planes, or sets |
| `writeCellCentres` | Dump cell-centre coordinates as `C` field |
| `writeCellVolumes` | Dump cell volumes as `V` field |
| `mag(U)` | Compute and write magnitude of vector field |
| `Q` | Compute Q-criterion (vortex visualization) |
| `vorticity` | Compute curl(U) |
| `yPlus` | Compute y+ on walls |
| `forces` | Integrate force/moment on a patch |
| `forceCoeffs` | Cd/Cl/Cm coefficients |

## `sample` — line / plane / point extraction

The `sample` function uses `system/sampleDict` to define what to sample.

### Line along x at constant y, z

```c++
type            sets;
libs            (sampling);
interpolationScheme cellPoint;
setFormat       raw;

sets
(
    centerline
    {
        type        uniform;
        axis        x;                   // independent variable along the line
        start       (0    0.05 0.005);   // line endpoints
        end         (1.0  0.05 0.005);
        nPoints     200;
    }
);

fields ( U p );
```

Run:

```bash
postProcess -func sampleDict -latestTime
```

Output lands in `postProcessing/sampleDict/<time>/`:

```
postProcessing/sampleDict/2/
├── centerline_U.xy        # x  Ux  Uy  Uz   per row
├── centerline_p.xy        # x  p           per row
```

The format is space-separated text, one row per sample point. Trivial to
parse with awk or numpy.

### Sample at a single point

A "single point" is just a 1-point line:

```c++
sets
(
    centerPoint
    {
        type        uniform;
        axis        x;
        start       (0.05 0.05 0.005);
        end         (0.05 0.05 0.005);
        nPoints     1;
    }
);
```

Or use `cloud` for arbitrary point sets:

```c++
sets
(
    probes
    {
        type        cloud;
        axis        xyz;
        points
        (
            (0.05 0.05 0.005)
            (0.10 0.05 0.005)
            (0.15 0.05 0.005)
        );
    }
);
```

### Sample on a 2D plane

```c++
type            surfaces;
libs            (sampling);
interpolationScheme cellPoint;
surfaceFormat   raw;

surfaces
(
    plane_y0_05
    {
        type        plane;
        planeType   pointAndNormal;
        pointAndNormalDict
        {
            point   (0 0.05 0);
            normal  (0 1 0);
        }
    }
);

fields ( U p );
```

## Manual extraction without `sample`: parse `internalField`

If you don't want to add a `sampleDict` and re-run `postProcess`, parse
the field file directly. OpenFOAM writes the latest fields under
`<latestTime>/<field>` in this format:

```
internalField   nonuniform List<vector>
400
(
(0.0 0.0 0.0)
(0.001 0.0 0.0)
(0.002 0.0 0.0)
...
)
;
```

For a vector field, parse with regex:

```python
import re

text = open(f"{case_dir}/2/U").read()

m = re.search(
    r"internalField\s+nonuniform\s+List<vector>\s*\d+\s*\((.*?)\)\s*;",
    text, re.DOTALL,
)
if m:
    body = m.group(1)
    cells = [
        tuple(float(x) for x in v.groups())
        for v in re.finditer(r"\(([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)\)", body)
    ]
    # cells is now a list of (Ux, Uy, Uz) tuples, indexed by cell ID
```

For a scalar field:

```python
m = re.search(
    r"internalField\s+nonuniform\s+List<scalar>\s*\d+\s*\((.*?)\)\s*;",
    text, re.DOTALL,
)
if m:
    values = [float(x) for x in m.group(1).split()]
```

For a `uniform` field (constant value):

```
internalField   uniform 0;
```

Parse this branch separately:

```python
m_uni = re.search(r"internalField\s+uniform\s+([\d.eE+-]+)", text)
if m_uni:
    value = float(m_uni.group(1))   # constant for every cell
```

## Find the cell nearest a point (without sample)

If you have cell centres (run `postProcess -func writeCellCentres -latestTime`
first), this is a single nearest-neighbour search:

```python
# Assuming u_field and c_field are lists of (x,y,z) tuples
target = (0.05, 0.05, 0.005)
best_d2 = float("inf")
u_at_target = None
for c, u in zip(c_field, u_field):
    d2 = sum((c[i] - target[i])**2 for i in range(3))
    if d2 < best_d2:
        best_d2 = d2
        u_at_target = u
```

This avoids needing a `sampleDict` entirely.

## Integrating quantities

### Mass flow rate through an outlet patch

```c++
// Add to system/controlDict, in functions{} block:
functions
{
    outletFlow
    {
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        regionType      patch;
        name            outlet;
        operation       sum;
        writeFields     no;
        fields          ( phi );          // phi is the volumetric flux
    }
}
```

After the run, `postProcessing/outletFlow/0/surfaceFieldValue.dat` lists
phi sum (= volumetric flow rate) over time.

### Force / moment on a wall

```c++
functions
{
    forces1
    {
        type            forces;
        libs            (forces);
        patches         ( walls );
        rho             rhoInf;
        rhoInf          1;                 // for incompressible: kinematic
        CofR            (0 0 0);
    }
}
```

After the run, `postProcessing/forces1/0/force.dat` lists
`(Fx Fy Fz) (Mx My Mz)` per timestep.

### Cd, Cl coefficients

```c++
functions
{
    forceCoeffs1
    {
        type            forceCoeffs;
        libs            (forces);
        patches         ( object );
        rho             rhoInf;
        rhoInf          1;
        liftDir         (0 1 0);
        dragDir         (1 0 0);
        CofR            (0 0 0);
        pitchAxis       (0 0 1);
        magUInf         10;
        lRef            1;
        Aref            1;
    }
}
```

`postProcessing/forceCoeffs1/0/forceCoeffs.dat` has `Cd Cl Cm` per
timestep.

## Reattachment length (BFS-style)

Standard recipe: sample velocity along a line just above the lower wall,
find where streamwise velocity changes sign.

```c++
sets
(
    wallSample
    {
        type        uniform;
        axis        x;
        start       (0.0  -0.0249 0.005);   // y just above the lower wall
        end         (0.30 -0.0249 0.005);
        nPoints     500;
    }
);

fields ( U );
```

Then in Python:

```python
data = []
for line in open("postProcessing/sampleDict/<time>/wallSample_U.xy"):
    parts = line.split()
    if len(parts) >= 4:
        x, ux, uy, uz = map(float, parts)
        data.append((x, ux))

# Find first x > 0 where ux changes sign (negative → positive)
x_r = None
for i in range(1, len(data)):
    if data[i-1][0] > 0 and data[i-1][1] < 0 and data[i][1] >= 0:
        x_r = data[i-1][0] + (data[i][0] - data[i-1][0]) * (
            -data[i-1][1] / (data[i][1] - data[i-1][1])
        )
        break
```

## Probes (time-history at fixed points)

For a transient run:

```c++
functions
{
    probes
    {
        type            probes;
        libs            (sampling);
        writeControl    timeStep;
        writeInterval   1;
        fields          ( U p );
        probeLocations
        (
            (0.05 0.05 0.005)
            (0.10 0.05 0.005)
        );
    }
}
```

`postProcessing/probes/0/U` contains time-history per probe.

## Common post-processing mistakes

- **Forgetting `-latestTime`** when only the final state matters: `postProcess`
  runs over every time directory, taking 5× longer.
- **Patch name in `sampleDict` doesn't exist in mesh**: silent failure, no
  output file.
- **`fields ( U p )` with vector and scalar mixed and `setFormat raw`**:
  output files are separate per field, but make sure your reader knows
  which is which.
- **Sampling a point that's outside the mesh**: silently returns zero or
  whatever the interpolator decides. Validate the point is inside the
  domain bounds first.
- **`writeCellCentres` BEFORE running the solver**: produces nothing useful.
  Run AFTER, on `latestTime`, so cell centres are computed against the
  written mesh.

## ParaView integration

Touch a `.foam` file at the case root and open it in ParaView:

```bash
touch case.foam
```

ParaView's OpenFOAM reader picks up all time directories and field files
automatically. Use this for visual inspection — much faster than writing
sample dicts for exploratory work.
