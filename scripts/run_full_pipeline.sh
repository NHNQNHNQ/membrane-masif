set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

MEM_PDB=""
MEM_MOL2=""
PEP_PDB=""
PEP_MOL2=""
WORKDIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mem_pdb) MEM_PDB="$2"; shift 2 ;;
    --mem_mol2) MEM_MOL2="$2"; shift 2 ;;
    --pep_pdb) PEP_PDB="$2"; shift 2 ;;
    --pep_mol2) PEP_MOL2="$2"; shift 2 ;;
    --workdir) WORKDIR="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$MEM_PDB" || -z "$MEM_MOL2" || -z "$PEP_PDB" || -z "$PEP_MOL2" || -z "$WORKDIR" ]]; then
  echo "usage: run_full_pipeline.sh --mem_pdb <mem.pdb> --mem_mol2 <mem.mol2> --pep_pdb <pep.pdb> --pep_mol2 <pep.mol2> --workdir <dir>"
  exit 1
fi

MEM_OUT="$WORKDIR/membrane_target"
PEP_OUT="$WORKDIR/peptide_target"
RESULT_DIR="$WORKDIR/match_results"
mkdir -p "$RESULT_DIR"

bash "$SCRIPT_DIR/generate_membrane_ply.sh" --pdb "$MEM_PDB" --mol2 "$MEM_MOL2" --outdir "$MEM_OUT" --name_chain MEM_A --ligand LIG
bash "$SCRIPT_DIR/generate_peptide_ply.sh" --pdb "$PEP_PDB" --mol2 "$PEP_MOL2" --outdir "$PEP_OUT" --name_chain PEP_A --ligand LIG

MEM_PLY="$MEM_OUT/output/all_feat_3l/pred_surfaces/ligand_only.ply"
PEP_DIR="$PEP_OUT/output/all_feat_3l/pred_surfaces"

"$PYTHON_BIN" "$SCRIPT_DIR/reorder_ply_to_pymesh.py" --ply "$MEM_PLY"
"$PYTHON_BIN" "$SCRIPT_DIR/rebuild_continuous_charge.py" --ply "$MEM_PLY" --pdb "$MEM_PDB"
"$PYTHON_BIN" "$SCRIPT_DIR/ply_based_matcher_test.py" \
  --membrane_ply "$MEM_PLY" \
  --peptide_dir "$PEP_DIR" \
  --output_csv "$RESULT_DIR/matching_results.csv"
"$PYTHON_BIN" "$SCRIPT_DIR/visualize_ply.py" --ply "$MEM_PLY" --out_png "$RESULT_DIR/membrane_charge.png"

echo "done"
echo "membrane ply: $MEM_PLY"
echo "peptide dir: $PEP_DIR"
echo "match csv: $RESULT_DIR/matching_results.csv"
echo "preview png: $RESULT_DIR/membrane_charge.png"
