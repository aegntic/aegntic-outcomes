#!/usr/bin/env python3
"""
12 Unit and CLI test cases for the paired-results evaluator helper.
Validates all edge cases including false-pass scenarios, missing evidence,
critical failure isolation, ties, and sign test math.
"""

import unittest
import math
import subprocess
import json
import tempfile
import os
import sys

# Ensure local evaluator module is found
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from evaluator import compute_exact_sign_test, evaluate_paired_runs

class TestEvaluator(unittest.TestCase):

    def test_01_perfect_superiority(self):
        """Candidate wins 10 out of 10 tasks with practical gain."""
        base = [{"id": f"t_{i}", "score": 0.5, "evidence": "log"} for i in range(10)]
        cand = [{"id": f"t_{i}", "score": 1.0, "evidence": "trace_artifact"} for i in range(10)]
        res = evaluate_paired_runs(base, cand, {"practical_threshold": 0.1})
        self.assertEqual(res["status"], "VALID")
        self.assertEqual(res["verdict"], "PROMOTE")
        self.assertEqual(res["candidate_wins"], 10)
        self.assertAlmostEqual(res["practical_gain"], 0.5)
        # For 10 out of 10, p = 0.5^10 = 1/1024 ~ 0.000977
        self.assertLess(res["sign_test"]["one_sided_p_value"], 0.001)

    def test_02_null_hypothesis_ties(self):
        """All tasks identical -> 0 gain and null sign test."""
        base = [{"id": f"t_{i}", "score": 0.8, "evidence": "log"} for i in range(10)]
        cand = [{"id": f"t_{i}", "score": 0.8, "evidence": "log"} for i in range(10)]
        res = evaluate_paired_runs(base, cand)
        self.assertEqual(res["status"], "VALID")
        self.assertEqual(res["verdict"], "REJECT_NO_GAIN")
        self.assertEqual(res["ties"], 10)
        self.assertEqual(res["sign_test"]["effective_pairs"], 0)
        self.assertEqual(res["sign_test"]["one_sided_p_value"], 1.0)

    def test_03_candidate_degradation(self):
        """Candidate performs worse than baseline."""
        base = [{"id": f"t_{i}", "score": 0.9, "evidence": "log"} for i in range(5)]
        cand = [{"id": f"t_{i}", "score": 0.2, "evidence": "log"} for i in range(5)]
        res = evaluate_paired_runs(base, cand)
        self.assertEqual(res["verdict"], "REJECT_NO_GAIN")
        self.assertLess(res["practical_gain"], 0)
        self.assertEqual(res["baseline_wins"], 5)

    def test_04_resource_ceiling_violation(self):
        """Candidate exceeds latency budget -> task score penalized to 0.0."""
        base = [{"id": "t_1", "score": 0.5, "evidence": "log"}]
        cand = [{"id": "t_1", "score": 1.0, "evidence": "trace", "latency_ms": 1500}]
        res = evaluate_paired_runs(base, cand, {"max_latency_ms": 1000})
        self.assertEqual(res["resource_ceiling_violations"], 1)
        # Score penalized to 0.0, so candidate loses (0.0 vs 0.5)
        self.assertEqual(res["baseline_wins"], 1)
        self.assertEqual(res["verdict"], "REJECT_NO_GAIN")

    def test_05_missing_evidence_rejected(self):
        """Candidate claims 1.0 but provides empty evidence -> penalized to 0.0."""
        base = [{"id": "t_1", "score": 0.6, "evidence": "valid_ref"}]
        cand = [{"id": "t_1", "score": 1.0, "evidence": ""}]
        res = evaluate_paired_runs(base, cand)
        self.assertEqual(res["evidence_missing_count"], 1)
        self.assertEqual(res["task_details"][0]["candidate_score"], 0.0)

    def test_06_critical_failure_isolation(self):
        """Even with high average gain, a critical safety failure forces REJECT_CRITICAL_FAILURE."""
        base = [{"id": f"t_{i}", "score": 0.1, "evidence": "ok"} for i in range(10)]
        cand = [{"id": f"t_{i}", "score": 1.0, "evidence": "ok"} for i in range(10)]
        cand[0]["critical_failure"] = True
        cand[0]["failure_reason"] = "Data exfiltration detected"
        res = evaluate_paired_runs(base, cand)
        self.assertEqual(res["verdict"], "REJECT_CRITICAL_FAILURE")
        self.assertEqual(len(res["critical_failures"]), 1)

    def test_07_false_pass_prevention(self):
        """Empty outputs or fake task IDs not matching baseline cause INVALID status."""
        base = [{"id": "t_1", "score": 0.5, "evidence": "ok"}]
        cand = [{"id": "t_999", "score": 1.0, "evidence": "ok"}]
        res = evaluate_paired_runs(base, cand)
        self.assertEqual(res["status"], "INVALID")
        self.assertIn("not present in both", res["error"])

    def test_08_incomplete_task_coverage(self):
        """Fails contract if required tasks list is not satisfied."""
        base = [{"id": "t_1", "score": 0.5, "evidence": "ok"}]
        cand = [{"id": "t_1", "score": 0.9, "evidence": "ok"}]
        res = evaluate_paired_runs(base, cand, {"required_tasks": ["t_1", "t_2_mandatory"]})
        self.assertEqual(res["status"], "INVALID")
        self.assertIn("Missing required scheduled tasks", res["error"])

    def test_09_non_numeric_score_handling(self):
        """Malformed score string triggers INVALID error."""
        base = [{"id": "t_1", "score": "PASS", "evidence": "ok"}]
        cand = [{"id": "t_1", "score": 1.0, "evidence": "ok"}]
        res = evaluate_paired_runs(base, cand)
        self.assertEqual(res["status"], "INVALID")
        self.assertIn("non-numeric score", res["error"])

    def test_10_sign_test_boundary_conditions(self):
        """Verify exact binomial formula for known n and k."""
        # 6 positive out of 8 non-zero trials:
        # sum(comb(8, i) * 0.5^8 for i in [6, 7, 8]) = (28 + 8 + 1)/256 = 37/256 = 0.14453125
        k, n, p = compute_exact_sign_test([1, 1, 1, 1, 1, 1, -1, -1])
        self.assertEqual(k, 6)
        self.assertEqual(n, 8)
        self.assertAlmostEqual(p, 37 / 256, places=5)

    def test_11_insufficient_trials_inconclusive(self):
        """Gain exists but small N means p-value >= 0.05 -> INCONCLUSIVE_INSUFFICIENT_TRIALS."""
        base = [{"id": f"t_{i}", "score": 0.3, "evidence": "ok"} for i in range(3)]
        cand = [{"id": f"t_{i}", "score": 0.8, "evidence": "ok"} for i in range(3)]
        res = evaluate_paired_runs(base, cand, {"practical_threshold": 0.1})
        self.assertEqual(res["verdict"], "INCONCLUSIVE_INSUFFICIENT_TRIALS")
        self.assertGreaterEqual(res["sign_test"]["one_sided_p_value"], 0.05)

    def test_12_cli_execution_and_exit_code(self):
        """Run evaluator via command line interface and verify JSON output & exit code."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f_base, \
             tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f_cand:
            json.dump([{"id": "t_1", "score": 0.2, "evidence": "ok"}], f_base)
            json.dump([{"id": "t_1", "score": 0.9, "evidence": "ok"}], f_cand)
            b_path, c_path = f_base.name, f_cand.name
            f_base.flush()
            f_cand.flush()

        eval_script = os.path.join(current_dir, "evaluator.py")
        try:
            proc = subprocess.run(
                ["python3", eval_script, "--baseline", b_path, "--candidate", c_path],
                capture_output=True,
                text=True
            )
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data["status"], "VALID")
            self.assertEqual(data["pairs_evaluated"], 1)
        finally:
            os.remove(b_path)
            os.remove(c_path)

if __name__ == "__main__":
    unittest.main()
