# sim-plugin-openfoam

OpenFOAM driver for [sim-cli](https://github.com/svd-ai-lab/sim-cli),
distributed as a plugin via Python `entry_points`.

## Install

For agent projects, install sim-cli-core and the OpenFOAM plugin in the project
environment:

```powershell
uv init  # only if this is not already a uv project
uv add sim-cli-core sim-plugin-openfoam
uv run sim plugin sync-skills --target .agents/skills --copy
uv run sim check openfoam
uv run sim plugin doctor openfoam --deep
```

For Claude Code, sync the bundled skill to `.claude/skills` instead:

```powershell
uv run sim plugin sync-skills --target .claude/skills --copy
```

For a reproducible agent run, pin the PyPI package version:

```powershell
uv add sim-cli-core "sim-plugin-openfoam==0.1.0"
```

`uv run sim ...` runs sim from this project environment, so it sees this
project's plugins. Without uv, create and activate a venv, then install
`sim-cli-core` plus this plugin from PyPI with `python -m pip`.

## Development

```bash
git clone https://github.com/svd-ai-lab/sim-plugin-openfoam
cd sim-plugin-openfoam
uv sync
uv run pytest
```

## License

Apache-2.0.
