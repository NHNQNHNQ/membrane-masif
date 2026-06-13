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
- `env/`: conda environment files for the original Linux MaSIF runtime and the
  newer analysis environment.
- `masif-neosurf-runpro/`: bundled MaSIF/Neosurf runner used by the preprocessing
  workflow.
- `pep71_case_study/`: Pep71 membrane-bound conformer analysis scripts and notes.
- `docs/`: method notes and implementation plans retained for transparency.

Generated outputs should be written to `result/`, `workdir/`, or another path
outside the Git-tracked source tree.

## Installation

Two environments are provided because the original MaSIF preprocessing stack and
the downstream analysis stack have different platform requirements.

### Linux preprocessing environment

Use this environment when regenerating MaSIF-style molecular surfaces with
MSMS/APBS/pdb2pqr/pymesh:

```bash
mamba env create -f env/membrane-masif.yml
mamba activate membrane-masif
```

The following external binaries must be installed separately and exported before
running surface generation:

```bash
export MSMS_BIN=/path/to/msms
export PDB2PQR_BIN=/path/to/pdb2pqr
export APBS_BIN=/path/to/apbs
export MULTIVALUE_BIN=/path/to/multivalue
```

### Analysis environment

Use this environment for PLY loading, scoring, plotting, Pepdiffusion outputs,
and MD trajectory analysis:

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

- The Linux preprocessing stack follows the legacy MaSIF dependency chain and is
  most reproducible on Linux x86_64.
- The analysis environment is intended for modern Python-based scoring and
  plotting tasks. It does not replace the original MSMS/APBS/pymesh surface
  generation stack.
- Scripts that generate manuscript figures may require data files described in
  `DATA_AVAILABILITY.md`.
- Large generated artifacts are excluded by `.gitignore`; archive them in a data
  repository, release asset, or institutional storage before making the GitHub
  repository public.

## Citation

If you use this repository, please cite the accompanying manuscript and the
software dependencies listed in `CITATION.cff` and
`masif-neosurf-runpro/citation.bib`.

## License

This project's original code is released under the [MIT License](LICENSE). The
bundled MaSIF/Neosurf components in `masif-neosurf-runpro/` retain their original
licenses (Apache-2.0 for MaSIF) and citation requirements, which take precedence
for those files.
