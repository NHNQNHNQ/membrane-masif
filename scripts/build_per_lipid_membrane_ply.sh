#!/bin/bash
# 基于"单分子分解-重组"策略的膜 PLY 生成（论文 Part 1 Method 段）。
#
# 思路：
#   1. 输入一个膜 PDB（含数百-数千个脂质分子 + 可选的肽/蛋白）
#   2. 按 (chain, residue_index) 切出每一个脂质子分子，写到独立 PDB
#   3. 对每个子分子调用 generate_peptide_ply.sh 生成局部 PLY
#   4. 把所有子 PLY 顶点 / 法向 / 特征 / 面（需偏移）拼接成完整膜 PLY
#   5. 调用 remove_ply_islands.py + reorder_ply_to_pymesh.py 做最后整形
#
# 与"对整张膜直接 MSMS"相比，单分子重组保留了每个脂质分子精细的局部曲率与
# RDKit 派生原子级特征，避免了大网格上的 self-intersection 与特征污染。
#
# usage:
#   bash scripts/build_per_lipid_membrane_ply.sh \
#       --pdb /abs/path/membrane.pdb \
#       --outdir /abs/path/work \
#       --output /abs/path/mem.ply \
#       [--lipid-resnames "POPC POPE POPG REL"] \
#       [--parallel 8]
#
# 输出：
#   --output 给出的目标 PLY
#   --outdir 下保留：split_pdbs/ <子 PDB>，per_lipid_plys/ <子 PLY>，merge.log

set -e
# pipefail / batch 内部 partial failures 不阻塞整体（少数脂质 MSMS 失败可接受）

PDB=""
OUTDIR=""
OUTPUT=""
LIPID_RESNAMES=""   # 空表示用所有非水非离子非蛋白
PARALLEL=4

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pdb)             PDB="$2"; shift 2 ;;
    --outdir)          OUTDIR="$2"; shift 2 ;;
    --output)          OUTPUT="$2"; shift 2 ;;
    --lipid-resnames)  LIPID_RESNAMES="$2"; shift 2 ;;
    --parallel)        PARALLEL="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
done

if [[ -z "$PDB" || -z "$OUTDIR" || -z "$OUTPUT" ]]; then
  echo "usage: --pdb FILE --outdir DIR --output FILE [--lipid-resnames \"NAMES\"] [--parallel N]"
  exit 2
fi
if [[ -z "${MSMS_BIN:-}" ]]; then
  echo "MSMS_BIN not set. source scripts/activate_pipeline.sh first."
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPLIT_DIR="$OUTDIR/split_pdbs"
PLY_DIR="$OUTDIR/per_lipid_plys"
LOG="$OUTDIR/merge.log"
mkdir -p "$SPLIT_DIR" "$PLY_DIR"
: > "$LOG"

echo "[$(date +%T)] step 1/4: 单分子拆分 -> $SPLIT_DIR"
python "$SCRIPT_DIR/_split_pdb_per_residue.py" \
    --pdb "$PDB" \
    --outdir "$SPLIT_DIR" \
    --resnames "$LIPID_RESNAMES" 2>&1 | tee -a "$LOG"

N_SPLIT=$(find "$SPLIT_DIR" -maxdepth 1 -name "*.pdb" -not -name "._*" | wc -l | tr -d ' ')
echo "[$(date +%T)]   split=$N_SPLIT"

echo "[$(date +%T)] step 2/4: 单分子 PLY 生成 (parallel=$PARALLEL)"
bash "$ROOT/scripts/batch_generate_peptide_ply.sh" \
    --input-dir "$SPLIT_DIR" \
    --output-dir "$PLY_DIR" \
    --prefix "" \
    --parallel "$PARALLEL" 2>&1 | tee -a "$LOG" || true  # 部分脂质失败可接受

N_PLY=$(find "$PLY_DIR" -maxdepth 1 -name "*.ply" -not -name "._*" | wc -l | tr -d ' ')
echo "[$(date +%T)]   per_lipid_plys=$N_PLY"

echo "[$(date +%T)] step 3/4: 拼接子 PLY -> $OUTPUT"
python "$SCRIPT_DIR/_concat_plys.py" \
    --input-dir "$PLY_DIR" \
    --output "$OUTPUT" 2>&1 | tee -a "$LOG"

echo "[$(date +%T)] step 4/4: 孤岛清理 + PyMesh 字段重排（in-place）"
python "$SCRIPT_DIR/remove_ply_islands.py" --ply "$OUTPUT" 2>&1 | tee -a "$LOG"
python "$SCRIPT_DIR/reorder_ply_to_pymesh.py" --ply "$OUTPUT" 2>&1 | tee -a "$LOG"

echo "[$(date +%T)] DONE -> $OUTPUT"
