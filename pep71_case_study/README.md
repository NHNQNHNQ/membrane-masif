# Pep71 membrane-bound conformer case study

This directory documents the Pep71 membrane-bound conformer analysis used during
manuscript preparation.

## Rationale

Pep71 (USER002, `RRKVKDIMKVVELTWRDWGE`) was evaluated as a lead peptide in the
manuscript. The development analysis compared the AlphaFold monomer surface with
membrane-bound conformers sampled from molecular dynamics. The working
hypothesis was that Pep71's functional surface is the membrane-bound conformer
rather than the isolated solution monomer.

## Analysis Flow

1. Build or obtain Pep71 membrane-bound MD trajectories.
2. Extract representative late-trajectory conformers.
3. Rebuild peptide PLY surfaces with the Membrane-MaSIF preprocessing workflow.
4. Score each conformer against the membrane-mode surface panel.
5. Compare monomer and membrane-bound feature vectors, logits, and ranks.

The exploratory scripts used during local development contain site-specific HPC
paths and are intentionally excluded from the first public Git snapshot. A
clean, data-archive-backed reproduction workflow should be added here when the
public Pep71 trajectory and surface files are deposited.

## Public Input Included

- `inputs/pep71_for_charmm_gui.pdb`: Pep71 starting structure prepared for
  membrane-system construction.

## Release TODO

- Add public trajectory/surface archive links.
- Add checksums for Pep71 PLY and scoring tables.
- Add a path-independent reproduction command once the public data package is
  available.
