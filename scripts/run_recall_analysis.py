"""跑全量 recall 分析（Fig 2b）：
  对 recall_pos / recall_neg 两组肽 PLY，依次以三模式膜 PLY 为参考、计算
  ply_based_matcher_test 的综合得分；输出 ROC / PR / 分层指标。

输入：
  --mem-ply       一张膜参考 PLY（或多张，逗号分隔，会取最大分数）
  --recall-pos    正样本肽 PLY 目录
  --recall-neg    负样本肽 PLY 目录
  --weights-json  train_ply_weights.py 输出 (charge/hbond/hphob/bias)
  --output-dir    指标 + 中间分数 CSV 输出目录
  --tsv           current_success_structures.tsv (含 source / length / 序列等)，可选
                  指定后会输出按数据源 / 长度桶分层的 recall

usage:
  python scripts/run_recall_analysis.py \
      --mem-ply       result/fig2a/charu/membrane_patch.ply \
      --recall-pos    result_plys/recall_pos \
      --recall-neg    result_plys/recall_neg \
      --weights-json  result/learned_weights.json \
      --output-dir    result/fig2b
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import mannwhitneyu
from sklearn.metrics import (
    auc,
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


def read_ply(path: Path):
    text = path.read_text(errors="ignore").splitlines()
    nv = 0
    props = []
    body_start = 0
    for i, line in enumerate(text):
        if line.startswith("element vertex"):
            nv = int(line.split()[2])
        elif line.startswith("property float"):
            props.append(line.split()[-1])
        elif line.strip() == "end_header":
            body_start = i + 1
            break
    if nv == 0:
        raise ValueError(f"empty ply: {path}")
    rows = [ln.split() for ln in text[body_start : body_start + nv]]
    arr = np.asarray([[float(x) for x in r[: len(props)]] for r in rows], dtype=float)
    return arr, {p: i for i, p in enumerate(props)}


def get_field(arr, mp, name):
    if name in mp:
        return arr[:, mp[name]]
    alt = "vertex_" + name
    if alt in mp:
        return arr[:, mp[alt]]
    raise KeyError(name)


# 与训练 (train_ply_weights.py) 完全一致的 Δ 特征：肽顶点查最近膜顶点 →
# 顶点级 (charge/hbond/hphob) - 膜对应值 - 膜均值，再按肽聚合 (mean)。
# 这样 logit = w·Δfeatures + bias 才物理可解释。
def feature_names(mp: dict) -> tuple[str, str, str]:
    cn = "charge"
    hn = "hbond"
    pn = "hphob" if "hphob" in mp else ("vertex_hphob" if "vertex_hphob" in mp else None)
    if pn is None:
        raise KeyError(f"no hphob field; have: {list(mp)}")
    for f in (cn, hn):
        if f not in mp:
            raise KeyError(f"missing field {f}; have: {list(mp)}")
    return cn, hn, pn


def peptide_feature(pep_arr, pm, mem_chq, mem_hb, mem_hp, mem_means, tree):
    cn, hn, pn = feature_names(pm)
    pxyz = pep_arr[:, [pm["x"], pm["y"], pm["z"]]]
    if pxyz.shape[0] < 3:
        return None
    pq = pep_arr[:, pm[cn]]
    phb = pep_arr[:, pm[hn]]
    php = pep_arr[:, pm[pn]]
    _, idx = tree.query(pxyz, k=1)
    dq = (pq - mem_chq[idx]) - mem_means[0]
    dh = (phb - mem_hb[idx]) - mem_means[1]
    dp = (php - mem_hp[idx]) - mem_means[2]
    return np.asarray([dq.mean(), dh.mean(), dp.mean()], dtype=float)


def score_dir(mem_pack, ply_dir: Path, weights):
    """单膜参考下的 Δ 特征评分。logit = w_charge·Δq + w_hbond·Δhb + w_hphob·Δhp + bias"""
    plys = sorted(p for p in ply_dir.glob("*.ply") if not p.name.startswith("._"))
    rows = []
    for p in plys:
        try:
            pep_arr, pm = read_ply(p)
        except Exception as e:
            print(f"  skip {p.name}: {e}", file=sys.stderr)
            continue
        try:
            f = peptide_feature(pep_arr, pm, *mem_pack)
        except Exception as e:
            print(f"  skip {p.name}: {e}", file=sys.stderr)
            continue
        if f is None or not np.all(np.isfinite(f)):
            continue
        score = float(
            weights["charge"] * f[0]
            + weights["hbond"] * f[1]
            + weights["hphob"] * f[2]
            + weights.get("bias", 0.0)
        )
        rows.append({"id": p.stem, "score": score})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mem-ply", required=True, help="单张膜参考 PLY（与训练用同一张以保证一致）")
    ap.add_argument("--recall-pos", required=True)
    ap.add_argument("--recall-neg", required=True)
    ap.add_argument("--weights-json", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--tsv", default="")
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    weights = json.loads(Path(args.weights_json).read_text())
    print(f"weights: {weights}", flush=True)

    mem_arr, mm = read_ply(Path(args.mem_ply.strip()))
    cn, hn, pn = feature_names(mm)
    mem_xyz = mem_arr[:, [mm["x"], mm["y"], mm["z"]]]
    mem_chq = mem_arr[:, mm[cn]]
    mem_hb = mem_arr[:, mm[hn]]
    mem_hp = mem_arr[:, mm[pn]]
    mem_means = np.asarray([mem_chq.mean(), mem_hb.mean(), mem_hp.mean()])
    tree = cKDTree(mem_xyz)
    mem_pack = (mem_chq, mem_hb, mem_hp, mem_means, tree)
    print(f"loaded mem ply: {args.mem_ply} ({len(mem_arr)} vertices)", flush=True)

    print("scoring positives...", flush=True)
    pos = score_dir(mem_pack, Path(args.recall_pos), weights)
    pos["label"] = 1
    print(f"  pos scored: {len(pos)}", flush=True)
    print("scoring negatives...", flush=True)
    neg = score_dir(mem_pack, Path(args.recall_neg), weights)
    neg["label"] = 0
    print(f"  neg scored: {len(neg)}", flush=True)

    df = pd.concat([pos, neg], ignore_index=True)
    df.to_csv(out / "scores.csv", index=False)

    y = df["label"].values
    s = df["score"].values
    fpr, tpr, _ = roc_curve(y, s)
    p_, r_, _ = precision_recall_curve(y, s)
    metrics = {
        "n_pos": int(len(pos)),
        "n_neg": int(len(neg)),
        "roc_auc": float(roc_auc_score(y, s)),
        "pr_auc": float(average_precision_score(y, s)),
        "mannwhitney_p": float(mannwhitneyu(pos["score"], neg["score"], alternative="greater").pvalue),
    }
    np.savez(out / "curves.npz", fpr=fpr, tpr=tpr, precision=p_, recall=r_)

    if args.tsv and Path(args.tsv).exists():
        meta = pd.read_csv(args.tsv, sep="\t")
        df2 = df.merge(meta[["sample_id", "source", "length"]], left_on="id", right_on="sample_id", how="left")
        # 分层 recall@FPR=0.1
        thr = np.quantile(neg["score"], 0.9)
        df2["pred_pos"] = df2["score"] >= thr
        by_source = (
            df2[df2["label"] == 1]
            .groupby("source")["pred_pos"].mean()
            .rename("recall_at_fpr0.1")
            .reset_index()
        )
        by_source.to_csv(out / "recall_by_source.csv", index=False)
        bins = pd.cut(df2["length"], [0, 12, 20, 30, 999])
        by_len = (
            df2[df2["label"] == 1]
            .groupby(bins)["pred_pos"].mean()
            .rename("recall_at_fpr0.1")
            .reset_index()
        )
        by_len.to_csv(out / "recall_by_length.csv", index=False)
        metrics["threshold_at_fpr0.1"] = float(thr)

    Path(out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
