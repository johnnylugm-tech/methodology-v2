"""
Baseline Manager — Phase-Gate Baseline 建立 + 版本化 + Drift 偵測
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging
import argparse
from datetime import datetime, timezone


@dataclass
class Baseline:
    """架構基線"""
    tag: str
    timestamp: str
    phase: int
    metrics: Dict[str, Any]
    structure: Dict[str, Any]  # 目錄結構快照


@dataclass
class DriftResult:
    """Drift 偵測結果"""
    tag: str
    baseline_timestamp: str
    current_timestamp: str
    drift: Dict[str, Any]  # {metric: {baseline, current, delta, severity}}
    summary: str


class BaselineManager:
    """
    管理架構基線 + 偵測 drift
    
    使用方式：
        bm = BaselineManager(project_path)
        
        # Phase-Gate 成功後建立 baseline
        bm.capture_baseline(phase=2, metrics={...})
        
        # 檢查 drift
        result = bm.check_drift(current_metrics={...})
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.baseline_dir = self.project_path / ".methodology" / "baselines"
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        
        self.thresholds: Dict[str, float] = {
            "coverage": 0.05,    # 5% drift → alert
            "complexity": 0.10,  # 10% drift → alert
            "linter_score": 0.05,
            "architecture": 0.05,
        }
    
    def capture_baseline(self, phase: int, metrics: Dict[str, Any], tag: str = None) -> Baseline:
        """
        在 Phase-Gate 成功後建立 baseline
        
        Args:
            phase: 當前 Phase (1-8)
            metrics: 快照指標 {coverage, complexity, linter_score, ...}
            tag: 自訂標籤（預設 phase-N）
        """
        structure = self._capture_structure()
        
        baseline = Baseline(
            tag=tag or f"phase-{phase}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            phase=phase,
            metrics=metrics,
            structure=structure
        )
        
        # 儲存
        path = self.baseline_dir / f"{baseline.tag}.json"
        try:
            path.write_text(json.dumps({
                "tag": baseline.tag,
                "timestamp": baseline.timestamp,
                "phase": baseline.phase,
                "metrics": baseline.metrics,
                "structure": baseline.structure
            }, ensure_ascii=False, indent=2))
        except Exception as e:
            logging.error(f"Failed to write baseline {baseline.tag}: {e}")

        # 更新 latest
        latest_path = self.baseline_dir / "latest.json"
        try:
            latest_path.write_text(json.dumps({
                "tag": baseline.tag,
                "timestamp": baseline.timestamp,
                "phase": baseline.phase,
                "metrics": baseline.metrics,
                "structure": baseline.structure
            }, ensure_ascii=False, indent=2))
        except Exception as e:
            logging.error(f"Failed to write latest.json: {e}")
        
        return baseline
    
    def check_drift(self, current_metrics: Dict[str, Any]) -> DriftResult:
        """
        檢查與 latest baseline 的 drift
        
        Args:
            current_metrics: 當前指標
        """
        latest_path = self.baseline_dir / "latest.json"
        
        if not latest_path.exists():
            # 沒有 baseline，第一次建立
            return DriftResult(
                tag="none",
                baseline_timestamp="none",
                current_timestamp=datetime.now(timezone.utc).isoformat(),
                drift={},
                summary="No baseline found — first run"
            )
        
        try:
            with open(latest_path) as f:
                latest = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Failed to read latest.json: {e}")
            return DriftResult(
                tag="error",
                baseline_timestamp="none",
                current_timestamp=datetime.now(timezone.utc).isoformat(),
                drift={},
                summary=f"Failed to read baseline: {e}"
            )
        
        drift = {}
        for key, current_val in current_metrics.items():
            baseline_val = latest["metrics"].get(key)
            if baseline_val is None or baseline_val == 0:
                continue
            
            delta = (current_val - baseline_val) / baseline_val
            threshold = self.thresholds.get(key, 0.05)
            
            if abs(delta) > threshold:
                severity = self._calc_severity(abs(delta), threshold)
                drift[key] = {
                    "baseline": baseline_val,
                    "current": current_val,
                    "delta": delta,
                    "threshold": threshold,
                    "severity": severity
                }
        
        # 結構 drift（目錄結構）
        current_structure = self._capture_structure()
        structure_drift = self._check_structure_drift(latest["structure"], current_structure)
        if structure_drift:
            drift["structure"] = structure_drift
        
        summary = self._summarize(drift)
        
        return DriftResult(
            tag=latest["tag"],
            baseline_timestamp=latest["timestamp"],
            current_timestamp=datetime.now(timezone.utc).isoformat(),
            drift=drift,
            summary=summary
        )
    
    def _capture_structure(self) -> Dict[str, Any]:
        """捕捉當前目錄結構"""
        structure = {}
        for py_file in sorted(self.project_path.rglob("*.py")):
            if "__pycache__" in str(py_file) or ".methodology" in str(py_file):
                continue
            rel = py_file.relative_to(self.project_path)
            structure[str(rel)] = {
                "size": py_file.stat().st_size,
                "modified": py_file.stat().st_mtime
            }
        return structure
    
    def _check_structure_drift(self, baseline: Dict, current: Dict) -> Optional[Dict]:
        """檢查目錄結構 drift"""
        added = set(current.keys()) - set(baseline.keys())
        removed = set(baseline.keys()) - set(current.keys())
        
        if added or removed:
            return {"added": list(added), "removed": list(removed), "severity": "medium"}
        return None
    
    def _calc_severity(self, delta_ratio: float, threshold: float) -> str:
        """計算 drift 嚴重性"""
        ratio = delta_ratio / threshold
        if ratio > 2:
            return "critical"
        elif ratio > 1:
            return "high"
        elif ratio > 0.5:
            return "medium"
        return "low"
    
    def _summarize(self, drift: Dict) -> str:
        """產生 drift 摘要"""
        if not drift:
            return "✅ No significant drift"
        
        critical = sum(1 for d in drift.values() if d.get("severity") == "critical")
        high = sum(1 for d in drift.values() if d.get("severity") == "high")
        
        if critical > 0:
            return f"🔴 Critical drift: {critical} critical, {high} high"
        elif high > 0:
            return f"🟠 High drift: {high} high priority"
        return f"⚠️ Minor drift: {len(drift)} items"
    
    def list_baselines(self) -> List[str]:
        """列出所有 baseline"""
        return [p.stem for p in self.baseline_dir.glob("*.json") if p.stem != "latest"]
    
    def get_baseline(self, tag: str) -> Optional[Baseline]:
        """取得指定 baseline"""
        path = self.baseline_dir / f"{tag}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return Baseline(**data)


