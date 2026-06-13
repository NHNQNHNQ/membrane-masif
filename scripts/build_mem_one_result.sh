set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
OBABEL_BIN="${OBABEL_BIN:-obabel}"

MEM_PDB="${MEM_PDB:-}"
ONE_PDB="${ONE_PDB:-}"

if [[ -z "$MEM_PDB" || -z "$ONE_PDB" ]]; then
  echo "please set MEM_PDB and ONE_PDB to input PDB files"
  exit 1
fi

RESULT_DIR="${RESULT_DIR:-$ROOT/result}"
mkdir -p "$RESULT_DIR/input" "$RESULT_DIR/mem_target" "$RESULT_DIR/one_target" "$RESULT_DIR/images" "$RESULT_DIR/pse"
rm -rf "$RESULT_DIR/mem_target" "$RESULT_DIR/one_target"
mkdir -p "$RESULT_DIR/mem_target" "$RESULT_DIR/one_target"

MEM_CLEAN="$RESULT_DIR/input/mem-ReLPS_clean.pdb"
ONE_CLEAN="$RESULT_DIR/input/one-ReLPS_clean.pdb"
MEM_MOL2="$RESULT_DIR/input/mem-ReLPS_clean.mol2"
ONE_MOL2="$RESULT_DIR/input/one-ReLPS_clean.mol2"

"$PYTHON_BIN" "$SCRIPT_DIR/pdb_cleaner.py" "$MEM_PDB" "$MEM_CLEAN"
"$PYTHON_BIN" "$SCRIPT_DIR/pdb_cleaner.py" "$ONE_PDB" "$ONE_CLEAN"

"$OBABEL_BIN" "$MEM_CLEAN" -O "$MEM_MOL2" >/dev/null 2>&1
"$OBABEL_BIN" "$ONE_CLEAN" -O "$ONE_MOL2" >/dev/null 2>&1

bash "$SCRIPT_DIR/run_preprocess_ligand_only.sh" --pdb "$MEM_CLEAN" --mol2 "$MEM_MOL2" --outdir "$RESULT_DIR/mem_target" --name_chain MEM_A --ligand LIG
bash "$SCRIPT_DIR/run_preprocess_ligand_only.sh" --pdb "$ONE_CLEAN" --mol2 "$ONE_MOL2" --outdir "$RESULT_DIR/one_target" --name_chain ONE_A --ligand LIG

MEM_PLY_RAW="$RESULT_DIR/mem_target/output/all_feat_3l/pred_surfaces/ligand_only.ply"
ONE_PLY_RAW="$RESULT_DIR/one_target/output/all_feat_3l/pred_surfaces/ligand_only.ply"
MEM_PLY="$RESULT_DIR/mem-ReLPS.ply"
ONE_PLY="$RESULT_DIR/one-ReLPS.ply"
cp "$MEM_PLY_RAW" "$MEM_PLY"
cp "$ONE_PLY_RAW" "$ONE_PLY"

"$PYTHON_BIN" "$SCRIPT_DIR/reorder_ply_to_pymesh.py" --ply "$MEM_PLY"
"$PYTHON_BIN" "$SCRIPT_DIR/reorder_ply_to_pymesh.py" --ply "$ONE_PLY"
"$PYTHON_BIN" "$SCRIPT_DIR/remove_ply_islands.py" --ply "$MEM_PLY" --keep_largest_only
"$PYTHON_BIN" "$SCRIPT_DIR/remove_ply_islands.py" --ply "$ONE_PLY" --min_vertices 40 --keep_ratio 0.01
"$PYTHON_BIN" "$SCRIPT_DIR/rebuild_continuous_charge.py" --ply "$MEM_PLY" --pdb "$MEM_CLEAN"
"$PYTHON_BIN" "$SCRIPT_DIR/rebuild_continuous_charge.py" --ply "$ONE_PLY" --pdb "$ONE_CLEAN"
"$PYTHON_BIN" "$SCRIPT_DIR/validate_ply_charge.py" --ply "$MEM_PLY" > "$RESULT_DIR/mem-ReLPS.charge.txt"
"$PYTHON_BIN" "$SCRIPT_DIR/validate_ply_charge.py" --ply "$ONE_PLY" > "$RESULT_DIR/one-ReLPS.charge.txt"

"$PYTHON_BIN" "$SCRIPT_DIR/visualize_ply.py" --ply "$MEM_PLY" --out_png "$RESULT_DIR/images/mem-ReLPS_charge.png"
"$PYTHON_BIN" "$SCRIPT_DIR/visualize_ply.py" --ply "$ONE_PLY" --out_png "$RESULT_DIR/images/one-ReLPS_charge.png"

if [[ -x "$SCRIPT_DIR/export_ply_colored_pse.sh" ]]; then
  bash "$SCRIPT_DIR/export_ply_colored_pse.sh" --ply "$MEM_PLY" --out_pse "$RESULT_DIR/pse/mem-ReLPS_colored.pse" || true
  bash "$SCRIPT_DIR/export_ply_colored_pse.sh" --ply "$ONE_PLY" --out_pse "$RESULT_DIR/pse/one-ReLPS_colored.pse" || true
fi

echo "result_dir=$RESULT_DIR"
echo "mem_ply=$MEM_PLY"
echo "one_ply=$ONE_PLY"
