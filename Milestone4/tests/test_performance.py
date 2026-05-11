"""
=============================================================================
MODULE 4 — Performance / Load Tests (Track C: Web Simulator)
Measures response time under concurrent load.
Targets:
  - Average response time < 200ms
  - P95 response time < 500ms
  - Error rate = 0% under expected load
  - Throughput: measures req/s
=============================================================================
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../Milestone2"))

import time
import threading
import statistics
import pytest
from fastapi.testclient import TestClient
from backend import app

client = TestClient(app)

IVR_URL = "http://localhost:8000"   # used for reference; TestClient bypasses HTTP


# ── helpers ───────────────────────────────────────────────────────────────────

def timed_request(fn, results: list, errors: list):
    """Run fn(), record elapsed ms into results; record any exception into errors."""
    try:
        t0 = time.perf_counter()
        fn()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        results.append(elapsed_ms)
    except Exception as e:
        errors.append(str(e))


def load_test(fn, n_requests: int, n_threads: int = 10):
    """
    Run fn() n_requests times across n_threads threads.
    Returns (results_ms, errors, duration_s).
    """
    results, errors = [], []
    threads = []
    t_start = time.perf_counter()

    for _ in range(n_requests):
        t = threading.Thread(target=timed_request, args=(fn, results, errors))
        threads.append(t)

    # Start in batches of n_threads to simulate concurrency
    for i in range(0, len(threads), n_threads):
        batch = threads[i:i + n_threads]
        for t in batch:
            t.start()
        for t in batch:
            t.join()

    total_duration = time.perf_counter() - t_start
    return results, errors, total_duration


def percentile(data: list, p: float) -> float:
    """Return the p-th percentile of data."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def print_report(label: str, results: list, errors: list, duration: float):
    if not results:
        print(f"\n[{label}] No results — {len(errors)} errors")
        return
    avg = statistics.mean(results)
    p95 = percentile(results, 95)
    p99 = percentile(results, 99)
    rps = len(results) / duration if duration > 0 else 0
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Requests : {len(results)} ok / {len(errors)} errors")
    print(f"  Avg      : {avg:.1f} ms")
    print(f"  P95      : {p95:.1f} ms")
    print(f"  P99      : {p99:.1f} ms")
    print(f"  Min/Max  : {min(results):.1f} / {max(results):.1f} ms")
    print(f"  Throughput: {rps:.1f} req/s")
    print(f"{'='*60}")


# ── P1  Health endpoint load ──────────────────────────────────────────────────

class TestHealthPerformance:
    def test_health_50_requests_under_500ms_p95(self):
        def req():
            r = client.get("/health")
            assert r.status_code == 200

        results, errors, duration = load_test(req, n_requests=50, n_threads=10)
        print_report("GET /health — 50 requests", results, errors, duration)

        assert len(errors) == 0, f"Errors: {errors}"
        p95 = percentile(results, 95)
        assert p95 < 500, f"P95 {p95:.1f}ms exceeds 500ms threshold"

    def test_health_average_under_200ms(self):
        def req():
            client.get("/health")

        results, errors, duration = load_test(req, n_requests=30, n_threads=5)
        avg = statistics.mean(results) if results else 9999
        assert avg < 200, f"Average {avg:.1f}ms exceeds 200ms threshold"


# ── P2  /ivr/start load ───────────────────────────────────────────────────────

class TestIVRStartPerformance:
    def test_start_50_concurrent_sessions(self):
        """50 concurrent session creations must all succeed under 500ms P95."""
        counter = [0]
        lock = threading.Lock()

        def req():
            with lock:
                counter[0] += 1
                cid = f"+91900{counter[0]:07d}"
            r = client.post("/ivr/start", json={"caller_id": cid})
            assert r.status_code == 200

        results, errors, duration = load_test(req, n_requests=50, n_threads=10)
        print_report("POST /ivr/start — 50 concurrent", results, errors, duration)

        assert len(errors) == 0
        p95 = percentile(results, 95)
        assert p95 < 500

    def test_start_error_rate_zero(self):
        counter = [0]
        lock = threading.Lock()

        def req():
            with lock:
                counter[0] += 1
                cid = f"+91800{counter[0]:07d}"
            r = client.post("/ivr/start", json={"caller_id": cid})
            assert r.status_code == 200

        results, errors, _ = load_test(req, n_requests=20, n_threads=5)
        assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}: {errors}"


