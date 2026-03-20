#!/usr/bin/env python3
"""
Data Quality Connector

提供：
- 輸入資料驗證
- 異常資料偵測
- 資料品質儀表板
- 自動清理建議
"""

import statistics
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from datetime import datetime
from collections import Counter


class QualityLevel(Enum):
    """品質等級"""
    EXCELLENT = "excellent"   # 95-100%
    GOOD = "good"            # 80-94%
    FAIR = "fair"            # 60-79%
    POOR = "poor"            # 40-59%
    BAD = "bad"              # 0-39%


class IssueType(Enum):
    """問題類型"""
    MISSING_VALUE = "missing_value"
    INVALID_FORMAT = "invalid_format"
    OUTLIER = "outlier"
    DUPLICATE = "duplicate"
    INCONSISTENT = "inconsistent"
    TYPE_MISMATCH = "type_mismatch"
    LENGTH_ERROR = "length_error"
    RANGE_ERROR = "range_error"


@dataclass
class QualityIssue:
    """品質問題"""
    issue_type: IssueType
    field: str
    row_index: int = None
    value: Any = None
    expected: str = None
    severity: str = "error"  # error, warning, info
    suggestion: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "type": self.issue_type.value,
            "field": self.field,
            "row": self.row_index,
            "value": str(self.value)[:100] if self.value else None,
            "expected": self.expected,
            "severity": self.severity,
            "suggestion": self.suggestion
        }


@dataclass
class FieldProfile:
    """欄位統計"""
    name: str
    field_type: type = None
    
    # 基本統計
    total_count: int = 0
    null_count: int = 0
    unique_count: int = 0
    
    # 數值統計
    min_value: float = None
    max_value: float = None
    mean_value: float = None
    median_value: float = None
    std_dev: float = None
    
    # 字串統計
    min_length: int = None
    max_length: int = None
    avg_length: float = None
    patterns: List[str] = field(default_factory=list)
    
    # 枚舉值
    top_values: List[Tuple[Any, int]] = field(default_factory=list)
    
    # 品質
    completeness: float = 0.0  # 非空比例
    consistency_score: float = 0.0  # 一致性分數
    
    def calculate_quality(self) -> float:
        """計算品質分數"""
        if self.total_count == 0:
            return 0.0
        
        score = self.completeness * 100
        
        # 一致性加成
        score += self.consistency_score * 10
        
        return min(100, max(0, score))
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.field_type.__name__ if self.field_type else None,
            "total": self.total_count,
            "null": self.null_count,
            "unique": self.unique_count,
            "completeness": f"{self.completeness*100:.1f}%",
            "quality_score": f"{self.calculate_quality():.1f}%",
            "min": self.min_value,
            "max": self.max_value,
            "mean": self.mean_value,
            "top_values": [(str(k), v) for k, v in self.top_values[:5]]
        }


@dataclass
class QualityReport:
    """品質報告"""
    timestamp: datetime = field(default_factory=datetime.now)
    total_rows: int = 0
    total_fields: int = 0
    
    # 欄位統計
    field_profiles: Dict[str, FieldProfile] = field(default_factory=dict)
    
    # 問題
    issues: List[QualityIssue] = field(default_factory=list)
    
    # 整體分數
    overall_quality: float = 0.0
    quality_level: QualityLevel = QualityLevel.GOOD
    
    # 建議
    recommendations: List[str] = field(default_factory=list)
    
    def add_issue(self, issue: QualityIssue):
        self.issues.append(issue)
    
    def get_issues_by_field(self, field: str) -> List[QualityIssue]:
        return [i for i in self.issues if i.field == field]
    
    def get_issues_by_type(self, issue_type: IssueType) -> List[QualityIssue]:
        return [i for i in self.issues if i.issue_type == issue_type]
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_rows": self.total_rows,
            "total_fields": self.total_fields,
            "overall_quality": f"{self.overall_quality:.1f}%",
            "quality_level": self.quality_level.value,
            "issues_count": len(self.issues),
            "field_profiles": {k: v.to_dict() for k, v in self.field_profiles.items()},
            "recommendations": self.recommendations
        }


