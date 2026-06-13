set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN="${PLUGIN:-$ROOT/masif-neosurf-runpro/masif_pymol_plugin.py}"
if [[ -z "${PYMOL_BIN:-}" ]]; then
  if command -v pymol >/dev/null 2>&1; then
    PYMOL_BIN="$(command -v pymol)"
  else
    PYMOL_BIN="pymol"
  fi
fi

PLY=""
OUT_PSE=""
OBJ_NAME="${OBJ_NAME:-surface}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ply) PLY="$2"; shift 2 ;;
    --out_pse) OUT_PSE="$2"; shift 2 ;;
    --obj_name) OBJ_NAME="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PLY" || -z "$OUT_PSE" ]]; then
  echo "usage: export_ply_colored_pse.sh --ply <input.ply> --out_pse <output.pse> [--obj_name name]"
  exit 1
fi

if [[ ! -f "$PLUGIN" ]]; then
  echo "missing plugin: $PLUGIN"
  exit 1
fi
if [[ ! -x "$PYMOL_BIN" ]]; then
  echo "missing pymol: $PYMOL_BIN"
  exit 1
fi

TMP_PML="$(mktemp /tmp/ply2pseXXXXXX.pml)"
TMP_DIR="$(mktemp -d /tmp/ply2pseXXXXXX)"
TMP_PLUGIN="$TMP_DIR/pluginpy.py"
TMP_PLY="$TMP_DIR/inputply.ply"
TMP_PSE="$TMP_DIR/output.pse"
cp "$PLUGIN" "$TMP_PLUGIN"
cp "$PLY" "$TMP_PLY"
cat > "$TMP_PML" <<EOF
reinitialize
run $TMP_PLUGIN
python
__init_plugin__(None)
python end
loadply $TMP_PLY, $OBJ_NAME
bg_color white
set ray_opaque_background, off
set pse_export_version, 1.7
save $TMP_PSE
quit
EOF

"$PYMOL_BIN" -cq "$TMP_PML"
mkdir -p "$(dirname "$OUT_PSE")"
if [[ ! -f "$TMP_PSE" ]]; then
  echo "failed to create pse"
  rm -rf "$TMP_DIR" "$TMP_PML"
  exit 1
fi
mv "$TMP_PSE" "$OUT_PSE"
rm -rf "$TMP_DIR" "$TMP_PML"
echo "saved $OUT_PSE"
