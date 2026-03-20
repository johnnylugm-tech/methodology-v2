#!/usr/bin/env python3
"""
Failover Manager - 故障轉移管理器

自動備援和故障切換
"""

import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time
import random


class HealthStatus(Enum):
    """健康狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FailoverStrategy(Enum):
    """故障轉移策略"""
    FAST_FAILOVER = "fast_failover"  # 快速切換
    GRACEFUL = "graceful"            # 優雅降級
    CASCADING = "cascading"          # 級聯降級


@dataclass
class ModelEndpoint:
    """模型端點"""
    id: str
    name: str
    provider: str
    url: str = None
    api_key: str = None
    is_primary: bool = False
    priority: int = 100  # 1-100, 越小越優先
    health: HealthStatus = HealthStatus.UNKNOWN
    latency_ms: float = 0.0
    error_rate: float = 0.0
    last_check: datetime = None
    consecutive_failures: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return 1 - (self.failed_requests / self.total_requests)
    
    @property
    def is_available(self) -> bool:
        return (self.health == HealthStatus.HEALTHY or 
                self.health == HealthStatus.DEGRADED)


@dataclass
class FailoverEvent:
    """故障事件"""
    timestamp: datetime
    source_id: str
    target_id: str
    reason: str
    duration_ms: float
    recovered: bool = False


@dataclass
class CircuitBreakerState:
    """熔斷器狀態"""
    model_id: str
    state: str = "closed"  # closed, open, half_open
    failure_count: int = 0
    last_failure: datetime = None
    next_retry: datetime = None


class CircuitBreaker:
    """熔斷器"""
    
    def __init__(self, model_id: str,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 half_open_max_calls: int = 3):
        self.model_id = model_id
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  # 秒
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitBreakerState(model_id=model_id)
        self.half_open_calls = 0
    
    def record_success(self):
        """記錄成功"""
        self.state.failure_count = 0
        self.state.state = "closed"
        self.half_open_calls = 0
    
    def record_failure(self):
        """記錄失敗"""
        self.state.failure_count += 1
        self.state.last_failure = datetime.now()
        
        if self.state.failure_count >= self.failure_threshold:
            self.state.state = "open"
            self.state.next_retry = datetime.now() + timedelta(seconds=self.recovery_timeout)
    
    def can_attempt(self) -> bool:
        """是否可以嘗試"""
        if self.state.state == "closed":
            return True
        
        if self.state.state == "open":
            if datetime.now() >= self.state.next_retry:
                self.state.state = "half_open"
                self.half_open_calls = 0
                return True
            return False
        
        if self.state.state == "half_open":
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def get_status(self) -> str:
        """取得狀態"""
        if self.state.state == "closed":
            return f"✅ Closed (failures: {self.state.failure_count})"
        elif self.state.state == "open":
            wait_time = (self.state.next_retry - datetime.now()).seconds if self.state.next_retry else 0
            return f"🔴 Open (retry in {wait_time}s)"
        else:
            return f"🟡 Half-Open (calls: {self.half_open_calls}/{self.half_open_max_calls})"


class FailoverManager:
    """故障轉移管理器"""
    
    def __init__(self, strategy: FailoverStrategy = FailoverStrategy.GRACEFUL):
        self.models: Dict[str, ModelEndpoint] = {}
        self.fallback_map: Dict[str, str] = {}  # primary_id -> fallback_id
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.events: List[FailoverEvent] = []
        self.strategy = strategy
        
        # 配置
        self.health_check_interval = 30  # 秒
        self.latency_threshold = 5000    # ms
        self.error_rate_threshold = 0.1  # 10%
    
    def register_model(self, model_id: str, name: str,
                      provider: str, is_primary: bool = False,
                      priority: int = 100, fallback_id: str = None):
        """註冊模型"""
        endpoint = ModelEndpoint(
            id=model_id,
            name=name,
            provider=provider,
            is_primary=is_primary,
            priority=priority,
        )
        
        self.models[model_id] = endpoint
        self.circuit_breakers[model_id] = CircuitBreaker(model_id)
        
        if fallback_id:
            self.fallback_map[model_id] = fallback_id
    
    def set_fallback(self, primary_id: str, fallback_id: str):
        """設定備援模型"""
        if primary_id in self.models and fallback_id in self.models:
            self.fallback_map[primary_id] = fallback_id
    
    def get_fallback(self, model_id: str) -> Optional[str]:
        """取得備援模型"""
        return self.fallback_map.get(model_id)
    
    def select_best_model(self, required_capabilities: List[str] = None) -> Optional[str]:
        """選擇最佳模型"""
        available = [
            m for m in self.models.values()
            if m.is_available and self.circuit_breakers[m.id].can_attempt()
        ]
        
        if not available:
            return None
        
        # 按優先級和健康狀態排序
        available.sort(key=lambda m: (m.priority, -m.success_rate, m.latency_ms))
        
        return available[0].id
    
    def health_check(self, model_id: str, check_func: Callable = None) -> HealthStatus:
        """健康檢查"""
        if model_id not in self.models:
            return HealthStatus.UNKNOWN
        
        model = self.models[model_id]
        
        # 如果有自訂檢查函數
        if check_func:
            try:
                start = time.time()
                result = check_func(model)
                latency = (time.time() - start) * 1000
                
                model.latency_ms = latency
                model.last_check = datetime.now()
                
                if result:
                    model.health = HealthStatus.HEALTHY
                else:
                    model.health = HealthStatus.UNHEALTHY
                
            except Exception as e:
                model.health = HealthStatus.UNHEALTHY
                model.consecutive_failures += 1
        else:
            # 預設檢查：基於指標
            if model.error_rate > self.error_rate_threshold:
                model.health = HealthStatus.UNHEALTHY
            elif model.latency_ms > self.latency_threshold:
                model.health = HealthStatus.DEGRADED
            else:
                model.health = HealthStatus.HEALTHY
        
        return model.health
    
    def record_success(self, model_id: str, latency_ms: float = None):
        """記錄成功"""
        if model_id not in self.models:
            return
        
        model = self.models[model_id]
        model.total_requests += 1
        
        if latency_ms:
            # 更新延遲 (EMA)
            if model.latency_ms > 0:
                model.latency_ms = model.latency_ms * 0.7 + latency_ms * 0.3
            else:
                model.latency_ms = latency_ms
        
        # 熔斷器
        cb = self.circuit_breakers.get(model_id)
        if cb:
            cb.record_success()
        
        # 重置連續失敗
        model.consecutive_failures = 0
    
    def record_failure(self, model_id: str, error: str = None):
        """記錄失敗"""
        if model_id not in self.models:
            return
        
        model = self.models[model_id]
        model.total_requests += 1
        model.failed_requests += 1
        model.consecutive_failures += 1
        
        # 熔斷器
        cb = self.circuit_breakers.get(model_id)
        if cb:
            cb.record_failure()
        
        # 檢查是否需要故障轉移
        if model.consecutive_failures >= 3:
            self._trigger_failover(model_id, error or "Consecutive failures")
    
    def _trigger_failover(self, model_id: str, reason: str):
        """觸發故障轉移"""
        fallback_id = self.get_fallback(model_id)
        
        if not fallback_id:
            # 嘗試自動選擇
            fallback_id = self.select_best_model()
        
        if fallback_id and fallback_id != model_id:
            self.events.append(FailoverEvent(
                timestamp=datetime.now(),
                source_id=model_id,
                target_id=fallback_id,
                reason=reason,
                duration_ms=0
            ))
    
    def execute_with_failover(self, task_func: Callable,
                             primary_model: str = None,
                             fallback_model: str = None,
                             max_retries: int = 3) -> Any:
        """執行任務，自動故障轉移"""
        if fallback_model:
            self.set_fallback(primary_model, fallback_model)
        
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            # 選擇模型
            model_id = primary_model if attempt == 0 else (
                fallback_model or self.select_best_model()
            )
            
            if not model_id:
                raise Exception("No available models")
            
            try:
                # 執行任務
                start = time.time()
                result = task_func(model_id)
                latency = (time.time() - start) * 1000
                
                # 記錄成功
                self.record_success(model_id, latency)
                
                return result
                
            except Exception as e:
                last_error = e
                attempt += 1
                
                # 記錄失敗
                self.record_failure(model_id, str(e))
                
                # 等待後重試
                if attempt < max_retries:
                    wait_time = min(2 ** attempt, 30)  # 指數退避，最多 30 秒
                    time.sleep(wait_time)
        
        # 所有重試都失敗
        raise last_error or Exception("All retries failed")
    
    def get_model_status(self, model_id: str = None) -> Dict:
        """取得模型狀態"""
        if model_id:
            models = [self.models.get(model_id)] if model_id in self.models else []
        else:
            models = self.models.values()
        
        return [
            {
                "id": m.id,
                "name": m.name,
                "health": m.health.value,
                "latency_ms": m.latency_ms,
                "error_rate": m.error_rate,
                "success_rate": m.success_rate,
                "is_primary": m.is_primary,
                "priority": m.priority,
                "circuit_breaker": self.circuit_breakers[m.id].get_status() if m.id in self.circuit_breakers else "N/A",
            }
            for m in models if m
        ]
    
    def get_failover_history(self, limit: int = 20) -> List[Dict]:
        """取得故障轉移歷史"""
        events = sorted(self.events, key=lambda x: -x.timestamp.timestamp())
        
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "from": e.source_id,
                "to": e.target_id,
                "reason": e.reason,
                "recovered": e.recovered,
            }
            for e in events[:limit]
        ]
    
    def generate_report(self) -> str:
        """生成報告"""
        status = self.get_model_status()
        
        healthy = sum(1 for s in status if s['health'] == 'healthy')
        degraded = sum(1 for s in status if s['health'] == 'degraded')
        unhealthy = sum(1 for s in status if s['health'] == 'unhealthy')
        
        report = f"""
