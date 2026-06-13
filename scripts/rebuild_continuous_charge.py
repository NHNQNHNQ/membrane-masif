import argparse
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def read_vertices_from_ply(ply_path: Path):
    lines = ply_path.read_text(errors="ignore").splitlines(True)
    nv = 0
    st = 0
    for i, line in enumerate(lines):
        if line.startswith("element vertex"):
            nv = int(line.split()[2])
        if line.strip() == "end_header":
            st = i + 1
            break
    rows = [ln.split() for ln in lines[st : st + nv]]
    verts = np.array([[float(r[0]), float(r[1]), float(r[2])] for r in rows], dtype=float)
    return lines, st, nv, rows, verts


def read_atoms_from_pdb(pdb_path: Path):
    atom_xyz = []
    atom_q = []
    q_elem = {
        "O": -0.55,
        "N": -0.35,
        "S": -0.15,
        "P": 1.00,
        "F": -0.20,
        "CL": -0.15,
        "BR": -0.10,
        "I": -0.05,
        "NA": 1.00,
        "K": 1.00,
        "MG": 2.00,
        "CA": 2.00,
        "C": 0.15,
        "H": 0.05,
    }
    for ln in pdb_path.read_text(errors="ignore").splitlines():
        if not (ln.startswith("ATOM") or ln.startswith("HETATM")):
            continue
        try:
            x = float(ln[30:38])
            y = float(ln[38:46])
            z = float(ln[46:54])
        except Exception:
            continue
        elem = ln[76:78].strip().upper()
        if not elem:
            an = ln[12:16].strip().upper()
            elem = "".join([c for c in an if c.isalpha()])[:2]
            elem = "CL" if elem.startswith("CL") else ("BR" if elem.startswith("BR") else elem[:1])
        q = q_elem.get(elem, 0.0)
        atom_xyz.append([x, y, z])
        atom_q.append(q)
    return np.asarray(atom_xyz, dtype=float), np.asarray(atom_q, dtype=float)


def build_continuous_charge(verts, atom_xyz, atom_q, sigma=1.0, k_neighbors=12):
    tree = cKDTree(atom_xyz)
    k = min(k_neighbors, len(atom_xyz))
    d, idx = tree.query(verts, k=k)
    if k == 1:
        d = d[:, None]
        idx = idx[:, None]
    d = np.maximum(d, 1e-3)
    w = np.exp(-(d ** 2) / (2 * sigma ** 2)) / d
    w = w / np.sum(w, axis=1, keepdims=True)
    return np.sum(atom_q[idx] * w, axis=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ply", required=True)
    parser.add_argument("--pdb", required=True)
    parser.add_argument("--backup", default="")
    args = parser.parse_args()

    ply = Path(args.ply)
    pdb = Path(args.pdb)
    backup = Path(args.backup) if args.backup else ply.with_suffix(".ply.bak_before_continuous_charge")
    if not backup.exists():
        backup.write_text(ply.read_text())

    lines, st, nv, rows, verts = read_vertices_from_ply(ply)
    atom_xyz, atom_q = read_atoms_from_pdb(pdb)
    charge = build_continuous_charge(verts, atom_xyz, atom_q)

    out = lines[:st]
    for i, r in enumerate(rows):
        r[4] = f"{float(charge[i]):.6f}"
        out.append(" ".join(r) + "\n")
    out.extend(lines[st + nv :])
    ply.write_text("".join(out))

    u = np.unique(np.round(charge, 6))
    print(
        "unique",
        len(u),
        "min",
        float(charge.min()),
        "max",
        float(charge.max()),
        "neg",
        int((charge < 0).sum()),
        "pos",
        int((charge > 0).sum()),
        "backup",
        str(backup),
    )


if __name__ == "__main__":
    main()
