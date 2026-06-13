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
REFERENCE_PSE=""
FEATURE="all"
OBJ_NAME="${OBJ_NAME:-surface}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ply) PLY="$2"; shift 2 ;;
    --out_pse) OUT_PSE="$2"; shift 2 ;;
    --reference_pse) REFERENCE_PSE="$2"; shift 2 ;;
    --feature) FEATURE="$2"; shift 2 ;;
    --obj_name) OBJ_NAME="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PLY" || -z "$OUT_PSE" || -z "$REFERENCE_PSE" ]]; then
  echo "usage: export_mem_view_pse.sh --ply <input.ply> --out_pse <output.pse> --reference_pse <reference.pse> [--feature all|charge|hphob|hbond|ddc|si] [--obj_name name]"
  exit 1
fi

case "$FEATURE" in
  all) KEEP_PREFIX="" ;;
  charge) KEEP_PREFIX="pb_" ;;
  hphob) KEEP_PREFIX="hphobic_" ;;
  hbond) KEEP_PREFIX="hbond_" ;;
  ddc) KEEP_PREFIX="ddc_" ;;
  si) KEEP_PREFIX="si_" ;;
  *) echo "unsupported feature: $FEATURE"; exit 1 ;;
esac

TMP_PML="$(mktemp /tmp/memviewXXXXXX.pml)"
TMP_DIR="$(mktemp -d /tmp/memviewXXXXXX)"
TMP_PLUGIN="$TMP_DIR/pluginpy.py"
TMP_PLY="$TMP_DIR/inputply.ply"
TMP_PSE="$TMP_DIR/output.pse"
cp "$PLUGIN" "$TMP_PLUGIN"
cp "$PLY" "$TMP_PLY"
cat > "$TMP_PML" <<EOF
reinitialize
load $REFERENCE_PSE
python
ref_view = cmd.get_view()
python end
reinitialize
run $TMP_PLUGIN
python
__init_plugin__(None)
python end
loadply $TMP_PLY, $OBJ_NAME
$(if [[ -n "$KEEP_PREFIX" ]]; then printf '%s\n%s\n' "disable all" "enable ${KEEP_PREFIX}*"; fi)
bg_color white
set ray_opaque_background, off
set pse_export_version, 1.7
set specular, 0
set depth_cue, 0
set orthoscopic, on
python
cmd.set_view(ref_view)
python end
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
