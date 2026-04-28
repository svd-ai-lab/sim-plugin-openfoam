# Function Objects (Runtime Monitors)

Function objects run **during** the solver loop, at intervals you
control. They write output to `postProcessing/<name>/<time>/`. Use for:

- runtime probes (sample fields without stopping the solver)
- forces / coefficients on patches
- y+ monitoring during the run (catch wall-mesh issues early)
- field-average / running statistics
- cell- and patch-integrated quantities

Function objects live in `system/controlDict` under a top-level
`functions { ... }` block, OR in separate dicts pulled in via `#include`.

## Anatomy

```c++
// system/controlDict
functions
{
    <funcName>
    {
        type                <funcType>;            // e.g. probes, forces, yPlus
        libs                (<libraryName>);       // e.g. sampling, forces, fieldFunctionObjects
        writeControl        timeStep;
        writeInterval       100;                    // every 100 timesteps
        fields              ( U p );                // (when relevant)
        // ...other type-specific keys...
    }
}
```

Multiple function objects can coexist. Common combo: probes + forces +
yPlus.

## Probes — sample fields at fixed points during the run

```c++
probes
{
    type            probes;
    libs            (sampling);
    writeControl    timeStep;
    writeInterval   10;
    fields          ( U p );
    probeLocations
    (
        (0.05 0.05 0.005)
        (0.10 0.05 0.005)
        (0.15 0.05 0.005)
    );
}
```

Output: `postProcessing/probes/0/U` and `.../p`. Format: time + value
per probe per row.

Use this when you want to watch a quantity evolve over time without
sampling every saved time directory afterwards.

## Forces and coefficients — wall integrations

```c++
forces1
{
    type            forces;
    libs            (forces);
    writeControl    timeStep;
    writeInterval   1;
    patches         ( object );          // wall patch(es) to integrate
    rho             rhoInf;
    rhoInf          1.0;                  // kinematic for incompressible
    CofR            (0 0 0);              // centre of rotation for moments
}

forceCoeffs1
{
    type            forceCoeffs;
    libs            (forces);
    writeControl    timeStep;
    writeInterval   1;
    patches         ( object );
    rho             rhoInf;
    rhoInf          1.0;
    liftDir         (0 1 0);
    dragDir         (1 0 0);
    CofR            (0 0 0);
    pitchAxis       (0 0 1);
    magUInf         10;
    lRef            1;
    Aref            1;
}
```

Output:
- `forces1/0/force.dat` — `time (Fx Fy Fz) (Mx My Mz)` per row
- `forceCoeffs1/0/forceCoeffs.dat` — `time Cd Cl Cm Cd_l Cd_p ...`

## y+ monitoring — catch wall-mesh issues during the run

```c++
yPlus
{
    type            yPlus;
    libs            (fieldFunctionObjects);
    writeControl    runTime;
    writeInterval   0.1;                   // every 0.1s of physical time
    patches         ();                     // empty = all wall patches
}
```

Output: `postProcessing/yPlus/<time>/yPlus.dat` lists per-patch y+
statistics: min, max, average. Watch for:

- **min y+ << 1** with high-Re wall functions: mesh too fine; either
  use low-Re BCs or coarsen
- **max y+ > 300**: wall function may extrapolate poorly; refine
- **patch y+ varying widely** (max/min > 100): irregular mesh

Adding this from the start tells you about wall-mesh health within the
first few timesteps — much faster than running to "convergence" then
discovering the wall mesh was wrong.

## Field-average — running mean over time

```c++
fieldAverage1
{
    type            fieldAverage;
    libs            (fieldFunctionObjects);
    writeControl    writeTime;
    timeStart       0.5;                   // start averaging after t = 0.5s (skip transient)
    fields
    (
        U
        {
            mean        on;
            prime2Mean  on;                // include UU' (Reynolds stress)
            base        time;
        }
        p { mean on; }
    );
}
```

Useful for LES / DES post-processing: sample mean and Reynolds-stress
fields after the initial transient. Output gets baked into time
directories as `UMean`, `pMean`, `UPrime2Mean`, etc.

## Surface field value — patch-integrated quantities

For e.g. mass flow through an outlet patch:

```c++
outletFlow
{
    type            surfaceFieldValue;
    libs            (fieldFunctionObjects);
    writeControl    timeStep;
    writeInterval   10;
    regionType      patch;
    name            outlet;
    operation       sum;
    writeFields     no;
    fields          ( phi );               // volumetric flux
}
```

`operation`: `sum` | `average` | `weightedAverage` | `min` | `max` |
`areaIntegrate` | `volIntegrate`.

For mass flow weighted by density (compressible):

```c++
operation       weightedAverage;
weightField     phi;
fields          ( T );          // average T weighted by phi (mass flow)
```

## Volume field value — domain-integrated quantities

For total kinetic energy:

```c++
totalKE
{
    type            volFieldValue;
    libs            (fieldFunctionObjects);
    writeControl    timeStep;
    writeInterval   10;
    regionType      all;
    operation       volIntegrate;
    writeFields     no;
    fields          ( k );                 // resolved TKE; for DNS use 0.5*|U|^2
}
```

For mean TKE in DNS isotropic turbulence: pre-compute `0.5*magSqr(U)` as a
new field via `mag` function object, then `volIntegrate` it.

## Stop the run when a condition is met

```c++
stopWhenSteady
{
    type            runTimeControl;
    libs            (utilityFunctionObjects);
    conditions
    {
        Uconverged
        {
            type            average;
            functionObject  Uavg;
            fields          ( U );
            tolerance       1e-5;
            window          1.0;            // average over 1.0s
            windowType      exact;
        }
    }
    satisfiedAction end;
}
```

Useful for transient cases that asymptote to steady but you can't
predict when. The solver writes "End" when the condition triggers.

## Multiple function objects via `#include`

For tidiness, keep function objects in their own files:

```c++
// system/controlDict
functions
{
    #include "monitors"          // pulls in system/monitors
    #include "probes"            // pulls in system/probes
}
```

Each included file is a `functions { ... }` block on its own.

## Common function-object mistakes

- **Wrong `libs ( ... )`** for the function type: function objects refuse
  to load. Common pairings:
  - `probes`, `sample`, `surfaces`, `sets`           → `(sampling)`
  - `forces`, `forceCoeffs`                          → `(forces)`
  - `yPlus`, `mag`, `Q`, `vorticity`, `divergence`,
    `surfaceFieldValue`, `volFieldValue`, `fieldAverage` → `(fieldFunctionObjects)`
  - `runTimeControl`                                 → `(utilityFunctionObjects)`
- **Patch name doesn't exist**: silently writes nothing. Check patch
  names match `constant/polyMesh/boundary`.
- **`writeControl timeStep` + `writeInterval 1`**: writes every step;
  output files balloon. Use `writeInterval 100` or `writeControl writeTime`.
- **`fieldAverage` with `timeStart 0`** on a transient case: the average
  is contaminated by the startup transient. Set `timeStart` after
  initial transient settles.
- **Forgetting `rhoInf`** for `forces` on incompressible cases: defaults
  to `1.0` but only if you set `rho rhoInf`. Without `rho`, forces are
  in dimensional confusion.
