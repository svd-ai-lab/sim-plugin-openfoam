# Parallel Execution

OpenFOAM uses MPI for parallelism. Decompose mesh into N pieces, run on
N MPI ranks, reconstruct results. Standard for any case > ~100k cells.

## Three-step workflow

```
1. decomposePar           # split mesh + 0/ fields into processor* dirs
2. mpirun -np N <solver> -parallel
3. reconstructPar         # merge processor*/<time>/ back into <time>/
```

## `system/decomposeParDict`

```c++
numberOfSubdomains  4;             // MUST match the -np value at mpirun

method              scotch;        // recommended general-purpose
// method           hierarchical;   // when scotch isn't available
// method           simple;         // axis-aligned slabs

// Coefficients only used by some methods:
hierarchicalCoeffs
{
    n           (2 2 1);            // splits per axis: nx · ny · nz must = numberOfSubdomains
    delta       0.001;
    order       xyz;
}

simpleCoeffs
{
    n           (2 2 1);
    delta       0.001;
}
```

Method selection:

| Method | When |
|---|---|
| `scotch` | Default, complex geometries, no a priori split. Almost always optimal. |
| `metis` | Same use case as scotch; less common but equally good. Build dependency: METIS library. |
| `hierarchical` | Structured meshes / when you want to control the split axes. |
| `simple` | Pure axis-aligned slabs. Trivial; rarely optimal. |
| `manual` | When you want to specify the cell→processor map yourself. |

`scotch` is shipped with OpenFOAM and works on any mesh. Use it unless
you have a reason not to.

## Choosing `numberOfSubdomains`

Rule of thumb: 1 subdomain per ~50k–100k cells. Less = wasted
parallelism; more = MPI communication dominates compute and you slow down.

Examples:

| Mesh size | Recommended `numberOfSubdomains` |
|---|---|
| 50k cells | 1 (don't decompose, run serial) |
| 200k cells | 4 |
| 1M cells | 8–16 |
| 5M cells | 32–64 |
| 20M cells | 128–256 |
| 100M+ cells | 512+ (and reconsider mesh) |

Then **set `mpirun -np N` to the same number**. They MUST match —
mismatch causes either a hang (rank > subdomain count) or processes
exiting silently (rank < subdomain count).

## Run sequence (single host)

```bash
# 1. Mesh + setup as usual
blockMesh
[ -d 0.orig ] && cp -r 0.orig 0
setFields 2>&1     # if needed

# 2. Decompose
decomposePar -force        # -force overwrites existing processor* dirs

# 3. Run
mpirun -np 4 simpleFoam -parallel > log.simpleFoam 2>&1
# (or whatever solver)

# 4. Reconstruct
reconstructPar -newTimes   # only reconstruct times not already on disk
```

For multi-region (CHT) cases, add `-allRegions`:

```bash
decomposePar -allRegions
mpirun -np 4 chtMultiRegionFoam -parallel
reconstructPar -allRegions
```

## Run sequence (cluster / SLURM)

For a SLURM-managed cluster:

```bash
#!/bin/bash
#SBATCH --job-name=of_run
#SBATCH --ntasks=64
#SBATCH --time=04:00:00
#SBATCH --partition=compute

source /etc/openfoam/openfoam.sh
cd $SLURM_SUBMIT_DIR

decomposePar -force
mpirun -np $SLURM_NTASKS simpleFoam -parallel
reconstructPar -newTimes
```

`numberOfSubdomains` in `decomposeParDict` must equal `$SLURM_NTASKS`.

## What you get under the hood

After `decomposePar`:

```
case/
├── processor0/
│   ├── 0/         # the slice of 0/ fields for this rank
│   ├── constant/
│   └── ...
├── processor1/
│   ├── 0/
│   └── ...
├── processor2/
└── processor3/
```

The solver runs in parallel, each rank writing time directories under
its own `processorN/`:

```
processor0/0/
processor0/0.05/
processor0/0.1/
...
```

`reconstructPar` walks these and assembles whole-domain time directories
under the case root.

## Visualizing parallel runs without reconstructing

For ParaView with the OpenFOAM reader: open the .foam stub from the
case root; ParaView reads `processorN/` directly via its parallel reader.
This saves a `reconstructPar` step when you just want to look.

## Common parallel mistakes

- **`numberOfSubdomains != -np`**: hangs or silent failures. Always cross-check.
- **Running `decomposePar` after editing `0/`**: `processor*/0/` is now
  stale. Re-decompose with `-force`.
- **`mpirun` without `-parallel` flag on the solver**: solver runs N
  independent serial copies, each on the full mesh — completely wrong
  results. The `-parallel` flag is mandatory.
- **`reconstructPar` overwriting time directories you wanted to keep
  decomposed**: use `-newTimes` to only assemble what's not already
  whole-domain.
- **Cluster `mpirun` host file conflicts**: when the scheduler provides
  hosts, don't override with `--hostfile`. Let `mpirun` use the
  scheduler's allocation.
- **Decomposing more than ~256 subdomains for ~100M cells**: scotch
  begins to struggle with extreme partition counts. Consider
  `hierarchical` for very large counts.

## Debugging parallel issues

If the solver hangs immediately:

```bash
# Check actual rank count vs decompose count
grep numberOfSubdomains system/decomposeParDict
ls processor* | wc -l        # how many processor dirs exist
```

If MPI complains about "processor boundary mismatch":

```bash
# Stale processor* dirs from a previous decompose with different N
rm -rf processor*
decomposePar -force
```

If runs are extremely slow (per-iteration time same as serial):

```bash
# May be MPI binding wrong, or mesh is so small parallel overhead dominates
# Check: scotch should produce well-balanced subdomains
grep "Number of cells" log.decomposePar
```

## sim-cli integration

For one-shot mode (`sim run`), wrap the parallel sequence in a script:

```python
# solve.py
import subprocess
subprocess.run(["blockMesh"], check=True)
subprocess.run(["decomposePar", "-force"], check=True)
subprocess.run(
    ["mpirun", "-np", "4", "simpleFoam", "-parallel"],
    check=True,
)
subprocess.run(["reconstructPar", "-newTimes"], check=True)
```

Then `sim run solve.py --solver openfoam` runs everything serially as
one trial. The mpirun child process spawns 4 ranks; sim-cli sees one
RunResult.
