import argparse
import math
from pathlib import Path

import numpy as np


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
    faces = []
    for line in face_lines:
        fields = line.split()
        if fields and fields[0] == "3":
            faces.append([int(fields[1]), int(fields[2]), int(fields[3])])
    return header, vertex_props, vertex_data, np.array(faces, dtype=int), face_lines, tail_lines


def cotangent(u, v):
    cross = np.linalg.norm(np.cross(u, v))
    if cross < 1e-12:
        return 0.0
    return float(np.dot(u, v) / cross)


def compute_shape_index(vertices, normals, faces):
    n = len(vertices)
    area = np.zeros(n, dtype=float)
    angle_sum = np.zeros(n, dtype=float)
    laplace = np.zeros((n, 3), dtype=float)

    for i, j, k in faces:
        vi = vertices[i]
        vj = vertices[j]
        vk = vertices[k]

        eij = vj - vi
        eik = vk - vi
        eji = vi - vj
        ejk = vk - vj
        eki = vi - vk
        ekj = vj - vk

        face_normal = np.cross(eij, eik)
        double_area = np.linalg.norm(face_normal)
        if double_area < 1e-12:
            continue
        tri_area = 0.5 * double_area
        share_area = tri_area / 3.0
        area[i] += share_area
        area[j] += share_area
        area[k] += share_area

        angle_i = math.acos(np.clip(np.dot(eij, eik) / (np.linalg.norm(eij) * np.linalg.norm(eik)), -1.0, 1.0))
        angle_j = math.acos(np.clip(np.dot(eji, ejk) / (np.linalg.norm(eji) * np.linalg.norm(ejk)), -1.0, 1.0))
        angle_k = math.acos(np.clip(np.dot(eki, ekj) / (np.linalg.norm(eki) * np.linalg.norm(ekj)), -1.0, 1.0))
        angle_sum[i] += angle_i
        angle_sum[j] += angle_j
        angle_sum[k] += angle_k

        cot_i = cotangent(eij, eik)
        cot_j = cotangent(ejk, eji)
        cot_k = cotangent(eki, ekj)

        laplace[i] += cot_k * (vj - vi) + cot_j * (vk - vi)
        laplace[j] += cot_i * (vk - vj) + cot_k * (vi - vj)
        laplace[k] += cot_j * (vi - vk) + cot_i * (vj - vk)

    safe_area = np.where(area > 1e-12, area, 1e-12)
    hvec = laplace / (2.0 * safe_area[:, None])
    signed_h = 0.5 * np.linalg.norm(hvec, axis=1)
    sign = np.sign(np.einsum("ij,ij->i", hvec, normals))
    sign[sign == 0] = 1.0
    signed_h *= sign

    gaussian = (2.0 * np.pi - angle_sum) / safe_area
    elem = signed_h * signed_h - gaussian
    elem[elem < 1e-8] = 1e-8
    root = np.sqrt(elem)
    k1 = signed_h + root
    k2 = signed_h - root
    denom = k1 - k2
    denom[np.abs(denom) < 1e-12] = 1e-12
    si = np.arctan((k1 + k2) / denom) * (2.0 / np.pi)
    si = np.clip(si, -1.0, 1.0)
    return si


def write_ascii_ply(path: Path, header, vertex_props, vertex_data, face_lines, tail_lines):
    out = []
    for line in header:
        if line.startswith("element face") and "si" not in vertex_props:
            out.append("property float si")
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
    args = parser.parse_args()

    in_path = Path(args.ply)
    out_path = Path(args.out)
    header, props, vertex_data, faces, face_lines, tail_lines = read_ascii_ply(in_path)
    prop_to_idx = {name: idx for idx, name in enumerate(props)}
    required = ["x", "y", "z", "nx", "ny", "nz"]
    missing = [name for name in required if name not in prop_to_idx]
    if missing:
        raise ValueError("missing properties: " + ",".join(missing))
    vertices = vertex_data[:, [prop_to_idx["x"], prop_to_idx["y"], prop_to_idx["z"]]]
    normals = vertex_data[:, [prop_to_idx["nx"], prop_to_idx["ny"], prop_to_idx["nz"]]]
    si = compute_shape_index(vertices, normals, faces)
    if "si" in prop_to_idx:
        vertex_data[:, prop_to_idx["si"]] = si
    else:
        vertex_data = np.column_stack([vertex_data, si])
    write_ascii_ply(out_path, header, props, vertex_data, face_lines, tail_lines)
    print(f"saved {out_path}")
    print(f"si_min {si.min():.6f} si_max {si.max():.6f} si_mean {si.mean():.6f}")


if __name__ == "__main__":
    main()
