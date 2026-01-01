from prometheus_client import Counter, Histogram, Gauge

documents_uploaded = Counter(
    "documents_uploaded_total", "Total documents uploaded"
)
documents_simplified = Counter(
    "documents_simplified_total", "Total documents simplified"
)
simplification_time = Histogram(
    "simplification_duration_seconds", "Time taken to simplify documents"
)
active_processing = Gauge(
    "documents_processing", "Documents currently processing"
)
api_requests = Counter(
    "api_requests_total", "Total API requests", ["method", "endpoint", "status_code"]
)
