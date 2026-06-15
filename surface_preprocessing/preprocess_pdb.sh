#!/bin/bash
#
# Surface preprocessing: molecular-surface (PLY) generation.
#
# Derived from the MaSIF / Neosurf preprocessing pipeline
# (Gainza et al., released under Apache-2.0 — see ./LICENSE and ./citation.bib).
# Trimmed to the surface-only path used by this project: extract a chain,
# protonate it, and compute the MSMS molecular surface with APBS electrostatics,
# Poisson-Boltzmann charge, and hydrophobicity features, then export a PLY.
#
# Requires the external binaries MSMS / pdb2pqr / APBS / multivalue, exported as
# MSMS_BIN / PDB2PQR_BIN / APBS_BIN / MULTIVALUE_BIN.
#
# Usage:
#   preprocess_pdb.sh <PDB_FILE> <PDBID_CHAINID> -o <OUTDIR> [-l <LIGAND>] [-s <SDF>]
# (the legacy -p/--ply-only flag is accepted and ignored; PLY is always the output)

### USER INPUT ################################################################

while [[ $# -gt 0 ]]; do
  case $1 in
    -o|--outdir)   OUTDIR=$2; shift 2 ;;
    -l|--ligand)   LIGAND="$2"; shift 2 ;;
    -s|--sdf)      SDFFILE="$(realpath "$2")"; shift 2 ;;
    -p|--ply-only) shift ;;                 # accepted for backward compatibility
    -*|--*)        echo "Unknown option $1"; exit 1 ;;
    *)             POSITIONAL_ARGS+=("$1"); shift ;;
  esac
done
set -- "${POSITIONAL_ARGS[@]}"
PDBFILE="$(realpath "$1")"
NAME_CHAIN=$2

if [ -z "$PDBFILE" ]; then echo "[ERROR] Please provide an input PDB file"; exit 1; fi
if [ -z "$NAME_CHAIN" ]; then echo "[ERROR] Please provide the protein definition (as <PDBID_CHAINID>)"; exit 1; fi
if [ -z "$OUTDIR" ]; then echo "[ERROR] Please provide an output directory"; exit 1; fi
if [ -z "$LIGAND" ]; then echo "[INFO] No small molecule provided"; fi

###############################################################################

BASEDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
MASIF_SOURCE=$BASEDIR/masif/source/

export PYTHONPATH=$MASIF_SOURCE
export PYTHONPATH=$PYTHONPATH:$OUTDIR
export TMPDIR=$OUTDIR/tmp/

mkdir -p "$OUTDIR"
OUTDIR="$(realpath "$OUTDIR")"
cd "$OUTDIR" || exit 1

mkdir -p data_preparation/00-raw_pdbs/
mkdir -p "$TMPDIR"

echo "Precomputing surface on $PDBFILE"
PDB_ID=$(echo "$NAME_CHAIN" | cut -d"_" -f1)
CHAIN1=$(echo "$NAME_CHAIN" | cut -d"_" -f2)
cp "$PDBFILE" data_preparation/00-raw_pdbs/"$PDB_ID".pdb

python -W ignore "$MASIF_SOURCE"/data_preparation/01-pdb_extract_and_triangulate.py "$PDB_ID"_"$CHAIN1" "$LIGAND" "$SDFFILE"
return_code=$?

if [ $return_code -eq 0 ]; then
    mkdir -p output/all_feat_3l/pred_surfaces
    cp data_preparation/01-benchmark_surfaces/"$PDB_ID"_"$CHAIN1".ply output/all_feat_3l/pred_surfaces/ligand_only.ply
fi

cd - > /dev/null
exit $return_code
