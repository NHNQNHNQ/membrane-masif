#!/bin/bash
# source 这个脚本激活 membrane-masif env 并配置 PLY 流水线所需的二进制路径。
# 兼容 bash 和 zsh。
#
# usage:
#   source scripts/activate_pipeline.sh

if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  _SELF="${BASH_SOURCE[0]}"
elif [[ -n "${(%):-%x}" ]]; then
  _SELF="${(%):-%x}"
else
  _SELF="$0"
fi
_ROOT="$(cd "$(dirname "$_SELF")/.." && pwd)"
_MINIFORGE="${MINIFORGE_HOME:-$HOME/miniforge3}"

source "$_MINIFORGE/etc/profile.d/conda.sh"
conda activate membrane-masif

export MSMS_BIN="$_ROOT/bin/msms_Arm64_2.6.1/msms"
export APBS_BIN="$(command -v apbs)"
export PDB2PQR_BIN="$(command -v pdb2pqr)"
export MULTIVALUE_BIN="$_ROOT/bin/multivalue"

_check() {
  local var="$1"
  local val
  eval "val=\${$var:-}"
  if [[ -z "$val" || ! -x "$val" ]]; then
    echo "[err] $var not found or not executable: $val"
    return 1
  fi
  echo "[ok ] $var=$val"
}
_check MSMS_BIN
_check APBS_BIN
_check PDB2PQR_BIN
_check MULTIVALUE_BIN
unset -f _check
unset _SELF _ROOT _MINIFORGE
