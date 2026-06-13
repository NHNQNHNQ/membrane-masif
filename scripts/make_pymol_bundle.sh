set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN="${PLUGIN:-$ROOT/masif-neosurf-runpro/masif_pymol_plugin.py}"

PLY=""
OUTDIR=""
OBJ_NAME="${OBJ_NAME:-surface}"
PSE_NAME="${PSE_NAME:-colored_output.pse}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ply) PLY="$2"; shift 2 ;;
    --outdir) OUTDIR="$2"; shift 2 ;;
    --obj_name) OBJ_NAME="$2"; shift 2 ;;
    --pse_name) PSE_NAME="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PLY" || -z "$OUTDIR" ]]; then
  echo "usage: make_pymol_bundle.sh --ply <input.ply> --outdir <bundle_dir> [--obj_name name] [--pse_name output.pse]"
  exit 1
fi
if [[ ! -f "$PLY" || ! -f "$PLUGIN" ]]; then
  echo "missing ply or plugin"
  exit 1
fi

mkdir -p "$OUTDIR"
cp "$PLY" "$OUTDIR/inputply.ply"
cp "$PLUGIN" "$OUTDIR/masif_pymol_plugin.py"
cat > "$OUTDIR/make_pse.pml" <<EOF
reinitialize
run masif_pymol_plugin.py
python
__init_plugin__(None)
python end
loadply inputply.ply, $OBJ_NAME
bg_color white
set ray_opaque_background, off
set pse_export_version, 1.7
save $PSE_NAME
quit
EOF
cat > "$OUTDIR/README.txt" <<EOF
1) 把本目录整体拷贝到你的Windows机器
2) 在PyMOL中进入本目录后执行: @make_pse.pml
3) 生成的会话文件: $PSE_NAME
EOF
echo "bundle ready: $OUTDIR"
