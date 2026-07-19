#!/usr/bin/env python3
"""
HECTOR RAGAS Evaluation Script

Evaluates HECTOR's retrieval quality using RAGAS metrics:
- Faithfulness: How grounded is the answer in retrieved context?
- Answer Relevance: Does the answer address the query?
- Context Precision: Are the retrieved contexts relevant?
- Context Recall: Does the context contain the ground truth?

Usage:
    python evaluation/evaluate_rag.py --dataset-paths evaluation --host localhost --port 8000
    python evaluation/evaluate_rag.py --dataset-paths evaluation --host localhost --port 8000 --api-key YOUR_KEY
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
DEFAULT_TOP_K = 10
DEFAULT_MAX_TOKENS = 1024
TIMEOUT_SECONDS = 60

REQUIRED_FIELDS = {"query", "ground_truth"}
OPTIONAL_FIELDS = {"expected_sections", "expected_acts", "category"}


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


def load_dataset(dataset_path: str) -> list[dict[str, Any]]:
    """Load train.json from the given dataset directory."""
    train_path = Path(dataset_path) / "train.json"
    if not train_path.exists():
        raise FileNotFoundError(f"train.json not found in {dataset_path}")

    with open(train_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("train.json must be a JSON array")

    for i, item in enumerate(data):
        missing = REQUIRED_FIELDS - set(item.keys())
        if missing:
            raise ValueError(f"Item {i} missing required fields: {missing}")

    return data


# ---------------------------------------------------------------------------
# HECTOR API client
# ---------------------------------------------------------------------------


def query_hector(
    query: str,
    host: str,
    port: int,
    api_key: str | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """Send a search query to HECTOR API and return the full response."""
    url = f"http://{host}:{port}/v1/search"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "query": query,
        "top_k": top_k,
        "response_format": "detailed",
    }

    try:
        resp = requests.post(
            url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to HECTOR at {host}:{port}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError:
        print(
            f"ERROR: HECTOR returned {resp.status_code}: {resp.text[:200]}",
            file=sys.stderr,
        )
        sys.exit(1)


def extract_contexts(response: dict[str, Any]) -> list[str]:
    """Extract retrieved document texts from HECTOR response."""
    items = response.get("items", [])
    return [item.get("document", "") for item in items if item.get("document")]


def extract_answer(response: dict[str, Any]) -> str:
    """Extract the generated answer from HECTOR response."""
    return response.get("generated_response", "")


# ---------------------------------------------------------------------------
# RAGAS evaluation (simplified local implementation)
# ---------------------------------------------------------------------------


def compute_ragas_metrics(
    query: str,
    answer: str,
    contexts: list[str],
    ground_truth: str,
) -> dict[str, float]:
    """
    Compute simplified RAGAS-inspired metrics.

    For production use, integrate the full RAGAS library with an LLM judge.
    This simplified version uses heuristic scoring for fast iteration.

    Metrics:
    - context_precision: fraction of retrieved contexts that contain
      any substring from the ground truth
    - context_recall: fraction of ground truth sentences found in contexts
    - answer_relevance: overlap between answer and ground truth keywords
    - faithfulness: overlap between answer and retrieved contexts
    """
    metrics = {}

    # --- Context Precision ---
    if contexts:
        gt_substrings = _split_into_sentences(ground_truth)
        relevant_count = 0
        for ctx in contexts:
            ctx_lower = ctx.lower()
            if any(sub.lower() in ctx_lower for sub in gt_substrings if len(sub) > 10):
                relevant_count += 1
        metrics["context_precision"] = (
            relevant_count / len(contexts) if contexts else 0.0
        )
    else:
        metrics["context_precision"] = 0.0

    # --- Context Recall ---
    gt_sentences = _split_into_sentences(ground_truth)
    if gt_sentences:
        all_context = " ".join(contexts).lower()
        found = sum(1 for s in gt_sentences if s.lower() in all_context and len(s) > 10)
        metrics["context_recall"] = found / len(gt_sentences)
    else:
        metrics["context_recall"] = 0.0

    # --- Answer Relevance ---
    if answer and ground_truth:
        gt_keywords = set(_extract_keywords(ground_truth))
        answer_keywords = set(_extract_keywords(answer))
        if gt_keywords:
            metrics["answer_relevance"] = len(gt_keywords & answer_keywords) / len(
                gt_keywords
            )
        else:
            metrics["answer_relevance"] = 0.0
    else:
        metrics["answer_relevance"] = 0.0

    # --- Faithfulness ---
    if answer and contexts:
        answer_keywords = set(_extract_keywords(answer))
        context_text = " ".join(contexts).lower()
        if answer_keywords:
            grounded = sum(1 for kw in answer_keywords if kw.lower() in context_text)
            metrics["faithfulness"] = grounded / len(answer_keywords)
        else:
            metrics["faithfulness"] = 0.0
    else:
        metrics["faithfulness"] = 0.0

    return metrics


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentence-like chunks."""
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text."""
    import re

    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "and",
        "but",
        "or",
        "if",
        "while",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "it",
        "its",
        "they",
        "them",
        "their",
        "about",
        "up",
        "also",
        "shall",
        "under",
        "section",
        "ipc",
        "bns",
        "crpc",
        "bnss",
        "bsa",
        "act",
        "code",
        "law",
        "case",
    }
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return [w for w in words if w not in stopwords and len(w) > 2]


# ---------------------------------------------------------------------------
# Citation quality metrics
# ---------------------------------------------------------------------------


def compute_citation_metrics(
    response: dict[str, Any],
    expected_sections: list[str],
    expected_acts: list[str],
) -> dict[str, float]:
    """Compute citation quality metrics."""
    citations = response.get("citations", [])
    items = response.get("items", [])

    metrics = {}

    # Citation count
    metrics["citation_count"] = len(citations)

    # Expected section recall
    if expected_sections:
        cited_sections = set()
        for c in citations:
            if c.get("section"):
                cited_sections.add(c["section"].strip())
        for item in items:
            meta = item.get("metadata", {})
            if meta.get("section_number"):
                cited_sections.add(meta["section_number"].strip())

        found = sum(1 for s in expected_sections if s in cited_sections)
        metrics["section_recall"] = found / len(expected_sections)
    else:
        metrics["section_recall"] = 1.0

    # Expected act recall
    if expected_acts:
        cited_acts = set()
        for c in citations:
            if c.get("act"):
                cited_acts.add(c["act"].strip().upper())
        for item in items:
            act = item.get("act") or item.get("metadata", {}).get("act_name", "")
            if act:
                cited_acts.add(act.strip().upper())

        found = sum(1 for a in expected_acts if a.upper() in cited_acts)
        metrics["act_recall"] = found / len(expected_acts)
    else:
        metrics["act_recall"] = 1.0

    return metrics


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------


def run_evaluation(
    dataset_path: str,
    host: str,
    port: int,
    api_key: str | None = None,
    top_k: int = DEFAULT_TOP_K,
    output_dir: str = "results",
) -> dict[str, Any]:
    """Run full evaluation and return summary."""
    dataset_name = Path(dataset_path).name
    print(f"\n{'=' * 60}")
    print(f"  HECTOR RAGAS Evaluation — {dataset_name}")
    print(f"{'=' * 60}")
    print(f"  API:      http://{host}:{port}")
    print(f"  Top-K:    {top_k}")
    print(f"  Dataset:  {dataset_path}")

    data = load_dataset(dataset_path)
    print(f"  Queries:  {len(data)}")
    print(f"{'=' * 60}\n")

    all_metrics = []
    errors = []

    for i, item in enumerate(data):
        query = item["query"]
        ground_truth = item["ground_truth"]
        expected_sections = item.get("expected_sections", [])
        expected_acts = item.get("expected_acts", [])
        category = item.get("category", "unknown")

        print(f"[{i + 1}/{len(data)}] {query[:80]}...")

        try:
            t0 = time.time()
            response = query_hector(query, host, port, api_key, top_k)
            latency_ms = (time.time() - t0) * 1000

            answer = extract_answer(response)
            contexts = extract_contexts(response)

            ragas = compute_ragas_metrics(query, answer, contexts, ground_truth)
            citation = compute_citation_metrics(
                response, expected_sections, expected_acts
            )

            result = {
                "query": query,
                "category": category,
                "latency_ms": round(latency_ms, 1),
                "num_contexts": len(contexts),
                "answer_length": len(answer),
                **ragas,
                **citation,
            }
            all_metrics.append(result)

            print(
                f"  -> Faithfulness: {ragas['faithfulness']:.2f} | "
                f"Relevance: {ragas['answer_relevance']:.2f} | "
                f"Context Recall: {ragas['context_recall']:.2f} | "
                f"Section Recall: {citation['section_recall']:.2f} | "
                f"Latency: {latency_ms:.0f}ms"
            )

        except Exception as e:
            errors.append({"query": query, "error": str(e)})
            print(f"  -> ERROR: {e}")

    # Compute summary
    summary = _compute_summary(all_metrics, dataset_name)
    summary["errors"] = errors

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  EVALUATION SUMMARY — {dataset_name}")
    print(f"{'=' * 60}")
    print(f"  Queries evaluated:  {len(all_metrics)}")
    print(f"  Errors:             {len(errors)}")
    print("")
    print("  RAGAS Metrics:")
    print(f"    Faithfulness:     {summary['faithfulness']:.3f}")
    print(f"    Answer Relevance: {summary['answer_relevance']:.3f}")
    print(f"    Context Precision:{summary['context_precision']:.3f}")
    print(f"    Context Recall:   {summary['context_recall']:.3f}")
    print("")
    print("  Citation Metrics:")
    print(f"    Section Recall:   {summary['section_recall']:.3f}")
    print(f"    Act Recall:       {summary['act_recall']:.3f}")
    print(f"    Avg Citations:    {summary['avg_citation_count']:.1f}")
    print("")
    print("  Performance:")
    print(f"    Avg Latency:      {summary['avg_latency_ms']:.0f}ms")
    print(f"    P95 Latency:      {summary['p95_latency_ms']:.0f}ms")
    print(f"{'=' * 60}\n")

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    results_path = Path(output_dir) / f"rag_{dataset_name}_evaluation_summary.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {results_path}")

    # Save per-query details
    details_path = Path(output_dir) / f"rag_{dataset_name}_evaluation_details.json"
    with open(details_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    print(f"Details saved to: {details_path}")

    return summary


def _compute_summary(metrics: list[dict], dataset_name: str) -> dict[str, Any]:
    """Compute aggregate summary from per-query metrics."""
    if not metrics:
        return {"error": "no metrics collected"}

    n = len(metrics)
    latencies = [m["latency_ms"] for m in metrics]
    latencies_sorted = sorted(latencies)

    summary = {
        "dataset": dataset_name,
        "total_queries": n,
        "faithfulness": sum(m["faithfulness"] for m in metrics) / n,
        "answer_relevance": sum(m["answer_relevance"] for m in metrics) / n,
        "context_precision": sum(m["context_precision"] for m in metrics) / n,
        "context_recall": sum(m["context_recall"] for m in metrics) / n,
        "section_recall": sum(m["section_recall"] for m in metrics) / n,
        "act_recall": sum(m["act_recall"] for m in metrics) / n,
        "avg_citation_count": sum(m["citation_count"] for m in metrics) / n,
        "avg_latency_ms": sum(latencies) / n,
        "p95_latency_ms": latencies_sorted[int(n * 0.95)]
        if n >= 20
        else latencies_sorted[-1],
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
    }

    # Per-category breakdown
    categories = {}
    for m in metrics:
        cat = m.get("category", "unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(m)

    summary["by_category"] = {}
    for cat, cat_metrics in categories.items():
        cn = len(cat_metrics)
        summary["by_category"][cat] = {
            "count": cn,
            "faithfulness": sum(m["faithfulness"] for m in cat_metrics) / cn,
            "answer_relevance": sum(m["answer_relevance"] for m in cat_metrics) / cn,
            "context_recall": sum(m["context_recall"] for m in cat_metrics) / cn,
        }

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="HECTOR RAGAS Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation
  python evaluation/evaluate_rag.py --dataset-paths evaluation --host localhost --port 8000

  # With API key
  python evaluation/evaluate_rag.py --dataset-paths evaluation --host localhost --port 8000 --api-key $HECTOR_API_KEY

  # Custom top-k
  python evaluation/evaluate_rag.py --dataset-paths evaluation --host localhost --port 8000 --top-k 20
        """,
    )
    parser.add_argument(
        "--dataset-paths",
        required=True,
        help="Path(s) to dataset directories containing train.json",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HECTOR_API_HOST", DEFAULT_HOST),
        help=f"HECTOR API host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("HECTOR_API_PORT", DEFAULT_PORT)),
        help=f"HECTOR API port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("HECTOR_API_KEY"),
        help="HECTOR API key (or set HECTOR_API_KEY env var)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Number of results to retrieve (default: {DEFAULT_TOP_K})",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save evaluation results (default: results)",
    )

    args = parser.parse_args()

    summary = run_evaluation(
        dataset_path=args.dataset_paths,
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        top_k=args.top_k,
        output_dir=args.output_dir,
    )

    # Exit with non-zero if any metric is critically low
    if summary.get("faithfulness", 0) < 0.3:
        print(
            "WARNING: Faithfulness below 30% — retrieval quality is poor",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
