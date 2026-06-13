import sys
from pathlib import Path


def clean_atom_name(name):
    x = name.strip()
    if x == "Nb2" or x == "Na2":
        return "N"
    if x == "Pa" or x == "Pb":
        return "P"
    return x


def assign_unique_residue_ids(lines):
    resid = 0
    prev_block_key = None
    out = []
    for ln in lines:
        if not (ln.startswith("ATOM") or ln.startswith("HETATM")) or len(ln) < 27:
            out.append(ln)
            continue
        block_key = (ln[17:20], ln[21:22], ln[22:26])
        if block_key != prev_block_key:
            resid += 1
            prev_block_key = block_key
        out.append(ln[:22] + f"{resid:4d}" + ln[26:])
    return out


def main():
    if len(sys.argv) != 3:
        print("usage: python pdb_cleaner.py <input.pdb> <output.pdb>")
        sys.exit(1)
    inp = Path(sys.argv[1])
    outp = Path(sys.argv[2])
    lines = inp.read_text(errors="ignore").splitlines(True)
    out = []
    for ln in lines:
        if (ln.startswith("ATOM") or ln.startswith("HETATM")) and len(ln) >= 78:
            atom_name = clean_atom_name(ln[12:16])
            elem = ln[76:78].strip()
            if atom_name in ("N", "P"):
                elem = atom_name
            nln = ln
            nln = nln[:12] + f"{atom_name:>4}" + nln[16:]
            nln = nln[:17] + "LIG " + nln[21:]
            nln = nln[:21] + "A" + nln[22:]
            nln = nln[:76] + f"{elem:>2}" + nln[78:]
            out.append(nln)
        elif (ln.startswith("ATOM") or ln.startswith("HETATM")) and len(ln) >= 27:
            atom_name = clean_atom_name(ln[12:16])
            nln = ln[:12] + f"{atom_name:>4}" + ln[16:]
            nln = nln[:17] + "LIG " + nln[21:]
            nln = nln[:21] + "A" + nln[22:]
            out.append(nln)
        else:
            out.append(ln)
    out = assign_unique_residue_ids(out)
    outp.write_text("".join(out))
    print(str(outp))


if __name__ == "__main__":
    main()
