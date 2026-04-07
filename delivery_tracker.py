#!/usr/bin/env python3
"""
Version Control - 版本控制與 Rollback

為 Agent 產出提供版本控制和回滾能力
"""

import json
import os
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Version:
    """版本"""
    version_id: str
    artifact_id: str
    
    # 版本號
    major: int = 0
    minor: int = 0
    patch: int = 0
    
    # 內容
    content: str = ""
    content_hash: str = ""
    content_size: int = 0
    
    # 元數據
    author: str = "system"
    message: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 時間
    created_at: datetime = field(default_factory=datetime.now)
    
    # 狀態
    status: str = "active"  # active, archived, deleted
    
    def __str__(self):
        return f"v{self.major}.{self.minor}.{self.patch}"
    
    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "artifact_id": self.artifact_id,
            "version": str(self),
            "content_hash": self.content_hash,
            "author": self.author,
            "message": self.message,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


@dataclass
class RollbackPoint:
    """回滾點"""
    id: str
    artifact_id: str
    from_version: str
    to_version: str
    reason: str
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"


@dataclass
class Artifact:
    """產出物"""
    id: str
    name: str
    type: str  # code, document, config, etc.
    current_version: Version
    versions: List[Version] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_version(self, version: Version):
        """新增版本"""
        self.versions.append(version)
        self.current_version = version
        self.updated_at = datetime.now()


class DeliveryTracker:
    """版本控制管理器"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "~/.methodology/versions"
        self.storage_path = os.path.expanduser(self.storage_path)
        
        # 內存緩存
        self.artifacts: Dict[str, Artifact] = {}
        self.versions: Dict[str, List[Version]] = {}
        self.rollback_history: List[RollbackPoint] = []
        
        # 確保目錄存在
        os.makedirs(self.storage_path, exist_ok=True)
    
    def register_artifact(self, artifact_id: str, name: str,
                          type: str = "unknown") -> Artifact:
        """
        注册產出物
        
        Args:
            artifact_id: 產出物 ID
            name: 名稱
            type: 類型
            
        Returns:
            Artifact 實例
        """
        if artifact_id in self.artifacts:
            return self.artifacts[artifact_id]
        
        artifact = Artifact(
            id=artifact_id,
            name=name,
            type=type,
            current_version=Version(
                version_id=f"{artifact_id}-v0.0.0",
                artifact_id=artifact_id,
            )
        )
        
        self.artifacts[artifact_id] = artifact
        self.versions[artifact_id] = []
        
        return artifact
    
    def commit(self, artifact_id: str, content: str,
              author: str = "system",
              message: str = "",
              tags: List[str] = None) -> Version:
        """
        提交新版本
        
        Args:
            artifact_id: 產出物 ID
            content: 內容
            author: 作者
            message: 提交訊息
            tags: 標籤
            
        Returns:
            新版本
        """
        artifact = self.artifacts.get(artifact_id)
        if not artifact:
            artifact = self.register_artifact(artifact_id, artifact_id)
        
        # 計算 hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # 計算新版本號
        current = artifact.current_version
        new_version = Version(
            version_id=f"{artifact_id}-v{current.major}.{current.minor}.{current.patch + 1}",
            artifact_id=artifact_id,
            major=current.major,
            minor=current.minor,
            patch=current.patch + 1,
            content=content,
            content_hash=content_hash,
            content_size=len(content),
            author=author,
            message=message,
            tags=tags or [],
        )
        
        artifact.add_version(new_version)
        self.versions[artifact_id].append(new_version)
        
        # 保存
        self._save_version(new_version)
        
        return new_version
    
    def tag_version(self, artifact_id: str, version: str,
                   tag: str) -> bool:
        """
        為版本添加標籤
        
        Args:
            artifact_id: 產出物 ID
            version: 版本號 (如 "v1.2.0")
            tag: 標籤
            
        Returns:
            是否成功
        """
        for v in self.versions.get(artifact_id, []):
            if str(v) == version:
                v.tags.append(tag)
                return True
        return False
    
    def create_release(self, artifact_id: str, version: str) -> bool:
        """
        創建發布版本
        
        Args:
            artifact_id: 產出物 ID
            version: 版本號
            
        Returns:
            是否成功
        """
        return self.tag_version(artifact_id, version, "release")
    
    def get_version(self, artifact_id: str, version: str = None) -> Optional[Version]:
        """
        取得版本
        
        Args:
            artifact_id: 產出物 ID
            version: 版本號 (None = 最新)
            
        Returns:
            Version 或 None
        """
        if version is None:
            artifact = self.artifacts.get(artifact_id)
            return artifact.current_version if artifact else None
        
        # 解析版本號
        for v in self.versions.get(artifact_id, []):
            if str(v) == version:
                return v
        
        return None
    
    def get_history(self, artifact_id: str, limit: int = 50) -> List[Version]:
        """
        取得版本歷史
        
        Args:
            artifact_id: 產出物 ID
            limit: 限制數量
            
        Returns:
            版本列表
        """
        versions = self.versions.get(artifact_id, [])
        return sorted(versions, key=lambda v: -v.created_at.timestamp())[:limit]
    
    def rollback(self, artifact_id: str, version: str,
                reason: str = "",
                created_by: str = "system") -> Optional[Version]:
        """
        回滾到指定版本
        
        Args:
            artifact_id: 產出物 ID
            version: 版本號
            reason: 回滾原因
            created_by: 誰發起
            
        Returns:
            回滾後的版本或 None
        """
        target = self.get_version(artifact_id, version)
        if not target:
            return None
        
        # 記錄回滾點
        artifact = self.artifacts.get(artifact_id)
        current = artifact.current_version if artifact else None
        
        rollback_point = RollbackPoint(
            id=f"rb-{len(self.rollback_history) + 1}",
            artifact_id=artifact_id,
            from_version=str(current) if current else "none",
            to_version=version,
            reason=reason,
            created_by=created_by,
        )
        
        self.rollback_history.append(rollback_point)
        
        # 更新當前版本
        if artifact:
            artifact.current_version = target
        
        return target
    
    def get_rollback_history(self, artifact_id: str = None) -> List[RollbackPoint]:
        """取得回滾歷史"""
        if artifact_id:
            return [
                rb for rb in self.rollback_history
                if rb.artifact_id == artifact_id
            ]
        return self.rollback_history
    
    def get_diff(self, artifact_id: str, 
                from_version: str, to_version: str) -> Dict:
        """
        取得兩個版本的差異
        
        Args:
            artifact_id: 產出物 ID
            from_version: 起點版本
            to_version: 終點版本
            
        Returns:
            差異資訊
        """
        v1 = self.get_version(artifact_id, from_version)
        v2 = self.get_version(artifact_id, to_version)
        
        if not v1 or not v2:
            return {"error": "Version not found"}
        
        # 簡單的 hash 比較
        return {
            "artifact_id": artifact_id,
            "from": str(v1),
            "to": str(v2),
            "content_changed": v1.content_hash != v2.content_hash,
            "size_diff": v2.content_size - v1.content_size,
        }
    
    def compare_versions(self, artifact_id: str) -> Dict:
        """
        比較所有版本
        
        Args:
            artifact_id: 產出物 ID
            
        Returns:
            比較結果
        """
        versions = self.get_history(artifact_id)
        
        if len(versions) < 2:
            return {"versions": [str(v) for v in versions]}
        
        comparisons = []
        for i in range(len(versions) - 1):
            v1 = versions[i + 1]  # 較舊
            v2 = versions[i]  # 較新
            
            comparisons.append({
                "from": str(v1),
                "to": str(v2),
                "size_diff": v2.content_size - v1.content_size,
                "author": v2.author,
                "message": v2.message,
            })
        
        return {
            "artifact_id": artifact_id,
            "total_versions": len(versions),
            "comparisons": comparisons,
        }
    
    def _save_version(self, version: Version):
        """保存版本到磁盤"""
        path = os.path.join(
            self.storage_path,
            version.artifact_id,
            f"{version.version_id}.json"
        )
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(version.to_dict(), f, indent=2, default=str)
    
    def generate_report(self) -> str:
        """生成報告"""
        report = f"""
