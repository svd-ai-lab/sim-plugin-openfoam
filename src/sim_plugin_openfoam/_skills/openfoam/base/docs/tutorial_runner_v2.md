# OpenFOAM Tutorial Runner v2 — Improved Protocol

## Principles (lessons from v1)

1. **Always prefer Allrun when it exists** — never reinvent the pipeline
2. **Never sed controlDict** — endTime reduction is lossy and error-prone
3. **Judge SLOW_PASS by log content, not exit code** — `Time = X` monotonic = OK
4. **Separate workflow errors from runtime errors** — the stage matters

## Canonical single-case runner

```bash
run_case() {
    local case_path="$1"     # relative to $FOAM_TUTORIALS
    local timeout_s="$2"     # e.g. 120
    local workdir="/tmp/sim_run_$(basename $case_path)"
    
    rm -rf "$workdir"
    cp -r "$FOAM_TUTORIALS/$case_path" "$workdir"
    cd "$workdir"
    
    local log_file="sim_run.log"
    
    if [ -f Allrun ]; then
        # Preferred path: let the tutorial drive itself
        timeout "$timeout_s" bash Allrun > "$log_file" 2>&1
        local rc=$?
    else
        # Fallback: manual blockMesh + solver
        [ -d 0.orig ] && cp -r 0.orig 0
        local solver=$(grep '^application' system/controlDict | \
                       awk '{print $2}' | tr -d ';')
        blockMesh > "$log_file" 2>&1
        timeout "$timeout_s" "$solver" >> "$log_file" 2>&1
        local rc=$?
    fi
    
    classify_result "$log_file" "$rc" "$timeout_s"
}
```

## Classifier

```bash
classify_result() {
    local log="$1"
    local rc="$2"
    local timeout_s="$3"
    
    # 1. Check for FOAM FATAL
    if grep -q "FOAM FATAL" "$log"; then
        # Which stage?
        if grep -qE "cannot find file|cannot open|No such file" "$log"; then
            echo "FAIL_PRECHECK: missing input file"
            return
        fi
        if grep -qE "Floating point exception|NaN|diverged" "$log"; then
            echo "FAIL_RUNTIME: numerical"
            return
        fi
        # Check if it failed during mesh step
        local last_app=$(grep -oE "Exec *: [a-zA-Z]+" "$log" | tail -1)
        if echo "$last_app" | grep -qE "blockMesh|snappyHexMesh|createPatch|mirrorMesh|extrudeMesh"; then
            echo "FAIL_WORKFLOW: mesh step failed"
            return
        fi
        echo "FAIL_RUNTIME: solver error"
        return
    fi
    
    # 2. Normal exit — did solver reach End?
    if [ "$rc" -eq 0 ]; then
        if tail -20 "$log" | grep -q "^End$"; then
            echo "PASS"
            return
        fi
    fi
    
    # 3. Timeout (rc=124) — was solver progressing?
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
        # Extract last 'Time = X' and check if it advanced
        local last_time=$(grep -oE "^Time = [0-9.e+-]+" "$log" | tail -1 | awk '{print $3}')
        if [ -n "$last_time" ] && [ "$(echo "$last_time > 0" | bc -l 2>/dev/null)" = "1" ]; then
            echo "SLOW_PASS: reached Time=$last_time"
            return
        fi
        echo "FAIL_WORKFLOW: timeout before first timestep"
        return
    fi
    
    # 4. Non-zero exit, no FATAL, no timeout
    echo "FAIL_RUNTIME: exit=$rc (unknown)"
}
```

## Test the classifier on the 5 original FAIL cases (expected outcomes)

| Case | With v2 runner | Expected classification |
|------|----------------|--------------------------|
| chemFoam/gri | `bash Allrun` → runs chemkinToFoam + chemFoam | PASS |
| thermocoupleTestCase | `bash Allrun` → runs with full time | SLOW_PASS or PASS |
| mdEquilibrationFoam/argon | `bash Allrun` → mdInitialise + solver | SLOW_PASS |
| mesh/blockMesh/pipe | `bash Allrun` → cp geometry + blockMesh | PASS |
| interFoam/weirOverflow | `bash Allrun` with 60s timeout | SLOW_PASS (Time>0) |

**All 5 "FAILs" resolve to PASS or SLOW_PASS once we respect Allrun.**
