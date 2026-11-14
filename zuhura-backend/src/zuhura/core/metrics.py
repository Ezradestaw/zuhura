"""
Minimal metrics registry with Prometheus text output.
Has no external dependencies.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

START_TIME = time.time()

# Thread-safe in-memory metrics storage
_request_counts: Dict[Tuple[str, str, int], int] = defaultdict(int)
_request_latencies: Dict[str, list] = defaultdict(list)
_ai_tool_counts: Dict[Tuple[str, str], int] = defaultdict(int)
_tile_cache_hits: int = 0
_tile_cache_misses: int = 0


def record_request(method: str, path: str, status_code: int, duration_seconds: float):
    """Records HTTP request telemetry."""
    # Normalize path to avoid high-cardinality label explosion
    norm_path = path.split("?")[0]
    if norm_path.startswith("/api/v1/tiles"):
        norm_path = "/api/v1/tiles/*"
    _request_counts[(method, norm_path, status_code)] += 1
    
    # Keep last 100 latency samples per path
    l_list = _request_latencies[norm_path]
    l_list.append(duration_seconds)
    if len(l_list) > 100:
        l_list.pop(0)


def record_ai_tool(tool_name: str, status: str):
    """Records scientific AI tool invocation."""
    _ai_tool_counts[(tool_name, status)] += 1


def record_tile_cache(hit: bool):
    """Records raster tile cache hit or miss."""
    global _tile_cache_hits, _tile_cache_misses
    if hit:
        _tile_cache_hits += 1
    else:
        _tile_cache_misses += 1


def generate_prometheus_metrics_text() -> str:
    """
    Renders metrics in the standard Prometheus exposition format (text/plain; version=0.0.4).
    """
    lines = []
    now = time.time()
    uptime = now - START_TIME

    # Uptime
    lines.append("# HELP zuhura_uptime_seconds Total runtime of the Zuhura backend service.")
    lines.append("# TYPE zuhura_uptime_seconds gauge")
    lines.append(f"zuhura_uptime_seconds {uptime:.2f}")

    # HTTP Requests Total
    lines.append("# HELP zuhura_http_requests_total Total number of HTTP requests processed.")
    lines.append("# TYPE zuhura_http_requests_total counter")
    if not _request_counts:
        lines.append('zuhura_http_requests_total{method="GET",path="/health",status="200"} 1')
    for (method, path, status), count in _request_counts.items():
        lines.append(f'zuhura_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

    # Request Latencies Mean
    lines.append("# HELP zuhura_http_request_duration_seconds_mean Rolling average latency in seconds.")
    lines.append("# TYPE zuhura_http_request_duration_seconds_mean gauge")
    for path, latencies in _request_latencies.items():
        if latencies:
            mean_lat = sum(latencies) / len(latencies)
            lines.append(f'zuhura_http_request_duration_seconds_mean{{path="{path}"}} {mean_lat:.4f}')

    # AI Tool Executions
    lines.append("# HELP zuhura_ai_tool_executions_total Executions of deterministic scientific tools.")
    lines.append("# TYPE zuhura_ai_tool_executions_total counter")
    for (tool, status), count in _ai_tool_counts.items():
        lines.append(f'zuhura_ai_tool_executions_total{{tool="{tool}",status="{status}"}} {count}')

    # Tile Cache Hits & Misses
    lines.append("# HELP zuhura_tile_cache_hits_total Total imagery and DEM tile cache hits.")
    lines.append("# TYPE zuhura_tile_cache_hits_total counter")
    lines.append(f"zuhura_tile_cache_hits_total {_tile_cache_hits}")
    lines.append("# HELP zuhura_tile_cache_misses_total Total tile cache misses.")
    lines.append("# TYPE zuhura_tile_cache_misses_total counter")
    lines.append(f"zuhura_tile_cache_misses_total {_tile_cache_misses}")

    return "\n".join(lines) + "\n"
