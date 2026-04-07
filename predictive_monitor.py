#!/usr/bin/env python3
"""
Predictive Monitor - 預測性監控

基於歷史數據預測異常
"""

import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics


@dataclass
class MetricPoint:
    """指標數據點"""
    timestamp: datetime
    value: float
    labels: Dict = field(default_factory=dict)


@dataclass
class Prediction:
    """預測結果"""
    metric: str
    predicted_value: float
    confidence: float  # 0-1
    trend: str  # up, down, stable
    recommendation: str


class PredictiveMonitor:
    """預測性監控"""
    
    def __init__(self, history_size: int = 100):
        """
        初始化
        
        Args:
            history_size: 歷史數據大小
        """
        self.history_size = history_size
        self.metrics: Dict[str, deque] = {}
        self.thresholds: Dict[str, Dict] = {}
    
    def record(self, metric: str, value: float, labels: Dict = None):
        """
        記錄指標
        
        Args:
            metric: 指標名稱
            value: 值
            labels: 標籤
        """
        if metric not in self.metrics:
            self.metrics[metric] = deque(maxlen=self.history_size)
        
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.metrics[metric].append(point)
    
    def set_threshold(self, metric: str, warning: float, critical: float):
        """
        設定閾值
        
        Args:
            metric: 指標名稱
            warning: 警告閾值
            critical: 嚴重閾值
        """
        self.thresholds[metric] = {
            "warning": warning,
            "critical": critical
        }
    
    def predict(self, metric: str, horizon: int = 5) -> Optional[Prediction]:
        """
        預測未來趨勢
        
        預測演算法說明：
        
        1. 資料收集
           - 需要至少 10 個歷史數據點
           - 每個數據點包含：value, timestamp, tags
        
        2. 線性迴歸 (Linear Regression)
           - 使用最小平方法 (OLS) 擬合直線
           - y = slope × x + intercept
           - slope: 趨勢斜率 (正值=上升, 負值=下降)
           - intercept: 截距
        
        3. 預測計算
           - 未來值 = slope × (n + horizon) + intercept
           - n = 歷史數據點數量
           - horizon = 預測未來多少個點
        
        4. 置信度計算 (R²)
           - R² = 1 - (SS_res / SS_tot)
           - SS_res: 殘差平方和
           - SS_tot: 總平方和
        
        5. 置信度等級
           - >80%: 數據穩定，趨勢明顯 (HIGH)
           - 50-80%: 數據有一定波動 (MEDIUM)
           - <50%: 數據隨機性高 (LOW)
        
        Args:
            metric: 指標名稱
            horizon: 預測未來多少個點
            
        Returns:
            Prediction 或 None (數據不足時)
        """
        if metric not in self.metrics or len(self.metrics[metric]) < 10:
            return None
        
        # 獲取歷史數據
        history = list(self.metrics[metric])
        values = [p.value for p in history]
        
        # 簡單線性回歸預測
        n = len(values)
        x_mean = sum(range(n)) / n
        y_mean = sum(values) / n
        
        # 計算斜率和截距
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return None
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # 預測未來
        future_x = n + horizon - 1
        predicted_value = slope * future_x + intercept
        
        # 計算置信度（基於 R²）
        ss_res = sum((v - (slope * i + intercept)) ** 2 for i, v in enumerate(values))
        ss_tot = sum((v - y_mean) ** 2 for v in values)
        
        if ss_tot == 0:
            confidence = 0.5
        else:
            r_squared = 1 - (ss_res / ss_tot)
            confidence = max(0, min(1, r_squared))
        
        # 趨勢
        if slope > 0.1:
            trend = "up"
        elif slope < -0.1:
            trend = "down"
        else:
            trend = "stable"
        
        # 建議
        recommendation = self._get_recommendation(metric, predicted_value, trend)
        
        return Prediction(
            metric=metric,
            predicted_value=predicted_value,
            confidence=confidence,
            trend=trend,
            recommendation=recommendation
        )
    
    def _get_recommendation(self, metric: str, predicted_value: float, trend: str) -> str:
        """獲取建議"""
        if metric == "error_rate":
            if predicted_value > 10:
                return "🔴 建議立即檢查系統錯誤"
            elif predicted_value > 5:
                return "🟡 建議關注錯誤趨勢"
            else:
                return "✅ 錯誤率正常"
        
        elif metric == "latency":
            if predicted_value > 5:
                return "🔴 建議擴展資源"
            elif predicted_value > 2:
                return "🟡 建議優化效能"
            else:
                return "✅ 延遲正常"
        
        elif metric == "cost":
            if trend == "up":
                return "🟡 成本上升中，建議優化"
            else:
                return "✅ 成本穩定"
        
        elif metric == "health_score":
            if predicted_value < 50:
                return "🔴 健康分數過低，建議全面檢查"
            elif predicted_value < 75:
                return "🟡 健康分數下降中"
            else:
                return "✅ 健康分數正常"
        
        return "✅ 指標正常"
    
    def check_thresholds(self, metric: str, value: float) -> str:
        """
        檢查閾值
        
        Args:
            metric: 指標名稱
            value: 值
            
        Returns:
            狀態 (normal/warning/critical)
        """
        if metric not in self.thresholds:
            return "normal"
        
        thresholds = self.thresholds[metric]
        
        if value >= thresholds["critical"]:
            return "critical"
        elif value >= thresholds["warning"]:
            return "warning"
        else:
            return "normal"
    
    def get_anomaly_score(self, metric: str, value: float) -> float:
        """
        獲取異常分數
        
        Args:
            metric: 指標名稱
            value: 值
            
        Returns:
            異常分數 (0-100)
        """
        if metric not in self.metrics or len(self.metrics[metric]) < 5:
            return 0
        
        values = [p.value for p in self.metrics[metric]]
        
        # 計算 Z-score
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 1
        
        if stdev == 0:
            return 0
        
        z_score = abs((value - mean) / stdev)
        
        # 轉換為 0-100 分
        return min(100, z_score * 25)
    
    def get_trend_analysis(self, metric: str) -> Dict:
        """
        獲取趨勢分析
        
        Args:
            metric: 指標名稱
            
        Returns:
            趨勢分析
        """
        if metric not in self.metrics or len(self.metrics[metric]) < 5:
            return {}
        
        history = list(self.metrics[metric])
        values = [p.value for p in history]
        
        # 計算趨勢
        n = len(values)
        
        # 簡單移動平均
        ma_5 = values[-5:] if len(values) >= 5 else values
        ma_prev = values[:-5] if len(values) >= 10 else values[:n//2]
        
        current_ma = statistics.mean(ma_5)
        previous_ma = statistics.mean(ma_prev)
        
        change_pct = ((current_ma - previous_ma) / previous_ma * 100) if previous_ma else 0
        
        return {
            "metric": metric,
            "current_value": values[-1] if values else 0,
            "moving_average_5": current_ma,
            "previous_average": previous_ma,
            "change_percent": change_pct,
            "trend": "up" if change_pct > 5 else "down" if change_pct < -5 else "stable",
            "volatility": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def get_summary(self) -> Dict:
        """獲取摘要"""
        summary = {
            "metrics": [],
            "alerts": [],
            "predictions": []
        }
        
        for metric in self.metrics:
            # 閾值檢查
            if self.metrics[metric]:
                latest = self.metrics[metric][-1]
                status = self.check_thresholds(metric, latest.value)
                
                if status != "normal":
                    summary["alerts"].append({
                        "metric": metric,
                        "value": latest.value,
                        "status": status,
                        "timestamp": latest.timestamp.isoformat()
                    })
            
            # 預測
            prediction = self.predict(metric)
            if prediction:
                summary["predictions"].append({
                    "metric": metric,
                    "predicted_value": prediction.predicted_value,
                    "confidence": prediction.confidence,
                    "trend": prediction.trend,
                    "recommendation": prediction.recommendation
                })
        
        return summary


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    monitor = PredictiveMonitor()
    
    # 設定閾值
    monitor.set_threshold("latency", warning=2, critical=5)
    monitor.set_threshold("error_rate", warning=5, critical=10)
    monitor.set_threshold("health_score", warning=75, critical=50)
    
    # 模擬數據
    import random
    
    print("=== Predictive Monitor Demo ===\n")
    
    # 記錄歷史數據
    for i in range(50):
        monitor.record("latency", 1.0 + random.random() * 2)
        monitor.record("error_rate", random.random() * 3)
        monitor.record("health_score", 90 - i * 0.3 + random.random() * 5)
    
    # 預測
    print("=== Predictions ===")
    for metric in ["latency", "error_rate", "health_score"]:
        pred = monitor.predict(metric)
        if pred:
            print(f"\n{metric}:")
            print(f"  Predicted: {pred.predicted_value:.2f}")
            print(f"  Confidence: {pred.confidence:.2%}")
            print(f"  Trend: {pred.trend}")
            print(f"  Recommendation: {pred.recommendation}")
    
    # 趨勢分析
    print("\n=== Trend Analysis ===")
    for metric in ["latency", "error_rate", "health_score"]:
        trend = monitor.get_trend_analysis(metric)
        if trend:
            print(f"\n{metric}:")
            print(f"  Current: {trend['current_value']:.2f}")
            print(f"  Change: {trend['change_percent']:.1f}%")
            print(f"  Trend: {trend['trend']}")
    
    # 摘要
    print("\n=== Summary ===")
    summary = monitor.get_summary()
    print(f"Alerts: {len(summary['alerts'])}")
    print(f"Predictions: {len(summary['predictions'])}")
