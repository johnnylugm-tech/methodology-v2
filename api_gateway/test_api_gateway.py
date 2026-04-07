"""Tests for api_gateway module"""
import pytest
from api_gateway import RateLimiter, AuthMiddleware, RequestMonitor, ResponseTransformer, APIGateway, Request, Response

class TestRateLimiter:
    """Test RateLimiter"""
    
    def test_check(self):
        """Test rate limit check"""
        limiter = RateLimiter(requests=5, window=60)
        assert limiter.check("client1") is True
    
    def test_limit_exceeded(self):
        """Test rate limit exceeded"""
        limiter = RateLimiter(requests=1, window=60)
        limiter.check("client1")
        assert limiter.check("client1") is False
    
    def test_get_remaining(self):
        """Test remaining requests"""
        limiter = RateLimiter(requests=5, window=60)
        remaining = limiter.get_remaining("client1")
        assert remaining == 5

class TestAuthMiddleware:
    """Test AuthMiddleware"""
    
    def test_authenticate_with_key(self):
        """Test authentication with API key"""
        auth = AuthMiddleware(api_key="test_key")
        request = Request(method="GET", path="/test", headers={"Authorization": "Bearer test_key"})
        assert auth.authenticate(request) is True

class TestRequestMonitor:
    """Test RequestMonitor"""
    
    def test_track(self):
        """Test tracking"""
        monitor = RequestMonitor()
        req = Request(method="GET", path="/test")
        resp = Response(status_code=200)
        monitor.track(req, resp, 0.1)
        stats = monitor.get_stats()
        assert stats["total_requests"] == 1

class TestResponseTransformer:
    """Test ResponseTransformer"""
    
    def test_transform(self):
        """Test transformation"""
        transformer = ResponseTransformer(add_headers={"X-Custom": "value"})
        resp = Response(status_code=200, body={"data": "test"})
        result = transformer.transform(resp)
        assert "X-Custom" in result.headers

class TestAPIGateway:
    """Test APIGateway"""
    
    def test_rate_limit(self):
        """Test rate limiting"""
        gateway = APIGateway()
        gateway.rate_limiter = RateLimiter(requests=1, window=60)
        
        req1 = Request(method="GET", path="/test")
        req2 = Request(method="GET", path="/test")
        
        resp1 = gateway.handle(req1)
        assert resp1.status_code == 200
        
        resp2 = gateway.handle(req2)
        assert resp2.status_code == 429

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
