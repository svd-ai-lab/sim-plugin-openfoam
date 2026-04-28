# Prompt for Linux Claude Code

Copy the text below the line and paste it as the first message to Claude Code on your Linux machine.

---

## Context

I'm building **sim** — a unified CLI for LLM agents to control CAD/CAE simulation software. We have working drivers for Fluent, COMSOL, ANSA, Flotherm on a Windows machine. Now we need to add **OpenFOAM** support.

OpenFOAM runs on this Linux machine. The Windows machine will control it remotely via an HTTP server called **sim-server**.

## Your Tasks (in order)

### Task 1: Environment Report

First, report the following information (just run the commands and tell me the results):

```bash
# OpenFOAM
which simpleFoam && simpleFoam -help 2>&1 | head -3
echo $WM_PROJECT_VERSION
echo $FOAM_TUTORIALS
ls $FOAM_TUTORIALS/incompressible/simpleFoam/ 2>/dev/null | head -10

# Python
python3 --version
pip3 --version

# Network
hostname
ip addr show | grep "inet " | grep -v 127.0.0.1
# If Tailscale is installed:
tailscale ip -4 2>/dev/null

# System
uname -a
free -h | head -2
nproc
```

### Task 2: Install sim-server

```bash
# Clone and install
git clone https://github.com/svd-ai-lab/sim-server.git
cd sim-server
pip3 install -e ".[dev]"
```

### Task 3: Extend sim-server for OpenFOAM

The current `sim-server` only supports Fluent. We need to add OpenFOAM support. The key changes to `src/sim_server/server.py`:

**The `/connect` endpoint** needs to support `solver="openfoam"`:
- When `solver="openfoam"`, do NOT launch a Python session object
- Instead, store the OpenFOAM environment info (version, project dir, available tutorials)
- Create a working directory for the session (e.g., `/tmp/sim_openfoam_<session_id>/`)

**The `/exec` endpoint** needs two execution modes for OpenFOAM:
- If the code starts with `#!openfoam` (shebang-style), treat it as a shell command sequence and run via `subprocess.run(code, shell=True)`, capturing stdout/stderr
- Otherwise, treat it as Python code that can use `subprocess` to call OpenFOAM commands

**Add a new `/upload` endpoint**:
- POST `/upload` with `{filename: str, content: str}` — writes a file to the session working directory
- This lets the Windows client send case files (blockMeshDict, controlDict, etc.)

**Add a new `/download` endpoint**:
- GET `/download/<path>` — reads a file from the session working directory and returns its content
- This lets the Windows client retrieve results (postProcessing output, logs, etc.)

### Task 4: Test with cavity tutorial

After implementing, test the full flow:

```bash
# Start the server (bind to all interfaces so Windows can reach it)
sim-server --host 0.0.0.0 --port 7600
```

Then in another terminal, test locally:

```bash
# Connect
curl -X POST http://localhost:7600/connect -H "Content-Type: application/json" -d '{"solver": "openfoam"}'

# Copy cavity tutorial to session working dir
curl -X POST http://localhost:7600/exec -H "Content-Type: application/json" -d '{
  "code": "#!openfoam\ncp -r $FOAM_TUTORIALS/incompressible/icoFoam/cavity/cavity/* .\nls -la",
  "label": "setup_cavity"
}'

# Run blockMesh
curl -X POST http://localhost:7600/exec -H "Content-Type: application/json" -d '{
  "code": "#!openfoam\nblockMesh 2>&1",
  "label": "blockMesh"
}'

# Run icoFoam
curl -X POST http://localhost:7600/exec -H "Content-Type: application/json" -d '{
  "code": "#!openfoam\nicoFoam 2>&1",
  "label": "icoFoam"
}'

# Check results
curl -X POST http://localhost:7600/exec -H "Content-Type: application/json" -d '{
  "code": "#!openfoam\nls -la 0.5/ 2>/dev/null && echo SUCCESS || echo NO_RESULTS",
  "label": "check_results"
}'

# Disconnect
curl -X POST http://localhost:7600/disconnect
```

### Task 5: Report back

After all tests pass, tell me:
1. The IP address I should use to connect from Windows (Tailscale IP preferred, else LAN IP)
2. The port (default 7600)
3. OpenFOAM version
4. Which tutorials are available
5. Any issues encountered

## Important Notes

- The server must bind to `0.0.0.0` (not `127.0.0.1`) so Windows can reach it
- OpenFOAM shell commands need the OpenFOAM environment sourced — make sure `$FOAM_TUTORIALS`, `$WM_PROJECT_DIR` etc. are available in the subprocess environment
- Keep the existing Fluent support working — OpenFOAM is an additional solver, not a replacement
- Use the existing code patterns in `server.py` — don't redesign, just extend
- Python 3.10+ is required for sim-server
