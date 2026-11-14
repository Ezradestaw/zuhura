#!/usr/bin/env python3
"""
Zuhura Planetary Digital Twin - Stage 8 Performance Benchmark Runner
Measures response latency percentiles (P50, P90, P95, P99) and memory RSS
across all 4 Scientific Terrain Intelligence endpoints to verify AC-09 criteria.
"""

import os
import sys
import time
import json
import psutil
import requests
import numpy as np
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1/spatial/terrain"

def benchmark_endpoint(name: str, url: str, payload: dict, iterations: int = 100):
    print(f"\nBenchmarking {name} ({iterations} iterations)...")
    latencies = []
    
    # Warmup
    for _ in range(5):
        requests.post(url, json=payload)
    
    process = psutil.Process(os.getpid())
    rss_start = process.memory_info().rss / (1024 * 1024)
    
    t_start = time.perf_counter()
    for i in range(iterations):
        t0 = time.perf_counter()
        resp = requests.post(url, json=payload)
        t1 = time.perf_counter()
        if resp.status_code != 200:
            print(f"  Error on iteration {i}: HTTP {resp.status_code} - {resp.text}")
            continue
        latencies.append((t1 - t0) * 1000.0) # in ms
    t_total = time.perf_counter() - t_start
    
    rss_end = process.memory_info().rss / (1024 * 1024)
    rss_delta = rss_end - rss_start
    
    p50 = float(np.percentile(latencies, 50))
    p90 = float(np.percentile(latencies, 90))
    p95 = float(np.percentile(latencies, 95))
    p99 = float(np.percentile(latencies, 99))
    mean = float(np.mean(latencies))
    
    print(f"  Mean: {mean:.2f} ms | P50: {p50:.2f} ms | P90: {p90:.2f} ms | P95: {p95:.2f} ms | P99: {p99:.2f} ms")
    print(f"  Throughput: {len(latencies) / t_total:.1f} req/s | RSS Delta: {rss_delta:+.2f} MB")
    
    return {
        "endpoint": name,
        "iterations": len(latencies),
        "mean_ms": round(mean, 2),
        "p50_ms": round(p50, 2),
        "p90_ms": round(p90, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "throughput_rps": round(len(latencies) / t_total, 1),
        "rss_delta_mb": round(rss_delta, 2)
    }

def main():
    print("=" * 70)
    print("ZUHURA STAGE 8: TERRAIN INTELLIGENCE API BENCHMARK SUITE")
    print("=" * 70)
    
    results = {}
    
    # 1. Point Analysis
    results["point_analysis"] = benchmark_endpoint(
        "POST /point-analysis",
        f"{BASE_URL}/point-analysis",
        {"latitude": 18.38, "longitude": 77.58, "kernel_size": 3, "include_morphometry": True},
        iterations=100
    )
    
    # 2. Transect Profile (50 samples)
    results["profile_50"] = benchmark_endpoint(
        "POST /profile (50 samples)",
        f"{BASE_URL}/profile",
        {
            "start_point": {"latitude": 18.25, "longitude": 77.35},
            "end_point": {"latitude": 18.50, "longitude": 77.80},
            "num_samples": 50,
            "include_derivatives": True
        },
        iterations=100
    )
    
    # 3. Transect Profile (200 samples)
    results["profile_200"] = benchmark_endpoint(
        "POST /profile (200 samples)",
        f"{BASE_URL}/profile",
        {
            "start_point": {"latitude": 18.25, "longitude": 77.35},
            "end_point": {"latitude": 18.50, "longitude": 77.80},
            "num_samples": 200,
            "include_derivatives": True
        },
        iterations=50
    )
    
    # 4. Area Statistics (15 km radius)
    results["statistics"] = benchmark_endpoint(
        "POST /statistics (15 km radius)",
        f"{BASE_URL}/statistics",
        {"center_point": {"latitude": 18.38, "longitude": 77.58}, "radius_km": 15.0},
        iterations=50
    )
    
    # 5. Spatial Comparison
    results["compare"] = benchmark_endpoint(
        "POST /compare",
        f"{BASE_URL}/compare",
        {
            "site_a": {"latitude": 18.38, "longitude": 77.58},
            "site_b": {"latitude": -5.37, "longitude": 137.81},
            "name_a": "Jezero",
            "name_b": "Gale"
        },
        iterations=50
    )
    
    out_path = Path("/home/anonymous/Zuhura/reports/stage8/terrain_api_benchmark_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"Benchmark results successfully written to {out_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
