import argparse
import importlib
import json
import os
import shutil
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    mods = [
        "pymesh",
        "numpy",
        "scipy",
        "sklearn",
        "networkx",
        "Bio",
        "tensorflow",
        "rdkit",
        "openbabel",
        "IPython",
    ]
    bins = ["msms", "pdb2pqr", "apbs", "multivalue", "mamba"]
    out = {
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "modules": {},
        "binaries": {},
        "env_vars": {
            "MSMS_BIN": os.environ.get("MSMS_BIN"),
            "PDB2PQR_BIN": os.environ.get("PDB2PQR_BIN"),
            "APBS_BIN": os.environ.get("APBS_BIN"),
            "MULTIVALUE_BIN": os.environ.get("MULTIVALUE_BIN"),
        },
    }
    for m in mods:
        try:
            mod = importlib.import_module(m)
            out["modules"][m] = {"ok": True, "version": getattr(mod, "__version__", None)}
        except Exception as e:
            out["modules"][m] = {"ok": False, "err": str(e)}
    for b in bins:
        out["binaries"][b] = shutil.which(b)

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    print("python", out["python"], out["python_version"])
    for m in mods:
        item = out["modules"][m]
        if item["ok"]:
            print("module", m, "ok", item["version"])
        else:
            print("module", m, "missing", item["err"])
    for b in bins:
        print("bin", b, out["binaries"][b])


if __name__ == "__main__":
    main()
