"""P0.1 acceptance — the package and every module import cleanly."""

import importlib
import pathlib
import pkgutil

import tatkal_sim


def test_package_imports_and_has_version():
    assert tatkal_sim.__version__ == "0.0.1"


def test_every_module_imports():
    pkg_dir = pathlib.Path(tatkal_sim.__file__).parent
    for mod in pkgutil.walk_packages([str(pkg_dir)], prefix="tatkal_sim."):
        importlib.import_module(mod.name)
