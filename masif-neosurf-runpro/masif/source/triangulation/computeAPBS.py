import os
import numpy
from IPython.core.debugger import set_trace
from subprocess import Popen, PIPE
from scipy.spatial import cKDTree

from default_config.global_vars import apbs_bin, pdb2pqr_bin, multivalue_bin
import random

"""
computeAPBS.py: Wrapper function to compute the Poisson Boltzmann electrostatics for a surface using APBS.
Pablo Gainza - LPDI STI EPFL 2019
This file is part of MaSIF.
Released under an Apache License 2.0
"""

def computeAPBS(vertices, pdb_file, tmp_file_base, mol2_file=None):
    """
        Calls APBS, pdb2pqr, and multivalue and returns the charges per vertex
    """
    fields = tmp_file_base.split("/")[0:-1]
    directory = "/".join(fields) + "/"
    filename_base = tmp_file_base.split("/")[-1]
    pdbname = pdb_file.split("/")[-1]
    args = [
        pdb2pqr_bin, pdbname, filename_base,
        "--ff=PARSE",
        "--whitespace",
        "--noopt",
        "--apbs-input={}.in".format(filename_base),
    ]
    if mol2_file is not None:
        args.append("--ligand=" + mol2_file)
    p2 = Popen(args, stdout=PIPE, stderr=PIPE, cwd=directory)
    stdout, stderr = p2.communicate()

    print("### PDB2PQR ###\n", stderr.decode('utf-8'))
    # from pdb import set_trace; set_trace()

    args = [apbs_bin, filename_base + ".in"]
    p2 = Popen(args, stdout=PIPE, stderr=PIPE, cwd=directory)
    stdout, stderr = p2.communicate()
    vertfile = open(directory + "/" + filename_base + ".csv", "w")
    for vert in vertices:
        vertfile.write("{},{},{}\n".format(vert[0], vert[1], vert[2]))
    vertfile.close()

    print("### APBS ###\n", stderr.decode('utf-8'))
    # from pdb import set_trace; set_trace()

    args = [
        multivalue_bin,
        filename_base + ".csv",
        filename_base + ".dx",
        filename_base + "_out.csv",
    ]
    p2 = Popen(args, stdout=PIPE, stderr=PIPE, cwd=directory)
    stdout, stderr = p2.communicate()

    print("### MULTIVALUE ###\n", stderr.decode('utf-8'))
    # from pdb import set_trace; set_trace()

    charges = numpy.array([0.0] * len(vertices))
    out_file = tmp_file_base + "_out.csv"
    if os.path.exists(out_file):
        chargefile = open(out_file)
        for ix, line in enumerate(chargefile.readlines()):
            charges[ix] = float(line.split(",")[3])
    else:
        atom_xyz = []
        atom_q = []
        q_elem = {
            "O": -0.55, "N": -0.35, "S": -0.15, "P": 1.00,
            "F": -0.20, "CL": -0.15, "BR": -0.10, "I": -0.05,
            "NA": 1.00, "K": 1.00, "MG": 2.00, "CA": 2.00,
            "C": 0.15, "H": 0.05
        }
        with open(pdb_file, "r") as f:
            for ln in f:
                if not (ln.startswith("ATOM") or ln.startswith("HETATM")):
                    continue
                try:
                    x = float(ln[30:38]); y = float(ln[38:46]); z = float(ln[46:54])
                except Exception:
                    continue
                elem = ln[76:78].strip().upper()
                if not elem:
                    an = "".join([c for c in ln[12:16].strip().upper() if c.isalpha()])[:2]
                    if an.startswith("CL"):
                        elem = "CL"
                    elif an.startswith("BR"):
                        elem = "BR"
                    else:
                        elem = an[:1]
                atom_xyz.append([x, y, z])
                atom_q.append(q_elem.get(elem, 0.0))
        if len(atom_xyz) > 0:
            atom_xyz = numpy.asarray(atom_xyz, dtype=float)
            atom_q = numpy.asarray(atom_q, dtype=float)
            k = min(12, len(atom_xyz))
            tree = cKDTree(atom_xyz)
            d, idx = tree.query(vertices, k=k)
            if k == 1:
                d = d[:, None]
                idx = idx[:, None]
            d = numpy.maximum(d, 1e-3)
            w = numpy.exp(-(d ** 2) / (2 * 1.0 ** 2)) / d
            w = w / numpy.sum(w, axis=1, keepdims=True)
            charges = numpy.sum(atom_q[idx] * w, axis=1)

    remove_fn = os.path.join(directory, filename_base)
    for fn in [remove_fn, remove_fn+'.csv', remove_fn+'.dx', remove_fn+'.in', remove_fn+'_out.csv']:
        if os.path.exists(fn):
            os.remove(fn)

    return charges
