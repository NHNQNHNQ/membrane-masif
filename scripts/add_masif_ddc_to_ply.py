import argparse
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def read_ascii_ply(path: Path):
    lines = path.read_text(errors="ignore").splitlines()
    header = []
    vertex_props = []
    vertex_count = 0
    face_count = 0
    end_header = 0
    in_vertex = False
    for i, line in enumerate(lines):
        header.append(line)
        if line.startswith("element vertex"):
            vertex_count = int(line.split()[2])
            in_vertex = True
        elif line.startswith("element face"):
            face_count = int(line.split()[2])
            in_vertex = False
        elif in_vertex and line.startswith("property float"):
            vertex_props.append(line.split()[-1])
        elif line.strip() == "end_header":
            end_header = i + 1
            break
    vertex_lines = lines[end_header : end_header + vertex_count]
    face_lines = lines[end_header + vertex_count : end_header + vertex_count + face_count]
    tail_lines = lines[end_header + vertex_count + face_count :]
    vertex_data = np.array([[float(x) for x in line.split()] for line in vertex_lines], dtype=float)
    return header, vertex_props, vertex_data, face_lines, tail_lines


def mean_normal_center_patch(distances, normals, radius):
    mask = distances <= radius
    if not np.any(mask):
        mask = np.ones(len(distances), dtype=bool)
    mean_normal = normals[mask].mean(axis=0)
    norm = np.linalg.norm(mean_normal)
    if norm == 0:
        return np.array([0.0, 0.0, 1.0], dtype=float)
    return mean_normal / norm


def compute_center_ddc(verts, normals, center_idx, patch_idx):
    patch_v = verts[patch_idx]
    patch_n = normals[patch_idx]
    center = verts[center_idx]
    distances = np.linalg.norm(patch_v - center, axis=1)
    ni = mean_normal_center_patch(distances, patch_n, 2.5)
    sf = patch_v + patch_n
    sf = sf - (ni + center)
    sf = np.linalg.norm(sf, axis=1) - distances
    sf = np.sign(sf)
    distances = distances.copy()
    distances[distances == 0] = 1e-8
    kij = np.linalg.norm(patch_n - ni, axis=1) / distances
    kij = sf * kij
    kij[kij > 0.7] = 0
    kij[kij < -0.7] = 0
    valid = distances > 1e-6
    if not np.any(valid):
        return 0.0
    return float(np.mean(kij[valid]))


def compute_vertex_ddc(verts, normals, radius, min_neighbors):
    tree = cKDTree(verts)
    ddc = np.zeros(len(verts), dtype=float)
    for i in range(len(verts)):
        patch_idx = tree.query_ball_point(verts[i], radius)
        if len(patch_idx) < min_neighbors:
            ddc[i] = 0.0
            continue
        ddc[i] = compute_center_ddc(verts, normals, i, patch_idx)
    return ddc


def write_ascii_ply(path: Path, header, vertex_props, vertex_data, face_lines, tail_lines):
    out = []
    for line in header:
        if line.startswith("element face") and "ddc" not in vertex_props:
            out.append("property float ddc")
            out.append(line)
        else:
            out.append(line)
    for row in vertex_data:
        out.append(" ".join(f"{x:.6f}" for x in row))
    out.extend(face_lines)
    out.extend(tail_lines)
    path.write_text("\n".join(out) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ply", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--radius", type=float, default=12.0)
    parser.add_argument("--min_neighbors", type=int, default=12)
    args = parser.parse_args()

    in_path = Path(args.ply)
    out_path = Path(args.out)
    header, props, vertex_data, face_lines, tail_lines = read_ascii_ply(in_path)
    prop_to_idx = {name: idx for idx, name in enumerate(props)}
    required = ["x", "y", "z", "nx", "ny", "nz"]
    missing = [name for name in required if name not in prop_to_idx]
    if missing:
        raise ValueError("missing properties: " + ",".join(missing))
    verts = vertex_data[:, [prop_to_idx["x"], prop_to_idx["y"], prop_to_idx["z"]]]
    normals = vertex_data[:, [prop_to_idx["nx"], prop_to_idx["ny"], prop_to_idx["nz"]]]
    ddc = compute_vertex_ddc(verts, normals, args.radius, args.min_neighbors)
    if "ddc" in prop_to_idx:
        vertex_data[:, prop_to_idx["ddc"]] = ddc
    else:
        vertex_data = np.column_stack([vertex_data, ddc])
    write_ascii_ply(out_path, header, props, vertex_data, face_lines, tail_lines)
    print(f"saved {out_path}")
    print(f"ddc_min {ddc.min():.6f} ddc_max {ddc.max():.6f} ddc_mean {ddc.mean():.6f}")


if __name__ == "__main__":
    main()
