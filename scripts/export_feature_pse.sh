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
FEATURE=""
OBJ_NAME="${OBJ_NAME:-surface}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ply) PLY="$2"; shift 2 ;;
    --out_pse) OUT_PSE="$2"; shift 2 ;;
    --feature) FEATURE="$2"; shift 2 ;;
    --obj_name) OBJ_NAME="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PLY" || -z "$OUT_PSE" || -z "$FEATURE" ]]; then
  echo "usage: export_feature_pse.sh --ply <input.ply> --out_pse <output.pse> --feature <ddc|hphob|charge|hbond> [--obj_name name]"
  exit 1
fi

case "$FEATURE" in
  charge) KEEP_PREFIX="pb_" ;;
  hphob) KEEP_PREFIX="hphobic_" ;;
  hbond) KEEP_PREFIX="hbond_" ;;
  ddc) KEEP_PREFIX="ddc_" ;;
  *) echo "unsupported feature: $FEATURE"; exit 1 ;;
esac

TMP_PML="$(mktemp /tmp/featurepseXXXXXX.pml)"
TMP_DIR="$(mktemp -d /tmp/featurepseXXXXXX)"
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
disable all
enable ${KEEP_PREFIX}*
bg_color white
set ray_opaque_background, off
set pse_export_version, 1.7
set specular, 0
set depth_cue, 0
set orthoscopic, on
zoom ${KEEP_PREFIX}*, 2
save $TMP_PSE
quit
EOF

"$PYMOL_BIN" -cq "$TMP_PML"
mkdir -p "$(dirname "$OUT_PSE")"
if [[ ! -f "$TMP_PSE" ]]; then
  echo "failed to create feature pse"
  rm -rf "$TMP_DIR" "$TMP_PML"
  exit 1
fi
mv "$TMP_PSE" "$OUT_PSE"
rm -rf "$TMP_DIR" "$TMP_PML"
echo "saved $OUT_PSE"
