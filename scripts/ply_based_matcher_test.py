import argparse
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


def read_ply(path: Path):
    lines = path.read_text(errors="ignore").splitlines()
    nv = 0
    st = 0
    props = []
    for i, l in enumerate(lines):
        if l.startswith("element vertex"):
            nv = int(l.split()[2])
        elif l.startswith("property float"):
            props.append(l.split()[-1])
        elif l.strip() == "end_header":
            st = i + 1
            break
    rows = [ln.split() for ln in lines[st : st + nv]]
    arr = np.array([[float(x) for x in r[: len(props)]] for r in rows], dtype=float)
    p2i = {p: i for i, p in enumerate(props)}
    return arr, p2i


def safe_corr(a, b, inverse=False):
    if len(a) < 3 or len(b) < 3:
        return 0.0
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 0.0
    c = float(np.corrcoef(a, b)[0, 1])
    if np.isnan(c):
        return 0.0
    return max(0.0, -c if inverse else c)


def score_pair(mem_arr, mem_map, pep_arr, pep_map):
    mem_xyz = mem_arr[:, [mem_map["x"], mem_map["y"], mem_map["z"]]]
    pep_xyz = pep_arr[:, [pep_map["x"], pep_map["y"], pep_map["z"]]]
    tree = cKDTree(mem_xyz)
    d, idx = tree.query(pep_xyz, k=1)
    spatial = float(np.exp(-np.mean(d)))
    charge = 0.0
    if "charge" in mem_map and "charge" in pep_map:
        mc = mem_arr[idx, mem_map["charge"]]
        pc = pep_arr[:, pep_map["charge"]]
        charge = safe_corr(mc, pc, inverse=True)
    hbond = 0.0
    if "hbond" in mem_map and "hbond" in pep_map:
        mh = mem_arr[idx, mem_map["hbond"]]
        ph = pep_arr[:, pep_map["hbond"]]
        hbond = safe_corr(mh, ph, inverse=False)
    return 0.5 * charge + 0.3 * spatial + 0.2 * hbond, spatial, charge, hbond


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--membrane_ply", required=True)
    ap.add_argument("--peptide_dir", required=True)
    ap.add_argument("--output_csv", required=True)
    ap.add_argument("--glob", default="*.ply")
    ap.add_argument("--top_n", type=int, default=50)
    args = ap.parse_args()

    mem_path = Path(args.membrane_ply)
    pep_dir = Path(args.peptide_dir)
    out_csv = Path(args.output_csv)

    mem_arr, mem_map = read_ply(mem_path)
    peps = sorted(pep_dir.glob(args.glob))
    peps = [p for p in peps if p.resolve() != mem_path.resolve()]
    results = []
    for p in peps:
        try:
            pep_arr, pep_map = read_ply(p)
            total, spatial, charge, hbond = score_pair(mem_arr, mem_map, pep_arr, pep_map)
            results.append((p.name, total, spatial, charge, hbond, len(pep_arr)))
        except Exception as e:
            results.append((p.name, -1.0, 0.0, 0.0, 0.0, 0))
            print("skip", p, str(e))

    results.sort(key=lambda x: x[1], reverse=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8") as f:
        f.write("peptide,total_score,spatial_score,charge_score,hbond_score,vertex_count\n")
        for row in results:
            f.write(",".join([str(x) for x in row]) + "\n")

    print("matched", len(results), "peptides")
    print("output", str(out_csv))
    print("top")
    for i, row in enumerate(results[: args.top_n], 1):
        print(i, row[0], "total", f"{row[1]:.6f}", "charge", f"{row[3]:.6f}", "spatial", f"{row[2]:.6f}")


if __name__ == "__main__":
    main()
