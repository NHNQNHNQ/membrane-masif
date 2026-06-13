# Data Availability

This repository is prepared for public code release. Large generated data and
manuscript working files should be deposited separately and referenced from the
final paper or GitHub release.

## Tracked in Git

- Source code in `scripts/` and `pep71_case_study/`
- Environment specifications in `env/`
- Small example inputs bundled with `masif-neosurf-runpro/`
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

## Recommended Public Release Layout

Use a separate DOI-backed archive or GitHub release assets with this structure:

```text
membrane-masif-data/
  README.md
  input_structures/
  generated_surfaces/
  scoring_tables/
  figure_source_data/
  pep71_case_study/
  checksums.sha256
```

Each folder should include a short README describing provenance, generation
script, software environment, and expected checksums.

## Items To Fill Before Public Release

- Manuscript DOI or preprint URL
- Data archive DOI or release URL
- License for top-level code and data
- Exact accession links for any public database inputs
- Checksums for the public data package
