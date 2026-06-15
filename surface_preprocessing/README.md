# Surface preprocessing (PLY generation)

This is a **trimmed subset** of the MaSIF / MaSIF-neosurf preprocessing code,
retaining only the molecular-surface (PLY) generation path used by this project.
The MaSIF descriptor neural networks, MaSIF-seed search, Rosetta seed
refinement/grafting, pretrained models, and benchmarks have all been removed.

`preprocess_pdb.sh` turns a structure into a molecular surface:

1. extract the requested chain(s) (`masif/source/input_output/extractPDB.py`),
2. protonate with `reduce` (`input_output/protonate.py`),
3. triangulate the surface with MSMS (`triangulation/computeMSMS.py`),
4. compute APBS Poisson–Boltzmann electrostatics, charge, and hydrophobicity
   features and write `output/all_feat_3l/pred_surfaces/ligand_only.ply`.

The complete import closure of this path is the only code kept under
`masif/source/` (`data_preparation/01-pdb_extract_and_triangulate.py` plus the
`default_config/`, `input_output/`, and `triangulation/` modules it imports).

## Dependencies

External binaries (install separately and export their paths, see the top-level
project README):

- **reduce** — add hydrogens
- **MSMS** — molecular-surface triangulation
- **pdb2pqr** + **APBS** (+ the `multivalue` tool) — electrostatics

Python packages: see [`masif/requirements.txt`](masif/requirements.txt).

## Usage

```bash
./preprocess_pdb.sh <PDB_FILE> <PDBID_CHAINID> -o <OUTDIR> [-l <LIGAND>] [-s <SDF>]
```

(This project drives it through `scripts/run_preprocess_ligand_only.sh` /
`scripts/generate_membrane_ply.sh` in the parent repository.)

## PyMOL plugin

[`masif_pymol_plugin.py`](masif_pymol_plugin.py) visualizes the generated `.ply`
surfaces. In PyMOL: `Install New Plugin -> Install from local file`, then
`loadply surface.ply`.

## License and attribution

This code is derived from MaSIF (Gainza et al.) and MaSIF-neosurf
(Marchand et al., *Nature*, 2025, doi:10.1038/s41586-024-08435-4) and remains
under the **Apache-2.0** license. The original license and citations are kept in
[`LICENSE`](LICENSE), [`citation.bib`](citation.bib), and
[`masif/LICENSE`](masif/LICENSE) / [`masif/citation.bib`](masif/citation.bib),
and must be preserved.