class DataQualityChecker:
    """資料品質檢查器"""
    
    def __init__(self):
        self.reports: List[QualityReport] = []
        self.validation_rules: Dict[str, Callable] = {}
        self._register_default_rules()
    
    def _register_default_rules(self):
        """註冊預設驗證規則"""
        # Email 格式
        self.register_rule("email", lambda v: 
            v is None or re.match(r'^[\w.-]+@[\w.-]+\.\w+$', str(v))
        )
        
        # URL 格式
        self.register_rule("url", lambda v:
            v is None or re.match(r'^https?://[\w.-]+\.\w+', str(v))
        )
        
        # Phone 格式
        self.register_rule("phone", lambda v:
            v is None or re.match(r'^[\d\s\-\+\(\)]+$', str(v))
        )
        
        # Positive number
        self.register_rule("positive", lambda v:
            v is None or (isinstance(v, (int, float)) and v >= 0)
        )
        
        # Percentage
        self.register_rule("percentage", lambda v:
            v is None or (isinstance(v, (int, float)) and 0 <= v <= 100)
        )
    
    def register_rule(self, name: str, validator: Callable):
        """註冊自訂驗證規則"""
        self.validation_rules[name] = validator
    
    def analyze(
        self,
        data: List[Dict],
        field_types: Dict[str, type] = None
    ) -> QualityReport:
        """分析資料品質"""
        report = QualityReport()
        
        if not data:
            return report
        
        report.total_rows = len(data)
        
        # 取得所有欄位
        all_fields = set()
        for row in data:
            all_fields.update(row.keys())
        
        report.total_fields = len(all_fields)
        
        # 分析每個欄位
        for field_name in all_fields:
            values = [row.get(field_name) for row in data]
            profile = self._analyze_field(
                field_name, 
                values, 
                field_types.get(field_name) if field_types else None
            )
            report.field_profiles[field_name] = profile
        
        # 偵測問題
        report = self._detect_issues(data, report)
        
        # 計算整體分數
        report.overall_quality = self._calculate_overall_quality(report)
        report.quality_level = self._get_quality_level(report.overall_quality)
        
        # 生成建議
        report.recommendations = self._generate_recommendations(report)
        
        self.reports.append(report)
        return report
    
    def _analyze_field(self, name: str, values: List[Any], field_type: type = None) -> FieldProfile:
        """分析單一欄位"""
        profile = FieldProfile(name=name, field_type=field_type)
        
        # 基本統計
        non_null = [v for v in values if v is not None and v != ""]
        profile.total_count = len(values)
        profile.null_count = len(values) - len(non_null)
        profile.unique_count = len(set(non_null)) if non_null else 0
        profile.completeness = len(non_null) / profile.total_count if profile.total_count > 0 else 0
        
        if not non_null:
            return profile
        
        # 根據類型分析
        try:
            numeric_values = [float(v) for v in non_null if self._is_numeric(v)]
            if len(numeric_values) == len(non_null):
                # 數值欄位
                profile.min_value = min(numeric_values)
                profile.max_value = max(numeric_values)
                profile.mean_value = statistics.mean(numeric_values)
                profile.median_value = statistics.median(numeric_values)
                if len(numeric_values) > 1:
                    profile.std_dev = statistics.stdev(numeric_values)
            else:
                # 字串欄位
                str_values = [str(v) for v in non_null]
                lengths = [len(s) for s in str_values]
                profile.min_length = min(lengths)
                profile.max_length = max(lengths)
                profile.avg_length = statistics.mean(lengths)
                
                # 最常見的值
                counter = Counter(str_values)
                profile.top_values = counter.most_common(5)
                
                # 常見模式
                patterns = self._extract_patterns(str_values)
                profile.patterns = patterns[:3]
        except:
            pass
        
        # 一致性分數
        if profile.unique_count == 1 and profile.total_count > 1:
            profile.consistency_score = 1.0
        elif profile.unique_count <= profile.total_count * 0.1:
            profile.consistency_score = 0.8
        else:
            profile.consistency_score = 0.5
        
        return profile
    
    def _is_numeric(self, v: Any) -> bool:
        """檢查是否為數值"""
        try:
            float(v)
            return True
        except:
            return False
    
    def _extract_patterns(self, values: List[str]) -> List[str]:
        """提取常見模式"""
        patterns = []
        for v in values[:100]:  # 只看前100個
            # Email pattern
            if re.match(r'^[\w.-]+@[\w.-]+\.\w+$', v):
                patterns.append("email")
            # URL pattern
            elif re.match(r'^https?://', v):
                patterns.append("url")
            # Date pattern
            elif re.match(r'^\d{4}-\d{2}-\d{2}', v):
                patterns.append("date")
            # Phone pattern
            elif re.match(r'^[\d\s\-\+\(\)]+$', v) and len(v) > 7:
                patterns.append("phone")
            # ID pattern
            elif re.match(r'^[a-zA-Z0-9_-]+$', v) and len(v) < 20:
                patterns.append("id")
        
        return list(set(patterns))
    
    def _detect_issues(
        self, 
        data: List[Dict], 
        report: QualityReport
    ) -> QualityReport:
        """偵測資料問題"""
        
        for field_name, profile in report.field_profiles.items():
            for i, row in enumerate(data):
                value = row.get(field_name)
                
                # Missing value
                if value is None or value == "":
                    issue = QualityIssue(
                        issue_type=IssueType.MISSING_VALUE,
                        field=field_name,
                        row_index=i,
                        value=value,
                        severity="error",
                        suggestion=f"Fill in the missing {field_name}"
                    )
                    report.add_issue(issue)
                    continue
                
                # Outlier detection (for numeric)
                if self._is_numeric(value):
                    if profile.mean_value and profile.std_dev:
                        z_score = abs((float(value) - profile.mean_value) / profile.std_dev)
                        if z_score > 3:  # 3 standard deviations
                            issue = QualityIssue(
                                issue_type=IssueType.OUTLIER,
                                field=field_name,
                                row_index=i,
                                value=value,
                                expected=f"Expected range: {profile.mean_value - 3*profile.std_dev:.2f} to {profile.mean_value + 3*profile.std_dev:.2f}",
                                severity="warning",
                                suggestion="Consider reviewing this outlier value"
                            )
                            report.add_issue(issue)
        
        # Duplicate detection
        seen = set()
        for i, row in enumerate(data):
            row_key = json.dumps(row, sort_keys=True)
            if row_key in seen:
                issue = QualityIssue(
                    issue_type=IssueType.DUPLICATE,
                    field="*",
                    row_index=i,
                    value=row_key[:100],
                    severity="warning",
                    suggestion="Remove duplicate row"
                )
                report.add_issue(issue)
            seen.add(row_key)
        
        return report
    
    def _calculate_overall_quality(self, report: QualityReport) -> float:
        """計算整體品質分數"""
        if not report.field_profiles:
            return 0.0
        
        # 平均欄位品質
        field_scores = [p.calculate_quality() for p in report.field_profiles.values()]
        avg_quality = statistics.mean(field_scores)
        
        # 根據問題數調整
        error_count = len([i for i in report.issues if i.severity == "error"])
        warning_count = len([i for i in report.issues if i.severity == "warning"])
        
        penalty = (error_count * 5) + (warning_count * 1)
        
        return max(0, avg_quality - penalty)
    
    def _get_quality_level(self, score: float) -> QualityLevel:
        """取得品質等級"""
        if score >= 95:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 60:
            return QualityLevel.FAIR
        elif score >= 40:
            return QualityLevel.POOR
        else:
            return QualityLevel.BAD
    
    def _generate_recommendations(self, report: QualityReport) -> List[str]:
        """生成改善建議"""
        recommendations = []
        
        # 根據問題生成建議
        issue_types = Counter([i.issue_type for i in report.issues])
        
        if IssueType.MISSING_VALUE in issue_types:
            count = issue_types[IssueType.MISSING_VALUE]
            recommendations.append(f"Fill in {count} missing values or use default values")
        
        if IssueType.OUTLIER in issue_types:
            recommendations.append("Review and handle outlier values in numeric fields")
        
        if IssueType.DUPLICATE in issue_types:
            recommendations.append("Remove duplicate rows to improve data integrity")
        
        # 根據品質等級建議
        if report.quality_level in [QualityLevel.POOR, QualityLevel.BAD]:
            recommendations.append("Consider re-collecting data with better validation")
        
        if report.quality_level == QualityLevel.EXCELLENT:
            recommendations.append("✅ Data quality is excellent! Maintain current standards.")
        
        return recommendations
    
    def clean_data(
        self,
        data: List[Dict],
        strategy: str = "remove"  # remove, fill_null, fill_default
    ) -> Tuple[List[Dict], QualityReport]:
        """清理資料"""
        report = self.analyze(data)
        
        if strategy == "remove":
            # 移除有問題的行
            problem_rows = set()
            for issue in report.issues:
                if issue.row_index is not None:
                    problem_rows.add(issue.row_index)
            
            cleaned = [row for i, row in enumerate(data) if i not in problem_rows]
        
        elif strategy == "fill_null":
            # 用 null 填補
            cleaned = data.copy()
            for issue in report.issues:
                if issue.row_index is not None and issue.field != "*":
                    cleaned[issue.row_index][issue.field] = None
        
        else:
            cleaned = data
        
        return cleaned, report
    
    def generate_report_markdown(self, report: QualityReport) -> str:
        """產生 Markdown 報告"""
        lines = []
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + " 📊 Data Quality Report ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")
        
        lines.append(f"**Timestamp**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Rows**: {report.total_rows}")
        lines.append(f"**Total Fields**: {report.total_fields}")
        lines.append("")
        
        # 品質等級
        level_icon = {
            QualityLevel.EXCELLENT: "🟢",
            QualityLevel.GOOD: "🟢",
            QualityLevel.FAIR: "🟡",
            QualityLevel.POOR: "🟠",
            QualityLevel.BAD: "🔴"
        }
        lines.append(f"**Overall Quality**: {level_icon.get(report.quality_level, '⚪')} {report.overall_quality:.1f}%")
        lines.append(f"**Quality Level**: {report.quality_level.value.upper()}")
        lines.append("")
        
        # 欄位品質
        lines.append("## 📋 Field Profiles")
        lines.append("")
        lines.append("| Field | Type | Completeness | Quality | Issues |")
        lines.append("|-------|------|-------------|---------|--------|")
        
        for name, profile in report.field_profiles.items():
            issues_count = len(report.get_issues_by_field(name))
            lines.append(
                f"| {name} | {profile.field_type.__name__ if profile.field_type else 'unknown'} | "
                f"{profile.completeness*100:.0f}% | {profile.calculate_quality():.0f}% | {issues_count} |"
            )
        lines.append("")
        
        # 問題摘要
        if report.issues:
            lines.append("## 🔍 Issues Summary")
            lines.append("")
            
            by_type = Counter([i.issue_type for i in report.issues])
            for issue_type, count in by_type.most_common():
                lines.append(f"- **{issue_type.value}**: {count}")
            lines.append("")
        
        # 建議
        if report.recommendations:
            lines.append("## 💡 Recommendations")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)