# 🔄 Failover 報告

## 模型狀態

| 模型 | 狀態 | 延遲 | 成功率 | 熔斷器 |
|------|------|------|--------|--------|
"""
        
        for s in status:
            health_icon = "✅" if s['health'] == 'healthy' else "🟡" if s['health'] == 'degraded' else "🔴"
            report += f"| {s['name']} | {health_icon} {s['health']} | {s['latency_ms']:.0f}ms | {s['success_rate']:.1%} | {s['circuit_breaker']} |\n"
        
        report += f"""

## 故障轉移歷史

| 時間 | 從 | 到 | 原因 |
|------|----|----|------|
"""
        
        history = self.get_failover_history(5)
        if history:
            for h in history:
                report += f"| {h['timestamp']} | {h['from']} | {h['to']} | {h['reason']} |\n"
        else:
            report += "| 無記錄 | - | - | - |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    manager = FailoverManager()
    
    # 註冊模型
    print("=== Registering Models ===")
    manager.register_model("gpt-4o", "GPT-4o", "OpenAI", is_primary=True, priority=1)
    manager.register_model("claude-4-sonnet", "Claude 4 Sonnet", "Anthropic", priority=2)
    manager.register_model("minimax-m2.7", "MiniMax M2.7", "MiniMax", priority=3)
    
    # 設定備援鏈
    manager.set_fallback("gpt-4o", "claude-4-sonnet")
    manager.set_fallback("claude-4-sonnet", "minimax-m2.7")
    
    # 模擬一些請求
    print("\n=== Simulating Requests ===")
    
    def mock_task(model_id):
        # 模擬任務
        if random.random() < 0.1:  # 10% 失敗率
            raise Exception("Simulated error")
        return f"Result from {model_id}"
    
    # 執行任務
    for i in range(10):
        try:
            result = manager.execute_with_failover(
                lambda mid=f"model-{i}": mock_task(mid),
                primary_model="gpt-4o",
                fallback_model="claude-4-sonnet"
            )
            print(f"Success: {result}")
        except Exception as e:
            print(f"Failed: {e}")
    
    # 狀態
    print("\n=== Model Status ===")
    for s in manager.get_model_status():
        print(f"{s['name']}: {s['health']} ({s['success_rate']:.1%})")
    
    # 報告
    print("\n=== Report ===")
    print(manager.generate_report())
