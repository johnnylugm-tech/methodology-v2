"""API Gateway for methodology-v2 with framework integration"""
import time, json

# Framework integration
try:
    import sys
    sys.path.insert(0, '/workspace/methodology-v2')
    from methodology import RBAC, ErrorClassifier
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False
from typing import Any, Callable, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

@dataclass
class Request:
    """HTTP Request"""
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    query_params: Dict[str, str] = field(default_factory=dict)

@dataclass
class Response:
    """HTTP Response"""
    status_code: int = 200
    body: Any = None
    headers: Dict[str, str] = field(default_factory=dict)

class RateLimiter:
    """Rate limiting middleware"""
    
    def __init__(self, requests: int = 100, window: int = 60, strategy: str = "sliding"):
        self.requests = requests
        self.window = window
        self.strategy = strategy
        self._requests: Dict[str, List[float]] = defaultdict(list)
    
    def check(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window
        
        if self.strategy == "sliding":
            # Remove old requests
            self._requests[client_id] = [t for t in self._requests[client_id] if t > window_start]
        
        # Check limit
        if len(self._requests[client_id]) >= self.requests:
            return False
        
        # Add request
        self._requests[client_id].append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        now = time.time()
        window_start = now - self.window
        self._requests[client_id] = [t for t in self._requests[client_id] if t > window_start]
        return max(0, self.requests - len(self._requests[client_id]))

class AuthMiddleware:
    """Authentication middleware"""
    
# TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable -     def __init__(self, api_key: Optional[str] = None, jwt_secret: Optional[str] = None):
# TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable -         self.api_key = api_key
        self.jwt_secret = jwt_secret
    
    def authenticate(self, request: Request) -> bool:
        # API Key check
        if self.api_key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
# TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable -                 if token == self.api_key:
                    return True
            return False
        return True  # No auth if not configured

class RequestMonitor:
    """Monitor API requests"""
    
    def __init__(self):
        self._metrics: List[Dict] = []
        self._counts: Dict[str, int] = defaultdict(int)
    
    def track(self, request: Request, response: Response, duration: float):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration": duration
        }
        self._metrics.append(entry)
        self._counts[request.path] += 1
    
    def get_stats(self) -> Dict:
        return {
            "total_requests": len(self._metrics),
            "by_endpoint": dict(self._counts),
            "recent": self._metrics[-10:]
        }

class ResponseTransformer:
    """Transform responses"""
    
    def __init__(self, format: str = "json", compression: bool = False, add_headers: Dict = None):
        self.format = format
        self.compression = compression
        self.add_headers = add_headers or {}
    
    def transform(self, response: Response) -> Response:
        # Add custom headers
        response.headers.update(self.add_headers)
        
        # Compression header
        if self.compression:
            response.headers["Content-Encoding"] = "gzip"
        
        return response

class APIGateway:
    """Main API Gateway"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.routes: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
        self.rate_limiter = RateLimiter()
        self.auth = AuthMiddleware()
        self.monitor = RequestMonitor()
        self.transformer = ResponseTransformer()
    
    def use(self, middleware: Callable):
        """Add middleware"""
        self.middleware.append(middleware)
    
    def route(self, path: str, methods: List[str] = None):
        """Register route"""
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator
    
    def handle(self, request: Request) -> Response:
        """Handle request"""
        start_time = time.time()
        
        # Rate limiting
        client_id = request.headers.get("X-Client-ID", "default")
        if not self.rate_limiter.check(client_id):
            return Response(
                status_code=429,
                body={"error": "Rate limit exceeded"}
            )
        
        # Authentication
        if not self.auth.authenticate(request):
            return Response(
                status_code=401,
                body={"error": "Unauthorized"}
            )
        
        # Route to handler
        handler = self.routes.get(request.path)
        if not handler:
            return Response(
                status_code=404,
                body={"error": "Not found"}
            )
        
        # Execute handler
        try:
            response = handler(request)
        except Exception as e:
            response = Response(
                status_code=500,
                body={"error": str(e)}
            )
        
        # Transform response
        response = self.transformer.transform(response)
        
        # Monitor
        duration = time.time() - start_time
        self.monitor.track(request, response, duration)
        
        return response

# Demo
if __name__ == "__main__":
    gateway = APIGateway(port=8080)
    
    # Add rate limiter
    gateway.use(gateway.rate_limiter)
    
    @gateway.route("/hello")
    def hello(request):
        return Response(body={"message": "Hello from API Gateway!"})
    
    @gateway.route("/agent/run")
    def agent_run(request):
        return Response(body={"status": "Agent executed"})
    
    # Stats
# # #     print("API Gateway initialized")
# # #     print(f"Routes: {list(gateway.routes.keys())}")
# # #     print(f"Rate limit: {gateway.rate_limiter.requests} req/{gateway.rate_limiter.window}s")
    
    # Test
    req = Request(method="GET", path="/hello")
    resp = gateway.handle(req)
# # #     print(f"\nResponse: {resp.status_code} - {resp.body}")