# ==================== Main ====================

if __name__ == "__main__":
    import json
    
    print("Data Quality Connector")
    print("=" * 50)
    print()
    
    # 建立檢查器
    checker = DataQualityChecker()
    
    # 測試資料
    test_data = [
        {"id": 1, "name": "Alice", "email": "alice@test.com", "age": 30, "score": 85},
        {"id": 2, "name": "Bob", "email": "bob@test.com", "age": 25, "score": 92},
        {"id": 3, "name": "Charlie", "email": "invalid-email", "age": 35, "score": 78},
        {"id": 4, "name": "Diana", "email": "diana@test.com", "age": 28, "score": 95},
        {"id": 5, "name": "", "email": "eve@test.com", "age": None, "score": 88},  # Issues
        {"id": 6, "name": "Frank", "email": "frank@test.com", "age": 150, "score": 70},  # Outlier
        {"id": 7, "name": "Grace", "email": "grace@test.com", "age": 32, "score": 90},
    ]
    
    field_types = {
        "id": int,
        "name": str,
        "email": str,
        "age": int,
        "score": int
    }
    
    # 分析
    print("## Analyzing Data Quality...")
    report = checker.analyze(test_data, field_types)
    
    # 產生報告
    print(checker.generate_report_markdown(report))
    
    # 清理
    print("\n## Cleaning Data...")
    cleaned, clean_report = checker.clean_data(test_data, strategy="remove")
    print(f"Original rows: {len(test_data)}")
    print(f"Cleaned rows: {len(cleaned)}")
    print(f"Removed: {len(test_data) - len(cleaned)}")
