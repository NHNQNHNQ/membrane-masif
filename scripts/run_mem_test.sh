set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

PLY=""
PDB=""
DO_REORDER="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ply) PLY="$2"; shift 2 ;;
    --pdb) PDB="$2"; shift 2 ;;
    --no-reorder) DO_REORDER="0"; shift 1 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PLY" || -z "$PDB" ]]; then
  echo "usage: run_mem_test.sh --ply <mem.ply> --pdb <mem_clean.pdb> [--no-reorder]"
  exit 1
fi

"$PYTHON_BIN" "$SCRIPT_DIR/check_env.py"

if [[ "$DO_REORDER" == "1" ]]; then
  "$PYTHON_BIN" "$SCRIPT_DIR/reorder_ply_to_pymesh.py" --ply "$PLY"
fi

"$PYTHON_BIN" "$SCRIPT_DIR/rebuild_continuous_charge.py" --ply "$PLY" --pdb "$PDB"
"$PYTHON_BIN" "$SCRIPT_DIR/validate_ply_charge.py" --ply "$PLY"

echo "mem test done: $PLY"