def main():
    parser = argparse.ArgumentParser(description="Baseline Manager + Drift Detector")
    parser.add_argument("--path", required=True, help="Project path")
    parser.add_argument("--capture", action="store_true", help="Capture baseline")
    parser.add_argument("--phase", type=int, help="Phase number for baseline")
    parser.add_argument("--check", action="store_true", help="Check drift")
    parser.add_argument("--tag", help="Custom tag for baseline")
    args = parser.parse_args()
    
    bm = BaselineManager(args.path)
    
    if args.capture:
        if args.phase is None:
            print("Error: --phase required when --capture is set")
            return
        # 讀取 metrics from latest baseline or use defaults
        latest = bm.get_baseline("latest") if (bm.baseline_dir / "latest.json").exists() else None
        metrics = latest.metrics if latest else {
            "coverage": 0,
            "complexity": 0,
            "linter_score": 0
        }
        baseline = bm.capture_baseline(phase=args.phase, metrics=metrics, tag=args.tag)
        print(f"✅ Baseline captured: {baseline.tag} (phase {baseline.phase})")
        print(f"   Timestamp: {baseline.timestamp}")
    
    elif args.check:
        # 嘗試讀取現有 metrics
        latest = bm.get_baseline("latest") if (bm.baseline_dir / "latest.json").exists() else None
        if latest:
            result = bm.check_drift(latest.metrics)
        else:
            result = DriftResult(
                tag="none",
                baseline_timestamp="none",
                current_timestamp=datetime.now(timezone.utc).isoformat(),
                drift={},
                summary="No baseline found — run with --capture --phase N first"
            )
        print(f"=== Drift Check ===")
        print(f"Baseline: {result.tag} ({result.baseline_timestamp})")
        print(f"Current:  {result.current_timestamp}")
        print(f"Summary:  {result.summary}")
        if result.drift:
            print(f"\nDrift Details:")
            for key, d in result.drift.items():
                if key != "structure":
                    print(f"  {key}: baseline={d['baseline']}, current={d['current']}, delta={d['delta']:.2%}, severity={d['severity']}")
                else:
                    print(f"  structure: added={d.get('added', [])}, removed={d.get('removed', [])}, severity={d['severity']}")
    else:
        baselines = bm.list_baselines()
        print(f"=== Baselines ({len(baselines)} found) ===")
        for tag in baselines:
            b = bm.get_baseline(tag)
            if b:
                print(f"  {b.tag} — phase {b.phase} — {b.timestamp}")


if __name__ == "__main__":
    main()
