import argparse
from pathlib import Path
from collections import deque


def parse_ply(path: Path):
    lines = path.read_text(errors="ignore").splitlines()
    nv = 0
    nf = 0
    st = 0
    props = []
    for i, l in enumerate(lines):
        if l.startswith("element vertex"):
            nv = int(l.split()[2])
        elif l.startswith("element face"):
            nf = int(l.split()[2])
        elif l.startswith("property float"):
            props.append(l.split()[-1])
        elif l.strip() == "end_header":
            st = i + 1
            break
    vertices = [ln.split() for ln in lines[st : st + nv]]
    faces = [ln for ln in lines[st + nv : st + nv + nf]]
    tail = lines[st + nv + nf :]
    return lines, st, nv, nf, props, vertices, faces, tail


def face_idx(face_line: str):
    s = face_line.split()
    if not s or s[0] != "3":
        return None
    return int(s[1]), int(s[2]), int(s[3])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--min_vertices", type=int, default=40)
    ap.add_argument("--keep_ratio", type=float, default=0.01)
    ap.add_argument("--keep_largest_only", action="store_true")
    args = ap.parse_args()

    p = Path(args.ply)
    lines, st, nv, nf, props, vertices, faces, tail = parse_ply(p)
    g = [set() for _ in range(nv)]
    face_tris = []
    for f in faces:
        idx = face_idx(f)
        if idx is None:
            continue
        a, b, c = idx
        face_tris.append((a, b, c))
        g[a].update((b, c))
        g[b].update((a, c))
        g[c].update((a, b))

    seen = [False] * nv
    comps = []
    for i in range(nv):
        if seen[i]:
            continue
        q = deque([i])
        seen[i] = True
        comp = []
        while q:
            u = q.popleft()
            comp.append(u)
            for v in g[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
        comps.append(comp)
    if not comps:
        print("no components")
        return
    comps.sort(key=len, reverse=True)
    largest = len(comps[0])
    keep = set(comps[0]) if args.keep_largest_only else set()
    if not args.keep_largest_only:
        for c in comps:
            if len(c) >= args.min_vertices and len(c) >= int(largest * args.keep_ratio):
                keep.update(c)

    mapping = {}
    new_vertices = []
    for old in sorted(keep):
        mapping[old] = len(new_vertices)
        new_vertices.append(vertices[old])

    new_faces = []
    for a, b, c in face_tris:
        if a in keep and b in keep and c in keep:
            new_faces.append(f"3 {mapping[a]} {mapping[b]} {mapping[c]}")

    out = []
    out.extend(lines[:st])
    for i, l in enumerate(out):
        if l.startswith("element vertex"):
            out[i] = f"element vertex {len(new_vertices)}"
        if l.startswith("element face"):
            out[i] = f"element face {len(new_faces)}"
    out.extend([" ".join(v) for v in new_vertices])
    out.extend(new_faces)
    out.extend(tail)

    bak = p.with_suffix(p.suffix + ".bak_before_remove_islands")
    if not bak.exists():
        bak.write_text("\n".join(lines) + "\n")
    p.write_text("\n".join(out) + "\n")
    print("components", len(comps), "largest", largest, "kept_vertices", len(new_vertices), "kept_faces", len(new_faces))


if __name__ == "__main__":
    main()
