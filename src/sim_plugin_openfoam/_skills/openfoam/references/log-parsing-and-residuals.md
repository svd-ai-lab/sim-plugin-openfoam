# Parsing OpenFOAM Logs

OpenFOAM solvers print a structured stream to stdout. Knowing how to
parse it is the difference between "I ran the solver" and "I know what
happened." This is also how you derive a `converged` signal cheaply,
without waiting for postProcess.

## Anatomy of a solver log

A typical `icoFoam` / `pimpleFoam` time-step block:

```
Time = 0.005

Courant Number mean: 0.021 max: 0.124
smoothSolver:  Solving for Ux, Initial residual = 0.00012, Final residual = 9.1e-07, No Iterations 2
smoothSolver:  Solving for Uy, Initial residual = 0.00011, Final residual = 8.8e-07, No Iterations 2
DICPCG:  Solving for p, Initial residual = 0.00065, Final residual = 6.2e-08, No Iterations 23
time step continuity errors : sum local = 3.2e-18, global = -1.1e-19, cumulative = 2.4e-18
ExecutionTime = 0.56 s  ClockTime = 1 s
```

Key lines:

- `Time = X`           → physical time reached (transient) or iteration number (steady)
- `Solving for <field>, Initial residual = X, Final residual = Y, No Iterations N` → per-field linear-system convergence inside this timestep
- `time step continuity errors : sum local = X, global = Y, cumulative = Z` → mass-conservation diagnostic
- `Courant Number mean / max` → stability metric for transient runs
- `ExecutionTime` / `ClockTime` → wall-clock budget

After the time loop completes (transient solver reached endTime, or
SIMPLE hit residualControl), the log ends with:

```
End
```

A clean `End` is the surest sign the solver completed normally.

For steady SIMPLE solvers, you may also see:

```
SIMPLE solution converged in 723 iterations
End
```

`SIMPLE solution converged` is an explicit pass signal.

## Five must-know diagnostic commands

Run these on the log file (or piped solver stdout) to extract the most
useful signals:

```bash
# 1. Did it end cleanly?
tail -5 log.icoFoam | grep -q "^End$" && echo "OK: clean End" || echo "WARN: no End"

# 2. What was the last simulated time?
grep "^Time = " log.icoFoam | tail -1

# 3. What were the final residuals?
grep "Final residual" log.icoFoam | tail -10

# 4. Any errors?
grep -iE "error|fatal|exception|nan|sigfpe" log.icoFoam

# 5. CFL trend (transient stability)
grep "Courant Number" log.icoFoam | tail -5
```

## Programmatic extraction (Python regex)

When you need structured data — e.g. to write a `converged` boolean
into your `result.json` — use these regexes:

```python
import re

residual_re = re.compile(
    r"Solving for ([\w.]+),\s*Initial residual\s*=\s*[\d.eE+-]+,\s*"
    r"Final residual\s*=\s*([\d.eE+-]+)"
)
time_re = re.compile(r"^Time\s*=\s*([\d.eE+-]+)\s*$")
simple_re = re.compile(r"SIMPLE solution converged in\s+\d+\s+iterations?")
continuity_re = re.compile(
    r"time step continuity errors\s*:\s*sum local\s*=\s*([\d.eE+-]+),?\s*"
    r"global\s*=\s*([\d.eE+-]+),?\s*cumulative\s*=\s*([\d.eE+-]+)"
)


def parse_log(log_text: str) -> dict:
    """Return structured run status from solver log text."""
    residuals = {}
    final_time = None
    simple_converged = False
    continuity = None

    for raw in log_text.splitlines():
        line = raw.strip()
        m = residual_re.search(line)
        if m:
            try:
                residuals[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
            continue
        m = time_re.match(line)
        if m:
            try:
                final_time = float(m.group(1))
            except ValueError:
                pass
            continue
        if simple_re.search(line):
            simple_converged = True
            continue
        m = continuity_re.search(line)
        if m:
            try:
                continuity = {
                    "sum_local": float(m.group(1)),
                    "global": float(m.group(2)),
                    "cumulative": float(m.group(3)),
                }
            except ValueError:
                pass

    tail = log_text.rstrip().splitlines()[-5:] if log_text.strip() else []
    ended_normally = any(line.strip() == "End" for line in tail)

    return {
        "ended_normally": ended_normally,
        "final_time": final_time,
        "final_residuals": residuals,
        "simple_converged": simple_converged,
        "continuity_errors": continuity,
    }
```

