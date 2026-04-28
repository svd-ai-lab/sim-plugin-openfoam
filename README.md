# sim-plugin-openfoam

OpenFOAM driver for [sim-cli](https://github.com/svd-ai-lab/sim-cli),
distributed as an out-of-tree plugin.

OpenFOAM driver for sim.

## Install

```bash
sim plugin install openfoam
```

Other paths:

```bash
pip install git+https://github.com/svd-ai-lab/sim-plugin-openfoam@v0.1.0
pip install https://github.com/svd-ai-lab/sim-plugin-openfoam/releases/download/v0.1.0/sim_plugin_openfoam-0.1.0-py3-none-any.whl
pip install -e .
```

After install:

```bash
sim plugin doctor openfoam
sim plugin sync-skills
```

## Development

```bash
git clone https://github.com/svd-ai-lab/sim-plugin-openfoam
cd sim-plugin-openfoam
uv sync
uv run pytest
```

## License

Apache-2.0.
