set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MASIF_ROOT="${MASIF_ROOT:-$ROOT/masif-neosurf-runpro}"

PDB=""
OUTDIR=""
NAME_CHAIN=""
CONDA_BIN="${CONDA_BIN:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pdb) PDB="$2"; shift 2 ;;
    --mol2) shift 2 ;;
    --outdir) OUTDIR="$2"; shift 2 ;;
    --name_chain) NAME_CHAIN="$2"; shift 2 ;;
    --ligand) shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PDB" || -z "$OUTDIR" ]]; then
  echo "usage: run_preprocess_ligand_only.sh --pdb <pdb> --outdir <outdir> [--name_chain <PDB_CHAIN>]"
  exit 1
fi

if [[ -z "${MSMS_BIN:-}" || -z "${PDB2PQR_BIN:-}" || -z "${APBS_BIN:-}" || -z "${MULTIVALUE_BIN:-}" ]]; then
  echo "please export MSMS_BIN/PDB2PQR_BIN/APBS_BIN/MULTIVALUE_BIN first"
  exit 1
fi

if [[ ! -f "$MASIF_ROOT/preprocess_pdb.sh" ]]; then
  echo "missing preprocess script: $MASIF_ROOT/preprocess_pdb.sh"
  exit 1
fi

mkdir -p "$OUTDIR/input"
if [[ -z "$NAME_CHAIN" ]]; then
  base="$(basename "$PDB")"
  base="${base%.*}"
  NAME_CHAIN="${base}_A"
fi

if [[ -n "$CONDA_BIN" ]]; then
  export PATH="$CONDA_BIN:$PATH"
fi
bash "$MASIF_ROOT/preprocess_pdb.sh" "$PDB" "$NAME_CHAIN" -o "$OUTDIR" -l LIG_A --ply-only

EXPECTED_PLY="$OUTDIR/output/all_feat_3l/pred_surfaces/ligand_only.ply"
if [[ ! -f "$EXPECTED_PLY" ]]; then
  echo "preprocess failed: missing $EXPECTED_PLY"
  exit 3
fi

echo "preprocess done: $OUTDIR"
