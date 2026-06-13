import argparse
from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


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
    arr = np.array([[float(x) for x in ln.split()[: len(props)]] for ln in lines[st : st + nv]], dtype=float)
    p2i = {p: i for i, p in enumerate(props)}
    return arr, p2i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ply", required=True)
    ap.add_argument("--out_png", required=True)
    ap.add_argument("--point_size", type=float, default=1.0)
    ap.add_argument("--elev", type=float, default=20.0)
    ap.add_argument("--azim", type=float, default=45.0)
    args = ap.parse_args()

    arr, p2i = read_ply(Path(args.ply))
    xyz = arr[:, [p2i["x"], p2i["y"], p2i["z"]]]
    if "charge" in p2i:
        c = arr[:, p2i["charge"]]
    else:
        c = np.zeros(len(xyz))

    fig = plt.figure(figsize=(8, 8), dpi=180)
    ax = fig.add_subplot(111, projection="3d")
    sc = ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], c=c, cmap="coolwarm", s=args.point_size, linewidths=0)
    ax.view_init(elev=args.elev, azim=args.azim)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    plt.colorbar(sc, ax=ax, shrink=0.6, label="charge")
    out = Path(args.out_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), bbox_inches="tight")
    plt.close(fig)
    print("saved", str(out))


if __name__ == "__main__":
    main()
