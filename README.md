# Membrane-MaSIF

Membrane-MaSIF is a publication-oriented workflow for generating membrane and
peptide molecular surface PLY files, rebuilding membrane charge features,
scoring membrane-peptide surface complementarity, and exporting visualizations
used in the accompanying manuscript.

This repository contains the reusable code, environment snapshots, and small
example inputs needed to reproduce the analysis pipeline. Large generated
surfaces, trajectories, PyMOL sessions, model checkpoints, and manuscript
working files are intentionally excluded from version control. See
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md) for the public-data layout.

## Companion Repository

This is one of two code repositories for the accompanying manuscript:

- **Membrane-MaSIF** (this repository): membrane/peptide surface generation,
  feature reconstruction, and membrane–peptide surface-complementarity scoring.
- **[PepGraph-Diffusion](https://github.com/NHNQNHNQ/PepGraph-Diffusion)**: the
  graph latent-diffusion generative model that proposes the candidate
  antimicrobial peptides scored here.

## Repository Layout

- `scripts/`: command-line utilities for preprocessing, PLY cleanup, scoring,
  figure generation, and environment checks.
- `env/`: conda environment file for the analysis environment.
- `surface_preprocessing/`: trimmed MaSIF surface-generation code (Apache-2.0)
  that turns a structure into a PLY molecular surface.

Generated outputs should be written to `result/`, `workdir/`, or another path
outside the Git-tracked source tree.

## Installation

One conda environment covers all analysis; surface generation additionally needs
a few standard external binaries.

### Surface-generation dependencies

`scripts/run_preprocess_ligand_only.sh` turns a cleaned PDB/MOL2 into a PLY
surface using the following external binaries. Install them and export their
paths before running surface generation (pre-generated PLY surfaces are also
available in the data archive — see [`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md)
— so most users can skip this step):

- **MSMS** — molecular-surface triangulation
- **pdb2pqr** — protonation and PQR charge assignment
- **APBS** — Poisson–Boltzmann electrostatics (provides the `multivalue` tool)

```bash
export MSMS_BIN=/path/to/msms
export PDB2PQR_BIN=/path/to/pdb2pqr
export APBS_BIN=/path/to/apbs
export MULTIVALUE_BIN=/path/to/multivalue
```

### Analysis environment

The conda environment in `env/membrane-masif-analysis.yml` (Python 3.11) provides
PLY loading and scoring, figure generation, peptide-diffusion sampling
(PyTorch + PyG), and MD-trajectory analysis (GROMACS / MDAnalysis / mdtraj /
LiPyphilic), plus `numpy`/`scipy`/`pandas`/`scikit-learn`/`networkx`,
`matplotlib`/`seaborn`, `rdkit`/`openbabel`/`biopython`, and
`trimesh`/`plyfile`/`meshio`:

```bash
mamba env create -f env/membrane-masif-analysis.yml
mamba activate membrane-masif
python scripts/verify_env.py
```

## Quick Start

Generate a membrane PLY:

```bash
bash scripts/generate_membrane_ply.sh \
  --pdb /abs/path/membrane_clean.pdb \
  --mol2 /abs/path/membrane_clean.mol2 \
  --name_chain MEM_A \
  --ligand LIG \
  --outdir /abs/path/workdir/membrane_target
```

Generate a peptide PLY:

```bash
bash scripts/generate_peptide_ply.sh \
  --pdb /abs/path/peptide_clean.pdb \
  --mol2 /abs/path/peptide_clean.mol2 \
  --name_chain PEP_A \
  --ligand LIG \
  --outdir /abs/path/workdir/peptide_target
```

Reorder PLY fields, rebuild continuous charge, and validate the result:

```bash
python scripts/reorder_ply_to_pymesh.py \
  --ply /abs/path/workdir/membrane_target/output/all_feat_3l/pred_surfaces/ligand_only.ply

python scripts/rebuild_continuous_charge.py \
  --ply /abs/path/workdir/membrane_target/output/all_feat_3l/pred_surfaces/ligand_only.ply \
  --pdb /abs/path/membrane_clean.pdb

python scripts/validate_ply_charge.py \
  --ply /abs/path/workdir/membrane_target/output/all_feat_3l/pred_surfaces/ligand_only.ply
```

Score membrane-peptide surface matching:

```bash
python scripts/ply_based_matcher_test.py \
  --membrane_ply /abs/path/workdir/membrane_target/output/all_feat_3l/pred_surfaces/ligand_only.ply \
  --peptide_dir /abs/path/workdir/peptide_target/output/all_feat_3l/pred_surfaces \
  --output_csv /abs/path/workdir/matching_results.csv
```

Run the combined membrane/peptide/scoring workflow:

```bash
bash scripts/run_full_pipeline.sh \
  --mem_pdb /abs/path/membrane_clean.pdb \
  --mem_mol2 /abs/path/membrane_clean.mol2 \
  --pep_pdb /abs/path/peptide_clean.pdb \
  --pep_mol2 /abs/path/peptide_clean.mol2 \
  --workdir /abs/path/workdir
```

## Reproducibility Notes

- Surface generation depends on the external MSMS / pdb2pqr / APBS binaries
  listed under Installation; install them separately and export their paths, or
  use the pre-generated PLY surfaces from the data archive.
- The analysis environment is a modern Python 3.11 conda stack (built and tested
  on Apple Silicon) for scoring, plotting, peptide-diffusion sampling, and
  MD-trajectory analysis.
- Scripts that generate manuscript figures may require data files described in
  `DATA_AVAILABILITY.md`.
- Large generated artifacts are excluded by `.gitignore`; archive them in a data
  repository, release asset, or institutional storage before making the GitHub
  repository public.

## Citation

If you use this repository, please cite the accompanying manuscript and the
software dependencies listed in `CITATION.cff` and
`surface_preprocessing/citation.bib`.

## License

This project's original code is released under the [MIT License](LICENSE). The
trimmed MaSIF surface-generation code in `surface_preprocessing/` retains its
original Apache-2.0 license and citation requirements, which take precedence for
those files.
