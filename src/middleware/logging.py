import time
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("app")

# rate limiter object (future use – abhi sirf create kar rahe hain)
limiter = Limiter(key_func=get_remote_address)


class RequestLoggingMiddleware:
    """ASGI-compatible logging middleware."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Only HTTP traffic
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                method = scope.get("method", "UNKNOWN")
                path = scope.get("path", "UNKNOWN")
                status_code = message["status"]

                logger.info(
                    f"{method} {path} - {status_code} - {process_time:.3f}s"
                )

                headers = message.setdefault("headers", [])
                headers.append(
                    (b"x-process-time", str(process_time).encode())
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)