# ── P3  /ivr/input load ───────────────────────────────────────────────────────

class TestDTMFPerformance:
    def _make_sessions(self, n: int):
        sids = []
        for i in range(n):
            r = client.post("/ivr/start", json={"caller_id": f"+91700{i:07d}"})
            sids.append(r.json()["data"]["session_id"])
        return sids

    def test_dtmf_input_50_requests_p95(self):
        sids = self._make_sessions(50)
        idx = [0]
        lock = threading.Lock()

        def req():
            with lock:
                sid = sids[idx[0] % len(sids)]
                idx[0] += 1
            r = client.post("/ivr/input", json={
                "session_id": sid, "digit": "1", "current_flow": "main_menu"
            })
            assert r.status_code == 200

        results, errors, duration = load_test(req, n_requests=50, n_threads=10)
        print_report("POST /ivr/input — 50 requests", results, errors, duration)

        assert len(errors) == 0
        p95 = percentile(results, 95)
        assert p95 < 500


# ── P4  /ivr/pnr load ────────────────────────────────────────────────────────

class TestPNRPerformance:
    def test_pnr_check_50_requests(self):
        sids = []
        for i in range(50):
            r = client.post("/ivr/start", json={"caller_id": f"+91600{i:07d}"})
            sids.append(r.json()["data"]["session_id"])

        idx = [0]
        lock = threading.Lock()

        def req():
            with lock:
                sid = sids[idx[0] % len(sids)]
                idx[0] += 1
            r = client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "4521679834"})
            assert r.status_code == 200

        results, errors, duration = load_test(req, n_requests=50, n_threads=10)
        print_report("POST /ivr/pnr — 50 requests", results, errors, duration)

        assert len(errors) == 0
        p95 = percentile(results, 95)
        assert p95 < 500


# ── P5  Mixed endpoint stress test ───────────────────────────────────────────

class TestMixedLoadStress:
    def test_mixed_endpoints_50_requests_zero_errors(self):
        """
        Simulate realistic mixed traffic:
        40% start, 30% DTMF, 20% PNR, 10% tracking
        """
        sessions = []
        for i in range(20):
            r = client.post("/ivr/start", json={"caller_id": f"+91500{i:07d}"})
            sessions.append(r.json()["data"]["session_id"])

        import random
        idx = [0]
        lock = threading.Lock()

        def req():
            with lock:
                sid = sessions[idx[0] % len(sessions)]
                idx[0] += 1
            choice = random.random()
            if choice < 0.4:
                client.post("/ivr/start", json={"caller_id": "+919999999999"})
            elif choice < 0.7:
                client.post("/ivr/input", json={
                    "session_id": sid, "digit": "1", "current_flow": "main_menu"
                })
            elif choice < 0.9:
                client.post("/ivr/pnr", json={"session_id": sid, "pnr_number": "4521679834"})
            else:
                client.post("/ivr/tracking", json={"session_id": sid, "train_number": "12951"})

        results, errors, duration = load_test(req, n_requests=50, n_threads=10)
        print_report("Mixed endpoints — 50 requests", results, errors, duration)

        assert len(errors) == 0
        p95 = percentile(results, 95)
        assert p95 < 500

    def test_throughput_at_least_10_rps(self):
        """System must handle at least 10 requests/second on health endpoint."""
        def req():
            client.get("/health")

        results, errors, duration = load_test(req, n_requests=50, n_threads=10)
        rps = len(results) / duration if duration > 0 else 0
        print(f"\nThroughput: {rps:.1f} req/s")
        assert rps >= 10, f"Throughput {rps:.1f} req/s is below 10 req/s minimum"