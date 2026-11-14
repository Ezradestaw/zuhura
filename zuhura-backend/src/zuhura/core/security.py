"""
Security headers, rate limiting and error sanitisation middleware.
Rate limiting uses a sliding window per client address.
"""

import ipaddress
import time
import threading
from typing import Dict, List
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from zuhura.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects mission-grade HTTP security headers onto every outbound response.
    Enforces strict isolation, frame security, MIME-type sniffing prevention,
    and HSTS transport security.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Defense-in-depth security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        response.headers["X-Planetary-Datum"] = "IAU/IAG 2015 WGCCRE (Mars)"

        return response


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding-window rate limiter for protecting compute-intensive
    scientific simulation endpoints from denial-of-service and quota exhaustion.
    """

    def __init__(self, requests_per_minute: int = 120):
        self.limit = requests_per_minute
        self.window_seconds = 60.0
        self._lock = threading.RLock()
        self._history: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str) -> tuple[bool, int, float]:
        """
        Determines whether client request is permitted under sliding window.
        Returns (is_allowed, remaining_quota, retry_after_seconds).
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            if client_ip not in self._history:
                self._history[client_ip] = []

            # Prune timestamps older than window
            timestamps = self._history[client_ip]
            self._history[client_ip] = [t for t in timestamps if t > window_start]
            valid_timestamps = self._history[client_ip]

            count = len(valid_timestamps)
            if count < self.limit:
                valid_timestamps.append(now)
                remaining = self.limit - (count + 1)
                return True, remaining, 0.0

            # Rate limit exceeded
            oldest_timestamp = valid_timestamps[0]
            retry_after = max(1.0, round((oldest_timestamp + self.window_seconds) - now, 1))
            return False, 0, retry_after

    def reset(self) -> None:
        """Clears all client request histories."""
        with self._lock:
            self._history.clear()


# Default rate limiters: General endpoints vs Compute-heavy endpoints
general_limiter = SlidingWindowRateLimiter(requests_per_minute=300)
heavy_compute_limiter = SlidingWindowRateLimiter(requests_per_minute=60)


def _is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _is_trusted_proxy(peer_ip: str) -> bool:
    if not _is_ip_address(peer_ip):
        return False
    peer = ipaddress.ip_address(peer_ip)
    for cidr in settings.TRUSTED_PROXY_CIDRS:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            continue
        if peer in network:
            return True
    return False


def resolve_client_ip(request: Request) -> str:
    """
    Use the socket peer unless that peer is an explicitly trusted proxy.
    A trusted proxy may supply X-Forwarded-For. The client is the right-most
    hop that is not itself a trusted proxy, and only if it is a real IP.
    """
    peer = request.client.host if request.client else "127.0.0.1"
    if not _is_trusted_proxy(peer):
        return peer

    forwarded = request.headers.get("x-forwarded-for")
    if not forwarded:
        return peer

    hops = [part.strip() for part in forwarded.split(",") if part.strip() and _is_ip_address(part.strip())]
    if not hops:
        return peer

    for hop in reversed(hops):
        if not _is_trusted_proxy(hop):
            return hop
    return hops[0]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware applying adaptive rate limiting to incoming requests.
    Exempts health, metrics, and documentation endpoints.
    """

    EXEMPT_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
        "/api/v1/health",
        "/api/v1/health/liveness",
        "/api/v1/health/readiness",
    }

    HEAVY_PATHS = {
        "/api/v1/spatial/vision/orb-match",
        "/api/v1/spatial/navigation/optimize-route",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Check exemption
        if path in self.EXEMPT_PATHS or path.startswith("/static"):
            return await call_next(request)

        client_ip = resolve_client_ip(request)

        # Select limiter based on endpoint intensity
        limiter = heavy_compute_limiter if path in self.HEAVY_PATHS else general_limiter
        allowed, remaining, retry_after = limiter.is_allowed(client_ip)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded for planetary simulation compute resource.",
                    "status_code": 429,
                    "retry_after_seconds": retry_after,
                    "policy": f"Maximum {limiter.limit} requests per minute."
                },
                headers={
                    "Retry-After": str(int(retry_after)),
                    "X-RateLimit-Limit": str(limiter.limit),
                    "X-RateLimit-Remaining": "0"
                }
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limiter.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
