from __future__ import annotations

from typing import Optional

try:
    from prometheus_client import Counter, Histogram, Gauge  # type: ignore
except Exception:  # pragma: no cover
    # No-op fallbacks if prometheus_client is not installed
    class _Noop:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            return None
        def observe(self, *args, **kwargs):
            return None
        def set(self, *args, **kwargs):
            return None

    def Counter(*args, **kwargs):
        return _Noop()
    def Histogram(*args, **kwargs):
        return _Noop()
    def Gauge(*args, **kwargs):
        return _Noop()


llm_requests = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "model", "operation"],
)
llm_errors = Counter(
    "llm_errors_total",
    "Total LLM API errors",
    ["provider", "model", "operation"],
)
llm_latency = Histogram(
    "llm_latency_seconds",
    "LLM response latency",
    ["provider", "model", "operation"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10),
)
llm_cost = Gauge(
    "llm_cost_usd",
    "Cumulative LLM cost in USD",
    ["provider", "model"],
)


def record_request(provider: str, model: str, operation: str) -> None:
    llm_requests.labels(provider=provider, model=model, operation=operation).inc()


def record_error(provider: str, model: str, operation: str) -> None:
    llm_errors.labels(provider=provider, model=model, operation=operation).inc()


def observe_latency(provider: str, model: str, operation: str, seconds: float) -> None:
    llm_latency.labels(provider=provider, model=model, operation=operation).observe(seconds)


def add_cost(provider: str, model: str, amount_usd: float) -> None:
    # This is cumulative by convention
    try:
        # This fetches current and adds amount; if not supported, set still works
        llm_cost.labels(provider=provider, model=model).inc(amount_usd)  # type: ignore[attr-defined]
    except Exception:
        pass


