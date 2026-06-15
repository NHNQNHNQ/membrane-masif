set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
YML="$ROOT/env/membrane-masif-analysis.yml"
TMP_YML="$ROOT/env/.membrane-masif.no-prefix.yml"
ENV_NAME="${ENV_NAME:-membrane-masif}"
export YML TMP_YML

python - <<'PY'
import os
from pathlib import Path
src = Path(os.environ["YML"])
dst = Path(os.environ["TMP_YML"])
lines = src.read_text().splitlines()
out = [ln for ln in lines if not ln.startswith("prefix:")]
dst.write_text("\n".join(out) + "\n")
PY

mamba env create -n "$ENV_NAME" -f "$TMP_YML" --force
rm -f "$TMP_YML"

echo "created $ENV_NAME"
