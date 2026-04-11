#!/usr/bin/env python3
"""
Requirement Traceability - 需求可追溯性模組

為 methodology-v2 提供完整的 FR → SRS → Code → Test 雙向追溯能力。

HARNESS v1.0/v2.0 合規：
- FR ↔ SRS 雙向映射
- SRS ↔ Code 雙向映射
- Code ↔ Test 雙向映射
- 自動完整性驗證
- ASPICE SWE.3 / SYS.4 合規

使用方式：
    from requirement_traceability import RequirementTraceability
    
    rt = RequirementTraceability(project_id="my-project")
    rt.add_requirement("FR-01", "用戶登錄", "SRS.md §2.1")
    rt.add_implementation("FR-01", "src/auth.py", "auth/login")
    rt.add_test("FR-01", "tests/test_auth.py", "test_login")
    
    # 驗證完整性
    report = rt.verify_completeness()
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import json
import uuid


class TraceStatus(Enum):
    """追溯狀態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    NOT_IMPLEMENTED = "not_implemented"


class LinkType(Enum):
    """追溯鏈接類型"""
    FR_TO_SRS = "fr→srs"
    SRS_TO_CODE = "srs→code"
    CODE_TO_TEST = "code→test"
    TEST_TO_QUALITY = "test→quality"
    QUALITY_TO_AUDIT = "quality→audit"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class Requirement:
    """需求項目"""
    req_id: str  # e.g., "FR-01", "NFR-01"
    title: str
    description: str
    priority: str = "HIGH"  # HIGH, MEDIUM, LOW
    status: TraceStatus = TraceStatus.PENDING
    srs_section: Optional[str] = None  # e.g., "§2.1"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "req_id": self.req_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status.value,
            "srs_section": self.srs_section,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class CodeComponent:
    """代碼組件"""
    file_path: str
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    line_range: Optional[str] = None  # "1-100"
    fr_id: Optional[str] = None
    test_files: List[str] = field(default_factory=list)
    coverage: Optional[float] = None  # 0.0 - 1.0
    
    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "functions": self.functions,
            "classes": self.classes,
            "line_range": self.line_range,
            "fr_id": self.fr_id,
            "test_files": self.test_files,
            "coverage": self.coverage
        }


@dataclass
class TestCoverage:
    """測試覆蓋"""
    test_file: str
    test_functions: List[str] = field(default_factory=list)
    fr_id: Optional[str] = None
    coverage_percentage: float = 0.0
    status: TraceStatus = TraceStatus.PENDING
    
    def to_dict(self) -> dict:
        return {
            "test_file": self.test_file,
            "test_functions": self.test_functions,
            "fr_id": self.fr_id,
            "coverage_percentage": self.coverage_percentage,
            "status": self.status.value
        }


@dataclass
class TraceLink:
    """追溯鏈接"""
    link_id: str
    source_type: str  # "fr", "srs", "code", "test", "quality", "audit"
    source_id: str
    target_type: str
    target_id: str
    link_type: LinkType = LinkType.FR_TO_SRS
    bidirectional: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    status: TraceStatus = TraceStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "link_id": self.link_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "link_type": self.link_type.value,
            "bidirectional": self.bidirectional,
            "created_at": self.created_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "status": self.status.value,
            "metadata": self.metadata
        }


