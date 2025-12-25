from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import time


limiter = Limiter(key_func=get_remote_address)


class RequestLoggingMiddleware:
    """ASGI-compatible logging middleware"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            # Non-HTTP (websocket etc.)
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                # You can log here
                method = scope.get("method")
                path = scope.get("path")
                status_code = message["status"]
                print(f"{method} {path} - {status_code} - {process_time:.3f}s")
                headers = message.setdefault("headers", [])
                headers.append((b"x-process-time", str(process_time).encode()))
            await send(message)

        await self.app(scope, receive, send_wrapper)
