from prometheus_client import Counter, Histogram, Gauge
import time

# -------------------- HTTP-level Counters --------------------

api_requests_total = Counter(
    "api_requests_total",
    "Total number of API requests received",
    ["method", "endpoint", "status"],
)

errors_total = Counter(
    "errors_total",
    "Total number of errors",
    ["error_type", "endpoint"],
)

# -------------------- HTTP-level Histograms --------------------

request_duration_seconds = Histogram(
    "request_duration_seconds",
    "Time spent processing request in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# -------------------- HTTP-level Gauges --------------------

active_requests = Gauge(
    "active_requests_current",
    "Number of currently active requests",
)

last_request_timestamp = Gauge(
    "last_request_timestamp_seconds",
    "Timestamp of last received request",
)


def record_request_timestamp() -> None:
    """Set gauge to current UNIX timestamp."""
    last_request_timestamp.set(time.time())


# ======================================================================
# Domain-specific metrics for documents / simplification / analysis
# ======================================================================

# -------- Document operations --------

documents_processed_total = Counter(
    "documents_processed_total",
    "Total documents processed by operation",
    ["operation"], 
)

# -------- Simplification metrics --------

simplifications_total = Counter(
    "simplifications_total",
    "Total simplifications performed by document type",
    ["document_type"],  # contract | policy | text | unknown ...
)

simplification_duration_seconds = Histogram(
    "simplification_duration_seconds",
    "Time spent simplifying documents in seconds",
    ["document_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# -------- Analysis metrics --------

analysis_duration_seconds = Histogram(
    "analysis_duration_seconds",
    "Time spent analyzing documents in seconds",
    ["analysis_type"],  # e.g. basic | deep
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
)


# ======================================================================
# Helper functions for routes
# ======================================================================

def record_document_operation(operation: str) -> None:
    """Increment document operation counter."""
    documents_processed_total.labels(operation=operation).inc()


def record_simplification(duration: float, document_type: str = "unknown") -> None:
    """Record a simplification operation and its duration."""
    simplifications_total.labels(document_type=document_type).inc()
    simplification_duration_seconds.labels(document_type=document_type).observe(duration)


def record_analysis(duration: float, analysis_type: str = "basic") -> None:
    """Record analysis duration for a given analysis type."""
    analysis_duration_seconds.labels(analysis_type=analysis_type).observe(duration)
