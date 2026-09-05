#!/usr/bin/env python3
"""
Paired-Results Evaluator Helper for Aegntic Outcome Plugins.

Consumes independently graded paired evaluation runs (Baseline vs. Candidate)
and evaluates:
  1. Scheduled task coverage
  2. Evidence presence
  3. Numeric validity
  4. Resource ceilings (latency, tokens, cost)
  5. Paired success gain
  6. Exact one-sided sign-test probability: P(X >= k) = sum(comb(n, i) * 0.5^n for i in range(k, n+1))
  7. Hard-boundary critical failure isolation

Standardized across all five outcome plugins.
"""

import sys
import json
import math
import argparse
from typing import Dict, Any, List, Tuple, Optional

def compute_exact_sign_test(differences: List[float]) -> Tuple[int, int, float]:
    """
    Computes one-sided exact sign test p-value for positive gains.
    Differences are (candidate - baseline).
    Ties (diff == 0) are excluded under standard sign-test procedure.
    """
    non_zero = [d for d in differences if abs(d) > 1e-9]
    n = len(non_zero)
    if n == 0:
        return 0, 0, 1.0
    
    k = sum(1 for d in non_zero if d > 0)
    # One-sided exact binomial tail probability where null p = 0.5
    p_value = sum(math.comb(n, i) * (0.5 ** n) for i in range(k, n + 1))
    return k, n, p_value

def evaluate_paired_runs(
    baseline_tasks: List[Dict[str, Any]],
    candidate_tasks: List[Dict[str, Any]],
    contract: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    contract = contract or {}
    required_tasks = set(contract.get("required_tasks", []))
    max_latency_ms = contract.get("max_latency_ms", float("inf"))
    max_tokens = contract.get("max_tokens", float("inf"))
    practical_threshold = contract.get("practical_threshold", 0.05)

    base_map = {t["id"]: t for t in baseline_tasks if "id" in t}
    cand_map = {t["id"]: t for t in candidate_tasks if "id" in t}

    all_task_ids = sorted(list(set(base_map.keys()) | set(cand_map.keys())))
    if required_tasks:
        missing_tasks = required_tasks - set(all_task_ids)
        if missing_tasks:
            return {
                "status": "INVALID",
                "error": f"Missing required scheduled tasks: {sorted(list(missing_tasks))}",
                "coverage_rate": len(all_task_ids) / len(required_tasks) if required_tasks else 1.0,
            }

    differences = []
    pairs_evaluated = 0
    candidate_wins = 0
    baseline_wins = 0
    ties = 0
    critical_failures = []
    evidence_missing_count = 0
    resource_violations = 0

    task_summaries = []

    for tid in all_task_ids:
        b_task = base_map.get(tid)
        c_task = cand_map.get(tid)

        if not b_task or not c_task:
            return {
                "status": "INVALID",
                "error": f"Task {tid} is not present in both baseline and candidate sets.",
            }

        # Validate numeric score
        b_score = b_task.get("score")
        c_score = c_task.get("score")

        if not isinstance(b_score, (int, float)) or not isinstance(c_score, (int, float)):
            return {
                "status": "INVALID",
                "error": f"Task {tid} has non-numeric score (baseline: {b_score}, candidate: {c_score})",
            }

        # Evidence validation: require non-empty evidence string or list
        c_evidence = c_task.get("evidence")
        if not c_evidence or (isinstance(c_evidence, (list, dict, str)) and len(c_evidence) == 0):
            evidence_missing_count += 1
            # If candidate claims success without evidence, reject that task outcome
            if c_score > 0:
                c_score = 0.0

        # Resource ceiling check on candidate
        c_latency = c_task.get("latency_ms", 0)
        c_tokens = c_task.get("tokens", 0)
        if c_latency > max_latency_ms or c_tokens > max_tokens:
            resource_violations += 1
            c_score = 0.0

        # Check critical failure flag
        if c_task.get("critical_failure", False):
            critical_failures.append({
                "task_id": tid,
                "reason": c_task.get("failure_reason", "Unspecified critical failure")
            })

        diff = float(c_score - b_score)
        differences.append(diff)
        pairs_evaluated += 1

        if diff > 1e-9:
            candidate_wins += 1
        elif diff < -1e-9:
            baseline_wins += 1
        else:
            ties += 1

        task_summaries.append({
            "id": tid,
            "baseline_score": b_score,
            "candidate_score": c_score,
            "diff": diff,
            "evidence_provided": bool(c_evidence),
            "resource_valid": (c_latency <= max_latency_ms and c_tokens <= max_tokens),
        })

    k, n_effective, p_value = compute_exact_sign_test(differences)
    mean_baseline = sum(t["baseline_score"] for t in task_summaries) / max(1, pairs_evaluated)
    mean_candidate = sum(t["candidate_score"] for t in task_summaries) / max(1, pairs_evaluated)
    mean_gain = mean_candidate - mean_baseline

    has_practical_gain = mean_gain >= practical_threshold
    is_statistically_significant = p_value < 0.05
    verdict = "REJECT"

    if critical_failures:
        verdict = "REJECT_CRITICAL_FAILURE"
    elif has_practical_gain and is_statistically_significant:
        verdict = "PROMOTE"
    elif has_practical_gain and not is_statistically_significant:
        verdict = "INCONCLUSIVE_INSUFFICIENT_TRIALS"
    else:
        verdict = "REJECT_NO_GAIN"

    return {
        "status": "VALID",
        "verdict": verdict,
        "pairs_evaluated": pairs_evaluated,
        "candidate_wins": candidate_wins,
        "baseline_wins": baseline_wins,
        "ties": ties,
        "mean_baseline_score": round(mean_baseline, 4),
        "mean_candidate_score": round(mean_candidate, 4),
        "practical_gain": round(mean_gain, 4),
        "practical_threshold": practical_threshold,
        "sign_test": {
            "effective_pairs": n_effective,
            "candidate_favorable_pairs": k,
            "one_sided_p_value": round(p_value, 5),
            "alpha_0_05": is_statistically_significant,
        },
        "evidence_missing_count": evidence_missing_count,
        "resource_ceiling_violations": resource_violations,
        "critical_failures": critical_failures,
        "task_details": task_summaries,
    }

def main():
    parser = argparse.ArgumentParser(description="Paired-results evaluator helper for outcome plugins.")
    parser.add_argument("--baseline", required=True, help="Path to baseline runs JSON")
    parser.add_argument("--candidate", required=True, help="Path to candidate runs JSON")
    parser.add_argument("--contract", required=False, help="Path to evaluation contract JSON")
    parser.add_argument("--output", required=False, help="Path to write evaluation output JSON")
    args = parser.parse_args()

    try:
        with open(args.baseline, "r", encoding="utf-8") as f:
            base_data = json.load(f)
        with open(args.candidate, "r", encoding="utf-8") as f:
            cand_data = json.load(f)
        
        contract_data = {}
        if args.contract:
            with open(args.contract, "r", encoding="utf-8") as f:
                contract_data = json.load(f)

        base_tasks = base_data if isinstance(base_data, list) else base_data.get("tasks", [])
        cand_tasks = cand_data if isinstance(cand_data, list) else cand_data.get("tasks", [])

        report = evaluate_paired_runs(base_tasks, cand_tasks, contract_data)

        output_json = json.dumps(report, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
        print(output_json)

        if report.get("status") != "VALID":
            sys.exit(1)
        sys.exit(0)

    except Exception as e:
        err = {"status": "ERROR", "error": str(e)}
        print(json.dumps(err, indent=2), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
