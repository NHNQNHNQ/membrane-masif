# Publication Release Checklist

Use this before making `NHNQNHNQ/membrane-masif` public.

## Repository Hygiene

- [ ] Initialize or update the Git repository at the intended release root.
- [ ] Confirm the remote is `git@github.com:NHNQNHNQ/membrane-masif.git`.
- [ ] Run `git status --short --ignored` and confirm large outputs are ignored.
- [ ] Remove AppleDouble files (`._*`), `.DS_Store`, and `__pycache__/`.
- [ ] Confirm no local-only paths, credentials, access keys, or unpublished raw data are
      tracked.
- [ ] Choose and add a top-level `LICENSE`.

## Reproducibility

- [ ] Verify the analysis environment with `python scripts/verify_env.py`.
- [ ] Verify the preprocessing environment on Linux if regenerating PLY files.
- [ ] Run at least one small surface-generation or scoring example.
- [ ] Record software versions and external binary paths in a release note.
- [ ] Add public data archive links to `DATA_AVAILABILITY.md`.

## Manuscript Links

- [ ] Update `CITATION.cff` with final title, authors, DOI, and release version.
- [ ] Add the manuscript DOI or preprint link to `README.md`.
- [ ] Confirm MaSIF/Neosurf citations are preserved.
- [ ] Confirm figure source-data files are either included in the data archive or
      clearly described.
