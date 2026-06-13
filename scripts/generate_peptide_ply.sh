set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PDB=""
MOL2=""
OUTDIR=""
NAME_CHAIN=""
LIGAND="LIG"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pdb) PDB="$2"; shift 2 ;;
    --mol2) MOL2="$2"; shift 2 ;;
    --outdir) OUTDIR="$2"; shift 2 ;;
    --name_chain) NAME_CHAIN="$2"; shift 2 ;;
    --ligand) LIGAND="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PDB" || -z "$MOL2" || -z "$OUTDIR" ]]; then
  echo "usage: generate_peptide_ply.sh --pdb <peptide_clean.pdb> --mol2 <peptide_clean.mol2> --outdir <output_dir> [--name_chain <PDB_CHAIN>] [--ligand <LIG>]"
  exit 1
fi

bash "$SCRIPT_DIR/run_preprocess_ligand_only.sh" --pdb "$PDB" --mol2 "$MOL2" --outdir "$OUTDIR" --name_chain "${NAME_CHAIN:-}" --ligand "$LIGAND"
echo "peptide ply generated under: $OUTDIR/output/all_feat_3l/pred_surfaces"
