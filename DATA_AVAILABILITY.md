# Data Availability

This repository is prepared for public code release. Large generated data and
manuscript working files should be deposited separately and referenced from the
final paper or GitHub release.

## Tracked in Git

- Source code in `scripts/`
- Trimmed MaSIF surface-generation code in `surface_preprocessing/`
- Environment specification in `env/`
- Method notes and public documentation

## Not Tracked in Git

The following artifacts are intentionally excluded by `.gitignore`:

- Generated PLY collections and MaSIF intermediate output directories
- PyMOL session files (`*.pse`)
- GROMACS trajectories and binary run files (`*.xtc`, `*.trr`, `*.tpr`,
  `*.edr`, `*.cpt`)
- Model checkpoints (`*.pt`, `*.pth`, `*.ckpt`)
- Manuscript figure exports, TIFF/TEM images, ZIP/TAR archives, and working
  document files
- Local absolute-path datasets used during development

## Data Archive

The molecular dynamics trajectories (four LL-37 / *A. baumannii* outer-membrane
systems, 200 ns production each) and the mode-specific membrane PLY surfaces
(control / bind / insert / pore) are deposited at Zenodo:

**https://doi.org/10.5281/zenodo.20709918**

Per-peptide and per-candidate PLY surface collections and membrane-matching
score tables are not deposited; they are regenerable with this pipeline from the
input structures and the deposited membrane surfaces.

## Still To Fill (on manuscript publication)

- Manuscript DOI or preprint URL
