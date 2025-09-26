from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from time import time
from collections import defaultdict
from typing import List

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, routes_prefix: List[str], rate_per_min: int = 60):
        super().__init__(app)
        self.routes_prefix = routes_prefix
        self.rate_per_min = rate_per_min
        self.bucket = defaultdict(list)  # naive in-memory

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in self.routes_prefix):
            key = request.client.host or "unknown"
            now = time()
            window = now - 60
            self.bucket[key] = [t for t in self.bucket[key] if t >= window]
            if len(self.bucket[key]) >= self.rate_per_min:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
            self.bucket[key].append(now)
        return await call_next(request)