# 📦 Version Control 報告

## 統計

| 指標 | 數值 |
|------|------|
| 產出物數 | {len(self.artifacts)} |
| 總版本數 | {sum(len(v) for v in self.versions.values())} |
| 回滾次數 | {len(self.rollback_history)} |

---

## 產出物

| ID | 名稱 | 當前版本 | 版本數 |
|------|------|----------|------|
"""
        
        for artifact_id, artifact in self.artifacts.items():
            report += f"| {artifact_id} | {artifact.name} | {artifact.current_version} | {len(self.versions.get(artifact_id, []))} |\n"
        
        if self.rollback_history:
            report += f"""

## 最近回滾

| ID | 產出物 | 從 | 到 | 時間 |
|------|------|------|------|------|
"""
            
            for rb in self.rollback_history[-5:]:
                report += f"| {rb.id} | {rb.artifact_id} | {rb.from_version} | {rb.to_version} | {rb.created_at.strftime('%Y-%m-%d %H:%M')} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vc = VersionControl(storage_path=f"{tmpdir}/versions")
        
        print("=== Register Artifact ===")
        artifact = vc.register_artifact("login-module", "登入模組", "code")
        print(f"Registered: {artifact.id}")
        
        print("\n=== Commits ===")
        v1 = vc.commit("login-module", "def login(): pass", author="dev", message="init")
        print(f"v1: {v1}")
        
        v2 = vc.commit("login-module", "def login(user, pass): return True", author="dev", message="add params")
        print(f"v2: {v2}")
        
        v3 = vc.commit("login-module", "def login(user, pass, remember=False): return True", author="dev", message="add remember")
        print(f"v3: {v3}")
        
        print("\n=== Tag ===")
        vc.tag_version("login-module", "v0.0.1", "release")
        vc.tag_version("login-module", "v0.0.1", "tested")
        print("Tagged v0.0.1")
        
        print("\n=== History ===")
        history = vc.get_history("login-module")
        for v in history:
            print(f"  {v} - {v.message} ({v.tags})")
        
        print("\n=== Rollback ===")
        rolled = vc.rollback("login-module", "v0.0.1", reason="Found bug")
        print(f"Rolled back to: {rolled}")
        
        print("\n=== Compare ===")
        comp = vc.compare_versions("login-module")
        print(f"Total versions: {comp['total_versions']}")
        
        print("\n=== Report ===")
        print(vc.generate_report())
