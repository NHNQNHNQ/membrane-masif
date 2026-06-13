import argparse
from pathlib import Path
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ply", required=True)
    args = parser.parse_args()

    p = Path(args.ply)
    lines = p.read_text(errors="ignore").splitlines()
    nv = 0
    st = 0
    for i, l in enumerate(lines):
        if l.startswith("element vertex"):
            nv = int(l.split()[2])
        if l.strip() == "end_header":
            st = i + 1
            break
    props = [ln.split()[-1] for ln in lines[:st] if ln.startswith("property float")]
    arr = np.array([[float(x) for x in ln.split()[: len(props)]] for ln in lines[st : st + nv]])
    ci = props.index("charge")
    ch = arr[:, ci]
    print("file", str(p))
    print("props", ",".join(props))
    print("vertices", nv)
    print("charge_unique", len(np.unique(np.round(ch, 6))))
    print("charge_min", float(ch.min()))
    print("charge_max", float(ch.max()))
    print("charge_neg", int((ch < 0).sum()))
    print("charge_pos", int((ch > 0).sum()))
    print("line1", lines[st] if nv > 0 else "")


if __name__ == "__main__":
    main()
