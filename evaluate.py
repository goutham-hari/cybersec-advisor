"""
evaluate.py — Retrieval evaluation harness for CyberSec Advisor

Measures how well retrieval actually finds the right book/page for a set of
known questions, comparing three methods:
  - vector-only   (semantic/embedding search)
  - bm25-only     (keyword search)
  - hybrid        (RRF fusion of both — what app.py actually uses)

Metrics computed, at k = 1, 3, 6:
  - Hit Rate@k   : fraction of questions where the correct chunk appears
                   anywhere in the top-k retrieved results
  - Precision@k  : (# correct chunks in top-k) / k, averaged over questions
  - MRR          : Mean Reciprocal Rank — average of 1/rank of the first
                   correct hit (rewards ranking the right answer higher,
                   not just getting it into the top-k at all)

Usage:
    python evaluate.py
    (reads eval_set.json in the same folder; edit that file with real
    questions + known book/page answers from your own ingested library
    before running for meaningful results)

Outputs:
    eval_results.csv   — full metrics table
    eval_chart.png      — bar chart comparing the three methods
"""

import json
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reuse the exact retrieval logic already running in app.py, so this
# evaluation reflects the real system rather than a reimplementation.
from app import (
    retrieve_vector, retrieve_bm25, reciprocal_rank_fusion,
    _bm25_metas, _bm25_docs, _id_to_pos,
)

K_VALUES = [1, 3, 6]
CANDIDATES = 20  # how many candidates each method pulls before scoring


def ids_to_chunks(ids):
    chunks = []
    for cid in ids:
        pos = _id_to_pos.get(cid)
        if pos is None:
            continue
        meta = _bm25_metas[pos]
        chunks.append({"book": meta.get("book"), "page": meta.get("page")})
    return chunks


def is_match(chunk, expected_book, expected_page, tolerance):
    if chunk["book"] != expected_book:
        return False
    try:
        return abs(int(chunk["page"]) - int(expected_page)) <= tolerance
    except (TypeError, ValueError):
        return False


def rank_of_first_hit(chunks, expected_book, expected_page, tolerance):
    for i, c in enumerate(chunks):
        if is_match(c, expected_book, expected_page, tolerance):
            return i + 1  # 1-indexed rank
    return None


def evaluate_method(name, get_ranked_ids_fn, eval_set):
    """
    get_ranked_ids_fn(question) -> ranked list of chunk ids (best first)
    Returns a dict of metrics plus per-query detail for this method.
    """
    per_query = []
    for item in eval_set:
        ranked_ids = get_ranked_ids_fn(item["question"])
        chunks = ids_to_chunks(ranked_ids)
        rank = rank_of_first_hit(
            chunks, item["expected_book"], item["expected_page"],
            item.get("page_tolerance", 1)
        )
        per_query.append({"question": item["question"], "rank": rank, "chunks": chunks})

    metrics = {"method": name}
    n = len(eval_set)

    # MRR
    reciprocal_ranks = [1.0 / r["rank"] if r["rank"] else 0.0 for r in per_query]
    metrics["MRR"] = sum(reciprocal_ranks) / n if n else 0.0

    # Hit Rate@k and Precision@k
    for k in K_VALUES:
        hits = sum(1 for r in per_query if r["rank"] and r["rank"] <= k)
        metrics[f"HitRate@{k}"] = hits / n if n else 0.0
        # Precision@k for a single-relevant-chunk task: 1/k if hit within top-k, else 0
        precisions = [(1.0 / k) if (r["rank"] and r["rank"] <= k) else 0.0 for r in per_query]
        metrics[f"Precision@{k}"] = sum(precisions) / n if n else 0.0

    return metrics, per_query


def main():
    with open("eval_set.json") as f:
        eval_set = json.load(f)

    if any("REPLACE" in item.get("notes", "") for item in eval_set):
        print("=" * 70)
        print("WARNING: eval_set.json still contains placeholder/template")
        print("questions. Edit it with real questions and known book/page")
        print("answers from your own ingested library before trusting these")
        print("numbers. Running anyway on the template data for demonstration.")
        print("=" * 70)
        print()

    methods = {
        "Vector-only": lambda q: retrieve_vector(q, CANDIDATES),
        "BM25-only": lambda q: retrieve_bm25(q, CANDIDATES),
        "Hybrid (RRF)": lambda q: reciprocal_rank_fusion(
            [retrieve_vector(q, CANDIDATES), retrieve_bm25(q, CANDIDATES)]
        ),
    }

    all_metrics = []
    all_detail = {}
    for name, fn in methods.items():
        metrics, detail = evaluate_method(name, fn, eval_set)
        all_metrics.append(metrics)
        all_detail[name] = detail
        print(f"\n--- {name} ---")
        for k, v in metrics.items():
            if k != "method":
                print(f"  {k}: {v:.3f}")

    # ---- CSV output ----
    fieldnames = ["method", "MRR"] + [f"HitRate@{k}" for k in K_VALUES] + [f"Precision@{k}" for k in K_VALUES]
    with open("eval_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in all_metrics:
            writer.writerow(m)
    print(f"\nSaved metrics table to eval_results.csv")

    # ---- Chart output ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Chart 1: Hit Rate@k for each method
    ax = axes[0]
    width = 0.25
    x = range(len(K_VALUES))
    colors = ["#8CA0AF", "#3DDC97", "#1F5B45"]
    for i, m in enumerate(all_metrics):
        vals = [m[f"HitRate@{k}"] for k in K_VALUES]
        ax.bar([xi + i * width for xi in x], vals, width=width, label=m["method"], color=colors[i % len(colors)])
    ax.set_xticks([xi + width for xi in x])
    ax.set_xticklabels([f"k={k}" for k in K_VALUES])
    ax.set_ylabel("Hit Rate")
    ax.set_title("Hit Rate@k by Retrieval Method")
    ax.set_ylim(0, 1.05)
    ax.legend()

    # Chart 2: MRR comparison
    ax2 = axes[1]
    names = [m["method"] for m in all_metrics]
    mrrs = [m["MRR"] for m in all_metrics]
    ax2.bar(names, mrrs, color=colors[:len(names)])
    ax2.set_ylabel("Mean Reciprocal Rank")
    ax2.set_title("MRR by Retrieval Method")
    ax2.set_ylim(0, 1.05)
    plt.setp(ax2.get_xticklabels(), rotation=15, ha="right")

    plt.tight_layout()
    plt.savefig("eval_chart.png", dpi=150)
    print("Saved comparison chart to eval_chart.png")


if __name__ == "__main__":
    main()
