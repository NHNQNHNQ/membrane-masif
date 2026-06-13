import argparse
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def read_ascii_ply(path: Path):
    lines = path.read_text(errors="ignore").splitlines()
    header = []
    props = []
    nv = 0
    nf = 0
    end_header = 0
    in_vertex = False
    for i, line in enumerate(lines):
        header.append(line)
        if line.startswith("element vertex"):
            nv = int(line.split()[2])
            in_vertex = True
        elif line.startswith("element face"):
            nf = int(line.split()[2])
            in_vertex = False
        elif in_vertex and line.startswith("property float"):
            props.append(line.split()[-1])
        elif line.strip() == "end_header":
            end_header = i + 1
            break
    vlines = lines[end_header : end_header + nv]
    flines = lines[end_header + nv : end_header + nv + nf]
    tail = lines[end_header + nv + nf :]
    verts = np.array([[float(x) for x in ln.split()] for ln in vlines], dtype=float)
    return header, props, verts, flines, tail


def write_ascii_ply(path: Path, header, props, verts, flines, tail):
    out = []
    for line in header:
        out.append(line)
    for row in verts:
        out.append(" ".join(f"{x:.6f}" for x in row))
    out.extend(flines)
    out.extend(tail)
    path.write_text("\n".join(out) + "\n")


def read_pdb_atoms(path: Path):
    coords = []
    elems = []
    for line in path.read_text(errors="ignore").splitlines():
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        if len(line) < 54:
            continue
        x = float(line[30:38])
        y = float(line[38:46])
        z = float(line[46:54])
        elem = line[76:78].strip().upper() if len(line) >= 78 else ""
        if not elem:
            name = line[12:16].strip()
            elem = name[0].upper() if name else "C"
        coords.append((x, y, z))
        elems.append(elem)
    return np.array(coords, dtype=float), np.array(elems)


def build_feature_maps(vertex_xyz, atom_xyz, atom_elem):
    tree = cKDTree(atom_xyz)
    k = min(8, len(atom_xyz))
    dist, idx = tree.query(vertex_xyz, k=k)
    if k == 1:
        dist = dist[:, None]
        idx = idx[:, None]
    w = 1.0 / (dist + 1e-3)
    elems = atom_elem[idx]

    hyd_map = {"C": 1.0, "S": 0.4, "P": 0.2, "N": -0.7, "O": -1.0, "H": 0.0}
    hb_map = {"N": 1.0, "O": -1.0, "S": -0.3, "P": 0.0, "C": 0.0, "H": 0.0}

    hyd_vals = np.vectorize(lambda e: hyd_map.get(e, 0.0))(elems)
    hb_vals = np.vectorize(lambda e: hb_map.get(e, 0.0))(elems)
    hyd = (hyd_vals * w).sum(axis=1) / w.sum(axis=1)
    hb = (hb_vals * w).sum(axis=1) / w.sum(axis=1)

    hyd = np.clip(hyd * 4.5, -4.5, 4.5)
    hb = hb - np.median(hb)
    hb_scale = np.percentile(np.abs(hb), 95)
    if hb_scale < 1e-6:
        hb_scale = 1.0
    hb = np.clip(hb / hb_scale, -1.0, 1.0)
    return hyd, hb


def contrast_ddc(ddc):
    q5, q50, q95 = np.percentile(ddc, [5, 50, 95])
    denom = max(q95 - q5, 1e-6)
    out = (ddc - q50) / denom * 1.4
    return np.clip(out, -0.7, 0.7)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--pdb", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    header, props, verts, flines, tail = read_ascii_ply(Path(args.ply))
    p2i = {p: i for i, p in enumerate(props)}
    for needed in ["x", "y", "z", "hphob", "hbond"]:
        if needed not in p2i:
            raise ValueError(f"missing property {needed}")

    atom_xyz, atom_elem = read_pdb_atoms(Path(args.pdb))
    xyz = verts[:, [p2i["x"], p2i["y"], p2i["z"]]]
    hyd, hb = build_feature_maps(xyz, atom_xyz, atom_elem)
    verts[:, p2i["hphob"]] = hyd
    verts[:, p2i["hbond"]] = hb

    if "ddc" in p2i:
        verts[:, p2i["ddc"]] = contrast_ddc(verts[:, p2i["ddc"]])

    write_ascii_ply(Path(args.out), header, props, verts, flines, tail)
    print("saved", args.out)
    print("hphob", float(hyd.min()), float(hyd.max()), float(hyd.mean()))
    print("hbond", float(hb.min()), float(hb.max()), float(hb.mean()))
    if "ddc" in p2i:
        ddc = verts[:, p2i["ddc"]]
        print("ddc", float(ddc.min()), float(ddc.max()), float(ddc.mean()))


if __name__ == "__main__":
    main()
