"""OpenFOAM driver plugin for sim-cli.

Distributed as a plugin; discovered by sim-cli via the
``sim.drivers`` entry-point group. Bundled skill files (under
``_skills/``) are exposed via the ``sim.skills`` entry-point group, and
lightweight metadata via ``sim.plugins``.
"""
from importlib.resources import files

from .driver import OpenFOAMDriver

skills_dir = files(__name__) / "_skills"

plugin_info = {
    "name": "openfoam",
    "summary": "OpenFOAM driver for sim.",
    "homepage": "https://github.com/svd-ai-lab/sim-plugin-openfoam",
    "license_class": "oss",
    "solver_name": "OpenFOAM",
}

__all__ = ["OpenFOAMDriver", "skills_dir", "plugin_info"]
