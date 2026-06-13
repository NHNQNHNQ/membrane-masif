"""Verify the membrane-masif analysis env.

Run inside the activated env:
    python scripts/verify_env.py
"""

import importlib
import shutil
import subprocess
import sys


CHECKS = [
    # core
    ("numpy", None),
    ("scipy", None),
    ("pandas", None),
    ("sklearn", None),
    ("networkx", None),
    ("matplotlib", None),
    ("seaborn", None),
    # cheminformatics
    ("rdkit", None),
    ("openbabel", None),
    ("Bio", None),  # biopython
    # MD analysis
    ("MDAnalysis", None),
    ("mdtraj", None),
    ("lipyphilic", None),
    # mesh / PLY
    ("trimesh", None),
    ("plyfile", None),
    ("meshio", None),
    # viz
    ("pymol", None),
    ("nglview", None),
    # deep learning
    ("torch", None),
    ("torch_geometric", None),
    ("torch_geometric.nn", "GINEConv"),
    ("torch_geometric.data", "Data"),
]


def check_import(mod, attr):
    try:
        m = importlib.import_module(mod)
        if attr is not None:
            getattr(m, attr)
        ver = getattr(m, "__version__", "?")
        return True, ver
    except Exception as e:
        return False, str(e)


def check_cmd(name):
    path = shutil.which(name)
    if path is None:
        return False, "not on PATH"
    try:
        r = subprocess.run(
            [path, "--version"], capture_output=True, text=True, timeout=10
        )
        first = (r.stdout or r.stderr).splitlines()[0] if (r.stdout or r.stderr) else ""
        return True, f"{path} ({first.strip()})"
    except Exception as e:
        return True, f"{path} (no --version, {e})"


def main():
    print(f"Python: {sys.version.split()[0]} @ {sys.executable}\n")
    fail = 0
    print("== Python imports ==")
    for mod, attr in CHECKS:
        ok, info = check_import(mod, attr)
        tag = "OK " if ok else "ERR"
        sub = f".{attr}" if attr else ""
        print(f"  [{tag}] {mod}{sub:20s}  {info}")
        if not ok:
            fail += 1

    print("\n== External binaries ==")
    for cmd in ["gmx", "pymol"]:
        ok, info = check_cmd(cmd)
        tag = "OK " if ok else "ERR"
        print(f"  [{tag}] {cmd:8s}  {info}")
        if not ok and cmd == "gmx":
            fail += 1

    print()
    if fail:
        print(f"FAILED: {fail} checks did not pass.")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
