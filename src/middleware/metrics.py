import time
from fastapi import Request
from src.monitoring.metrics import (
    api_requests_total,
    request_duration_seconds,
    errors_total,
    active_requests,
    record_request_timestamp,
)


class MetricsMiddleware:
    """Prometheus metrics collection middleware."""

    def __init__(self, app):
        self.app = app
        self._active_request_count = 0

    async def __call__(self, scope, receive, send):
        # Only HTTP requests
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # active requests++
        self._active_request_count += 1
        active_requests.set(self._active_request_count)

        # last request time
        record_request_timestamp()

        start_time = time.time()
        endpoint = scope.get("path", "unknown")
        method = scope.get("method", "unknown")

        async def send_with_metrics(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time

                # total requests
                api_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status_code,
                ).inc()

                # duration histogram
                request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(duration)

                # errors counter
                if status_code >= 400:
                    errors_total.labels(
                        error_type=f"http_{status_code}",
                        endpoint=endpoint,
                    ).inc()

                # active requests--
                self._active_request_count -= 1
                active_requests.set(self._active_request_count)

            await send(message)

        await self.app(scope, receive, send_with_metrics)