class RequirementTraceability:
    """
    需求可追溯性管理器
    
    提供 FR → SRS → Code → Test 完整雙向追溯能力
    """
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.requirements: Dict[str, Requirement] = {}
        self.code_components: Dict[str, CodeComponent] = {}  # key = file_path
        self.test_coverage: Dict[str, TestCoverage] = {}  # key = test_file
        self.links: List[TraceLink] = []
        self._link_index: Dict[str, List[str]] = {}  # req_id → [link_ids]
        
    # ========== Requirement Management ==========
    
    def add_requirement(
        self,
        req_id: str,
        title: str,
        description: str,
        srs_section: Optional[str] = None,
        priority: str = "HIGH",
        metadata: Optional[Dict] = None
    ) -> Requirement:
        """新增需求"""
        req = Requirement(
            req_id=req_id,
            title=title,
            description=description,
            srs_section=srs_section,
            priority=priority,
            metadata=metadata or {}
        )
        self.requirements[req_id] = req
        return req
    
    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        """獲取需求"""
        return self.requirements.get(req_id)
    
    def list_requirements(self, status: Optional[TraceStatus] = None) -> List[Requirement]:
        """列出需求"""
        if status:
            return [r for r in self.requirements.values() if r.status == status]
        return list(self.requirements.values())
    
    # ========== Code Component Management ==========
    
    def add_code_component(
        self,
        file_path: str,
        fr_id: Optional[str] = None,
        functions: Optional[List[str]] = None,
        classes: Optional[List[str]] = None,
        line_range: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> CodeComponent:
        """新增代碼組件"""
        component = CodeComponent(
            file_path=file_path,
            fr_id=fr_id,
            functions=functions or [],
            classes=classes or [],
            line_range=line_range,
            metadata=metadata or {}
        )
        self.code_components[file_path] = component
        
        # 如果有 FR 關聯，自動建立鏈接
        if fr_id:
            self._auto_link_fr_to_code(fr_id, file_path)
        
        return component
    
    def link_code_to_test(self, file_path: str, test_file: str) -> Optional[TraceLink]:
        """建立 Code → Test 鏈接"""
        if file_path not in self.code_components:
            return None
        
        self.code_components[file_path].test_files.append(test_file)
        
        return self.add_link(
            source_type="code",
            source_id=file_path,
            target_type="test",
            target_id=test_file,
            link_type=LinkType.CODE_TO_TEST
        )
    
    def _auto_link_fr_to_code(self, fr_id: str, file_path: str) -> TraceLink:
        """自動建立 FR → Code 鏈接"""
        return self.add_link(
            source_type="fr",
            source_id=fr_id,
            target_type="code",
            target_id=file_path,
            link_type=LinkType.SRS_TO_CODE
        )
    
    # ========== Test Coverage Management ==========
    
    def add_test_coverage(
        self,
        test_file: str,
        fr_id: Optional[str] = None,
        test_functions: Optional[List[str]] = None,
        coverage_percentage: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> TestCoverage:
        """新增測試覆蓋"""
        coverage = TestCoverage(
            test_file=test_file,
            fr_id=fr_id,
            test_functions=test_functions or [],
            coverage_percentage=coverage_percentage,
            metadata=metadata or {}
        )
        self.test_coverage[test_file] = coverage
        
        # 如果有 FR 關聯，自動建立鏈接
        if fr_id:
            self.add_link(
                source_type="fr",
                source_id=fr_id,
                target_type="test",
                target_id=test_file,
                link_type=LinkType.CODE_TO_TEST
            )
        
        return coverage
    
    # ========== Link Management ==========
    
    def add_link(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        link_type: LinkType = LinkType.FR_TO_SRS,
        bidirectional: bool = True,
        metadata: Optional[Dict] = None
    ) -> TraceLink:
        """新增追溯鏈接"""
        link_id = str(uuid.uuid4())[:8]
        
        link = TraceLink(
            link_id=link_id,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            link_type=link_type,
            bidirectional=bidirectional,
            metadata=metadata or {}
        )
        
        self.links.append(link)
        
        # 建立索引
        for req_id in [source_id, target_id]:
            if req_id.startswith("FR-") or req_id.startswith("NFR-"):
                if req_id not in self._link_index:
                    self._link_index[req_id] = []
                self._link_index[req_id].append(link_id)
        
        return link
    
    def get_links_for_requirement(self, req_id: str) -> List[TraceLink]:
        """獲取某需求的所有鏈接"""
        link_ids = self._link_index.get(req_id, [])
        return [l for l in self.links if l.link_id in link_ids]
    
    def get_downstream(self, req_id: str) -> Dict[str, List[str]]:
        """獲取下游組件（FR → SRS → Code → Test）"""
        downstream = {
            "srs": [],
            "code": [],
            "test": [],
            "quality": []
        }
        
        for link in self.links:
            if link.source_id == req_id or link.source_id == f"FR-{req_id}":
                if link.target_type == "srs":
                    downstream["srs"].append(link.target_id)
                elif link.target_type == "code":
                    downstream["code"].append(link.target_id)
                elif link.target_type == "test":
                    downstream["test"].append(link.target_id)
                elif link.target_type == "quality":
                    downstream["quality"].append(link.target_id)
        
        return downstream
    
    def get_upstream(self, component_id: str) -> Dict[str, List[str]]:
        """獲取上游組件"""
        upstream = {
            "fr": [],
            "srs": [],
            "code": [],
            "test": []
        }
        
        for link in self.links:
            if link.target_id == component_id:
                if link.source_type == "fr":
                    upstream["fr"].append(link.source_id)
                elif link.source_type == "srs":
                    upstream["srs"].append(link.source_id)
                elif link.source_type == "code":
                    upstream["code"].append(link.source_id)
        
        return upstream
    
    # ========== Verification ==========
    
    def mark_verified(self, req_id: str, verifier: str = "system") -> bool:
        """標記為已驗證"""
        if req_id in self.requirements:
            self.requirements[req_id].status = TraceStatus.VERIFIED
            return True
        return False
    
    def verify_completeness(self) -> Dict[str, Any]:
        """驗證追溯完整性"""
        total_frs = len(self.requirements)
        
        # 計算各類型的覆蓋
        frs_with_srs = set()
        frs_with_code = set()
        frs_with_test = set()
        verified_frs = set()
        
        for link in self.links:
            if link.source_type == "fr":
                if link.target_type == "srs":
                    frs_with_srs.add(link.source_id)
                elif link.target_type == "code":
                    frs_with_code.add(link.source_id)
                elif link.target_type == "test":
                    frs_with_test.add(link.source_id)
        
        for req in self.requirements.values():
            if req.status == TraceStatus.VERIFIED:
                verified_frs.add(req.req_id)
        
        # 計算覆蓋率
        srs_coverage = len(frs_with_srs) / total_frs if total_frs > 0 else 0
        code_coverage = len(frs_with_code) / total_frs if total_frs > 0 else 0
        test_coverage = len(frs_with_test) / total_frs if total_frs > 0 else 0
        verification_rate = len(verified_frs) / total_frs if total_frs > 0 else 0
        
        return {
            "total_requirements": total_frs,
            "frs_with_srs_mapping": len(frs_with_srs),
            "frs_with_code_implementation": len(frs_with_code),
            "frs_with_test_coverage": len(frs_with_test),
            "frs_verified": len(verified_frs),
            "srs_coverage": f"{srs_coverage * 100:.1f}%",
            "code_coverage": f"{code_coverage * 100:.1f}%",
            "test_coverage": f"{test_coverage * 100:.1f}%",
            "verification_rate": f"{verification_rate * 100:.1f}%",
            "overall_completeness": f"{((srs_coverage + code_coverage + test_coverage) / 3) * 100:.1f}%",
            "total_links": len(self.links),
            "missing_mappings": {
                "fr_without_srs": list(set(self.requirements.keys()) - frs_with_srs),
                "fr_without_code": list(set(self.requirements.keys()) - frs_with_code),
                "fr_without_test": list(set(self.requirements.keys()) - frs_with_test),
            }
        }
    
    def get_traceability_matrix(self) -> List[Dict[str, Any]]:
        """生成追溯矩陣"""
        matrix = []
        
        for req_id, req in sorted(self.requirements.items()):
            downstream = self.get_downstream(req_id)
            
            matrix.append({
                "requirement_id": req_id,
                "title": req.title,
                "priority": req.priority,
                "status": req.status.value,
                "srs_section": req.srs_section,
                "code_files": downstream["code"],
                "test_files": downstream["test"],
                "links_count": len(self._link_index.get(req_id, []))
            })
        
        return matrix
    
    # ========== Export ==========
    
    def export_report(self, format: str = "standard") -> Dict[str, Any]:
        """匯出報告"""
        completeness = self.verify_completeness()
        matrix = self.get_traceability_matrix()
        
        report = {
            "project_id": self.project_id,
            "exported_at": datetime.now().isoformat(),
            "completeness": completeness,
            "traceability_matrix": matrix,
            "all_links": [l.to_dict() for l in self.links],
            "requirements": [r.to_dict() for r in self.requirements.values()],
            "code_components": [c.to_dict() for c in self.code_components.values()],
            "test_coverage": [t.to_dict() for t in self.test_coverage.values()]
        }
        
        if format == "aspice":
            report["aspice_compliance"] = {
                "SWE_3_B_SP1": completeness["srs_coverage"] == "100.0%",
                "SWE_3_B_SP2": completeness["code_coverage"] == "100.0%",
                "SWE_3_B_SP3": completeness["test_coverage"] == "100.0%",
                "all_requirements_traced": completeness["overall_completeness"] == "100.0%"
            }
        
        return report
    
    def save(self, filepath: str) -> None:
        """保存到文件"""
        report = self.export_report()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filepath: str) -> "RequirementTraceability":
        """從文件加載"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        rt = cls(project_id=data["project_id"])
        
        # 恢復 requirements
        for req_data in data.get("requirements", []):
            req = Requirement(
                req_id=req_data["req_id"],
                title=req_data["title"],
                description=req_data["description"],
                priority=req_data.get("priority", "HIGH"),
                status=TraceStatus(req_data.get("status", "pending")),
                srs_section=req_data.get("srs_section")
            )
            rt.requirements[req.req_id] = req
        
        # 恢復 links
        for link_data in data.get("all_links", []):
            link = TraceLink(
                link_id=link_data["link_id"],
                source_type=link_data["source_type"],
                source_id=link_data["source_id"],
                target_type=link_data["target_type"],
                target_id=link_data["target_id"],
                link_type=LinkType(link_data.get("link_type", "fr→srs")),
                status=TraceStatus(link_data.get("status", "pending"))
            )
            rt.links.append(link)
            
            # 重建索引
            for req_id in [link.source_id, link.target_id]:
                if req_id.startswith("FR-") or req_id.startswith("NFR-"):
                    if req_id not in rt._link_index:
                        rt._link_index[req_id] = []
                    rt._link_index[req_id].append(link.link_id)
        
        return rt


# ========== CLI Interface ==========

def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Requirement Traceability Manager")
    parser.add_argument("--project-id", required=True, help="項目 ID")
    parser.add_argument("--add-fr", help="新增 FR (格式: FR-01,Title,Description)")
    parser.add_argument("--link", help="建立鏈接 (格式: fr,FR-01,code,src/auth.py)")
    parser.add_argument("--verify", action="store_true", help="驗證完整性")
    parser.add_argument("--export", help="匯出報告到文件")
    parser.add_argument("--format", default="standard", choices=["standard", "aspice"])
    
    args = parser.parse_args()
    
    rt = RequirementTraceability(args.project_id)
    
    if args.add_fr:
        parts = args.add_fr.split(",")
        if len(parts) >= 3:
            rt.add_requirement(parts[0], parts[1], parts[2])
    
    if args.link:
        parts = args.link.split(",")
        if len(parts) >= 4:
            rt.add_link(parts[0], parts[1], parts[2], parts[3])
    
    if args.verify:
        result = rt.verify_completeness()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if args.export:
        report = rt.export_report(format=args.format)
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to {args.export}")


if __name__ == "__main__":
    main()