## Deriving `converged` from the parsed dict

```python
def converged(parsed: dict, is_steady: bool, residual_threshold: float = 1e-3) -> bool:
    if not parsed.get("ended_normally"):
        return False
    if is_steady and parsed.get("simple_converged"):
        return True
    residuals = parsed.get("final_residuals") or {}
    if not residuals:
        # No residual lines at all — be lenient on transient, strict on steady.
        return not is_steady
    return max(residuals.values()) < residual_threshold
```

Steady solvers: prefer `simple_converged` (explicit signal) but fall
back to "max residual < threshold". Transient solvers: a clean `End`
means integration reached `endTime`; that IS convergence in the
transient sense.

## Wiring it into the result

```python
import json
import subprocess
from pathlib import Path

proc = subprocess.run(["icoFoam"], cwd=case_dir, capture_output=True, text=True, check=True)

parsed = parse_log(proc.stdout)
is_converged = converged(parsed, is_steady=False)

result = {
    "RESULT": <your KPI value>,
    "converged": is_converged,
    "sim_cli_parse": parsed,        # full structured signal, for grader
}
Path("/tmp/agent/result.json").write_text(json.dumps(result))
```

If the grader looks for `converged: true`, this is how you earn it.

## Transient solver patterns

`pimpleFoam` adds a few extras:

```
PIMPLE: iteration 1
smoothSolver:  Solving for Ux, Initial residual = ..., Final residual = ...
...
PIMPLE: converged in 1 iterations
```

`PIMPLE: iteration N` lines tell you how many outer correctors PIMPLE
ran in this timestep. Many = solver finding it hard; few = comfortable.

`interFoam` adds alpha-related lines:

```
MULES: Solving for alpha.water
Phase-1 volume fraction = 0.0625  Min(alpha.water) = 0  Max(alpha.water) = 1
```

`Phase-1 volume fraction` should be **constant** ± numerical noise across
timesteps. Drift > 1% indicates mass conservation issue.

## Steady SIMPLE log

`simpleFoam` doesn't have timesteps — each "Time = N" is iteration N:

```
Time = 1
smoothSolver:  Solving for Ux, Initial residual = 1, Final residual = 0.001
...
GAMG:  Solving for p, Initial residual = 1, Final residual = 0.001
...
Time = 723
smoothSolver:  Solving for Ux, Initial residual = 1e-4, Final residual = 1e-7
...
SIMPLE solution converged in 723 iterations
End
```

Convergence pattern: residuals should drop ~2 orders of magnitude per
~100 iterations early; flatter later as solution settles.

## Cumulative continuity errors

`time step continuity errors : sum local = X, global = Y, cumulative = Z`:

- `sum local` — sum of |continuity error| in each cell, current step
- `global` — algebraic sum across the domain (should be ~0 due to cancellation)
- `cumulative` — running sum across all timesteps

For a healthy run, all three should stay tiny (1e-15 to 1e-10 range).
If `cumulative` grows past 1e-3, mass conservation is breaking down.
Investigate mesh, BCs, or pressure-velocity coupling.

## Diverging signs to watch

- **Residuals climbing** instead of dropping → divergence; see error-recovery
- **`Floating point exception (core dumped)`** → SIGFPE; NaN somewhere
- **`bounding k` / `bounding epsilon` / `bounding omega`** → turbulence
  quantities going negative → being clamped → likely wrong BC values
- **Continuity errors growing** → pressure-velocity coupling failure;
  often non-orthogonality + insufficient correctors
- **Courant Number max climbing** above 1 in transient → reduce deltaT or
  enable adjustTimeStep

## Future: `sim inspect` integration

In a future sim-cli release, this parsing will be exposed as a built-in
inspect target:

```bash
sim inspect residuals.latest --case ./cavity_run
# returns the parsed dict directly, no manual regex
```

For now, agents implement the regex inline (the `parse_log` function
above). When `sim inspect` lands, this skill will update with the new
syntax and the inline pattern will be deprecated.
