#!/usr/bin/env python3
"""
ADR Registry
============
ADR 的持久化和管理
"""

import json
import uuid
from pathlib import Path
from typing import List, Optional
from .adr import ADR, ADRRecord

class ADRRegistry:
    """
    ADR 登記處
    
    使用方式：
    
    ```python
    registry = ADRRegistry()
    
    # 創建 ADR
    adr = ADR(
        title="使用 PostgreSQL",
        context="需要關聯式資料庫",
        decision="選擇 PostgreSQL 15",
        consequences="需要管理基礎設施"
    )
    
    adr_id = registry.save(adr)
    
    # 列出所有
    for adr in registry.list_all():
        print(f"ADR-{adr.id}: {adr.title}")
    
    # 查詢單一
    adr = registry.get("001")
    
    # 導出 Markdown
    registry.export_markdown("docs/adr/")
    ```
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.adr_dir = self.project_path / ".methodology" / "decisions"
        self.adr_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.adr_dir / "adr_index.json"
        
        if not self.index_file.exists():
            self._write_index({})
    
    def _read_index(self) -> dict:
        return json.loads(self.index_file.read_text())
    
    def _write_index(self, index: dict):
        self.index_file.write_text(json.dumps(index, indent=2))
    
    def _next_id(self) -> str:
        """產生下一個 ADR ID"""
        index = self._read_index()
        if not index:
            return "001"
        
        max_id = max(int(k) for k in index.keys())
        return f"{max_id + 1:03d}"
    
    def save(self, adr: ADR) -> str:
        """保存 ADR"""
        adr_id = self._next_id()
        adr.adr_id = adr_id
        
        # 保存到 index
        index = self._read_index()
        index[adr_id] = {
            "title": adr.title,
            "status": adr.status,
            "created_at": adr.created_at
        }
        self._write_index(index)
        
        # 保存 ADR 內容
        adr_file = self.adr_dir / f"adr-{adr_id}.json"
        with open(adr_file, 'w') as f:
            json.dump({
                "id": adr.adr_id,
                "title": adr.title,
                "status": adr.status,
                "context": adr.context,
                "decision": adr.decision,
                "consequences": adr.consequences,
                "alternatives": adr.alternatives,
                "related_decisions": adr.related_decisions,
                "created_by": adr.created_by,
                "created_at": adr.created_at
            }, f, indent=2)
        
        return adr_id
    
    def get(self, adr_id: str) -> Optional[ADRRecord]:
        """取得 ADR"""
        adr_file = self.adr_dir / f"adr-{adr_id}.json"
        if not adr_file.exists():
            return None
        
        with open(adr_file) as f:
            data = json.load(f)
        
        return ADRRecord(**data)
    
    def list_all(self) -> List[ADRRecord]:
        """列出所有 ADR"""
        index = self._read_index()
        results = []
        
        for adr_id in sorted(index.keys()):
            adr = self.get(adr_id)
            if adr:
                results.append(adr)
        
        return results
    
    def list_by_status(self, status: str) -> List[ADRRecord]:
        """按狀態篩選"""
        return [adr for adr in self.list_all() if adr.status == status]
    
    def update_status(self, adr_id: str, new_status: str) -> bool:
        """更新 ADR 狀態"""
        adr_file = self.adr_dir / f"adr-{adr_id}.json"
        if not adr_file.exists():
            return False
        
        with open(adr_file) as f:
            data = json.load(f)
        
        data["status"] = new_status
        
        with open(adr_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # 更新 index
        index = self._read_index()
        if adr_id in index:
            index[adr_id]["status"] = new_status
            self._write_index(index)
        
        return True
    
    def export_markdown(self, output_dir: str) -> int:
        """導出所有 ADR 為 Markdown"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for adr in self.list_all():
            md = adr.to_markdown()
            md_file = output_path / f"adr-{adr.id}.md"
            md_file.write_text(md)
            count += 1
        
        return count
    
    def generate_report(self) -> str:
        """生成 ADR 報告"""
        all_adr = self.list_all()
        
        report = ["# Architecture Decision Records Report\n"]
        report.append(f"Total ADRs: {len(all_adr)}\n")
        
        by_status = {}
        for adr in all_adr:
            if adr.status not in by_status:
                by_status[adr.status] = []
            by_status[adr.status].append(adr)
        
        for status, adrs in sorted(by_status.items()):
            report.append(f"\n## {status.upper()} ({len(adrs)})")
            for adr in adrs:
                report.append(f"- ADR-{adr.id}: {adr.title}")
        
        return "\n".join(report)