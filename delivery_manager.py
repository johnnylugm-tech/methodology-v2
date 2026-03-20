#!/usr/bin/env python3
"""
Delivery Manager - 交付物管理

統一版本控制與交付追蹤
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import hashlib


class DeliveryStatus(Enum):
    """交付狀態"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    RELEASED = "released"
    DEPRECATED = "deprecated"


class DeliveryType(Enum):
    """交付類型"""
    CODE = "code"
    DOCUMENT = "document"
    REPORT = "report"
    MODEL = "model"
    API = "api"
    OTHER = "other"


@dataclass
class Version:
    """版本"""
    major: int = 0
    minor: int = 0
    patch: int = 0
    
    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"
    
    def bump_major(self) -> "Version":
        return Version(self.major + 1, 0, 0)
    
    def bump_minor(self) -> "Version":
        return Version(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> "Version":
        return Version(self.major, self.minor, self.patch + 1)


@dataclass
class DeliveryItem:
    """交付項目"""
    id: str
    name: str
    description: str
    type: DeliveryType
    status: DeliveryStatus = DeliveryStatus.DRAFT
    
    # 版本
    version: Version = field(default_factory=Version)
    previous_version: Version = None
    
    # 內容
    content_hash: str = None
    file_path: str = None
    size_bytes: int = 0
    
    # 元數據
    tags: List[str] = field(default_factory=list)
    author: str = None
    project_id: str = None
    
    # 追蹤
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    released_at: datetime = None
    
    # 審核
    reviewers: List[str] = field(default_factory=list)
    approved_by: List[str] = field(default_factory=list)
    notes: str = ""
    
    def content_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": str(self.version),
            "status": self.status.value,
            "type": self.type.value,
        }


@dataclass
class Release:
    """發布"""
    id: str
    name: str
    version: Version
    items: List[str]  # delivery item IDs
    release_notes: str = ""
    changelog: str = ""
    status: str = "planned"  # planned, in_progress, completed
    created_at: datetime = field(default_factory=datetime.now)
    released_at: datetime = None


class DeliveryManager:
    """交付物管理系統"""
    
    def __init__(self):
        self.items: Dict[str, DeliveryItem] = {}
        self.releases: Dict[str, Release] = {}
        self.tags: Dict[str, List[str]] = defaultdict(list)  # tag -> item IDs
        self.projects: Dict[str, List[str]] = defaultdict(list)  # project -> item IDs
    
    def create_item(self, name: str, description: str,
                   item_type: DeliveryType,
                   author: str = None,
                   project_id: str = None,
                   tags: List[str] = None) -> str:
        """建立交付項目"""
        item_id = f"del-{len(self.items) + 1}"
        
        item = DeliveryItem(
            id=item_id,
            name=name,
            description=description,
            type=item_type,
            author=author,
            project_id=project_id,
            tags=tags or [],
        )
        
        self.items[item_id] = item
        
        # 更新索引
        if project_id:
            self.projects[project_id].append(item_id)
        for tag in item.tags:
            self.tags[tag].append(item_id)
        
        return item_id
    
    def update_item(self, item_id: str, **kwargs):
        """更新交付項目"""
        item = self.items.get(item_id)
        if not item:
            return
        
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        item.updated_at = datetime.now()
    
    def set_content(self, item_id: str, content: str, file_path: str = None):
        """設定內容"""
        item = self.items.get(item_id)
        if not item:
            return
        
        # 計算 hash
        item.content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        item.file_path = file_path
        item.size_bytes = len(content)
        item.updated_at = datetime.now()
    
    def bump_version(self, item_id: str, bump_type: str = "patch") -> Version:
        """更新版本"""
        item = self.items.get(item_id)
        if not item:
            return None
        
        item.previous_version = Version(item.version.major, item.version.minor, item.version.patch)
        
        if bump_type == "major":
            item.version = item.version.bump_major()
        elif bump_type == "minor":
            item.version = item.version.bump_minor()
        else:
            item.version = item.version.bump_patch()
        
        item.updated_at = datetime.now()
        return item.version
    
    def submit_for_review(self, item_id: str, reviewers: List[str] = None):
        """提交審核"""
        item = self.items.get(item_id)
        if not item:
            return
        
        item.status = DeliveryStatus.REVIEW
        if reviewers:
            item.reviewers = reviewers
        item.updated_at = datetime.now()
    
    def approve(self, item_id: str, approver: str):
        """核准"""
        item = self.items.get(item_id)
        if not item:
            return
        
        if approver not in item.approved_by:
            item.approved_by.append(approver)
        
        # 如果所有人都核准了
        if set(item.reviewers).issubset(set(item.approved_by)):
            item.status = DeliveryStatus.APPROVED
        
        item.updated_at = datetime.now()
    
    def release(self, item_id: str):
        """發布"""
        item = self.items.get(item_id)
        if not item:
            return
        
        item.status = DeliveryStatus.RELEASED
        item.released_at = datetime.now()
        item.updated_at = datetime.now()
    
    def deprecate(self, item_id: str):
        """廢棄"""
        item = self.items.get(item_id)
        if not item:
            return
        
        item.status = DeliveryStatus.DEPRECATED
        item.updated_at = datetime.now()
    
    def create_release(self, name: str, version: Version,
                      item_ids: List[str],
                      release_notes: str = "",
                      changelog: str = "") -> str:
        """建立發布"""
        release_id = f"release-{len(self.releases) + 1}"
        
        release = Release(
            id=release_id,
            name=name,
            version=version,
            items=item_ids,
            release_notes=release_notes,
            changelog=changelog,
        )
        
        self.releases[release_id] = release
        return release_id
    
    def get_items_by_project(self, project_id: str) -> List[Dict]:
        """取得專案的所有交付項目"""
        item_ids = self.projects.get(project_id, [])
        return [self.items[i].content_dict() for i in item_ids if i in self.items]
    
    def get_items_by_tag(self, tag: str) -> List[Dict]:
        """取得特定標籤的項目"""
        item_ids = self.tags.get(tag, [])
        return [self.items[i].content_dict() for i in item_ids if i in self.items]
    
    def get_items_by_status(self, status: DeliveryStatus) -> List[Dict]:
        """取得特定狀態的項目"""
        return [
            item.content_dict()
            for item in self.items.values()
            if item.status == status
        ]
    
    def get_recent_items(self, limit: int = 10) -> List[Dict]:
        """取得最近的項目"""
        sorted_items = sorted(
            self.items.values(),
            key=lambda x: -x.updated_at.timestamp()
        )
        return [item.content_dict() for item in sorted_items[:limit]]
    
    def get_release_history(self, item_id: str) -> List[Dict]:
        """取得項目的發布歷史"""
        item = self.items.get(item_id)
        if not item:
            return []
        
        history = []
        
        if item.previous_version:
            history.append({
                "version": str(item.previous_version),
                "action": "previous"
            })
        
        history.append({
            "version": str(item.version),
            "status": item.status.value,
            "released_at": item.released_at.isoformat() if item.released_at else None,
        })
        
        return history
    
    def get_summary(self) -> Dict:
        """取得摘要"""
        by_status = defaultdict(int)
        by_type = defaultdict(int)
        
        for item in self.items.values():
            by_status[item.status.value] += 1
            by_type[item.type.value] += 1
        
        return {
            "total_items": len(self.items),
            "total_releases": len(self.releases),
            "by_status": dict(by_status),
            "by_type": dict(by_type),
        }
    
    def generate_changelog(self, release_id: str) -> str:
        """生成變更日誌"""
        release = self.releases.get(release_id)
        if not release:
            return ""
        
        changelog = f"# {release.name} ({release.version})\n\n"
        changelog += f"**Release Date**: {release.created_at.strftime('%Y-%m-%d')}\n\n"
        
        if release.release_notes:
            changelog += f"## Notes\n\n{release.release_notes}\n\n"
        
        changelog += "## Items\n\n"
        
        for item_id in release.items:
            item = self.items.get(item_id)
            if item:
                changelog += f"- [{item.status.value}] {item.name} ({item.version})\n"
        
        return changelog


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    manager = DeliveryManager()
    
    # 建立交付項目
    print("=== Creating Items ===")
    
    doc1 = manager.create_item(
        name="API 文檔",
        description="REST API 完整文檔",
        item_type=DeliveryType.DOCUMENT,
        author="johnny",
        project_id="project-ai",
        tags=["api", "documentation"]
    )
    
    code1 = manager.create_item(
        name="認證模組",
        description="用戶認證和授權",
        item_type=DeliveryType.CODE,
        author="johnny",
        project_id="project-ai",
        tags=["security", "core"]
    )
    
    model1 = manager.create_item(
        name="推薦模型 v1",
        description="商品推薦模型",
        item_type=DeliveryType.MODEL,
        author="johnny",
        project_id="project-ai",
        tags=["ml", "ai"]
    )
    
    # 設定內容
    manager.set_content(doc1, "API documentation content...", "/docs/api.md")
    manager.set_content(code1, "def authenticate(): pass", "/src/auth.py")
    
    # 版本管理
    print("\n=== Version Bump ===")
    v1 = manager.bump_version(code1, "minor")
    print(f"Code version: {v1}")
    
    # 提交審核
    manager.submit_for_review(code1, reviewers=["pm", "lead-dev"])
    manager.approve(code1, "pm")
    manager.approve(code1, "lead-dev")
    
    # 發布
    manager.release(code1)
    manager.release(doc1)
    
    # 建立 Release
    print("\n=== Creating Release ===")
    release = manager.create_release(
        name="MVP Release",
        version=Version(1, 0, 0),
        item_ids=[doc1, code1],
        release_notes="First release with core functionality"
    )
    
    # 查詢
    print("\n=== Project Items ===")
    items = manager.get_items_by_project("project-ai")
    for item in items:
        print(f"  {item['name']} - {item['version']} ({item['status']})")
    
    print("\n=== Summary ===")
    summary = manager.get_summary()
    print(f"Total items: {summary['total_items']}")
    print(f"By status: {summary['by_status']}")
    
    print("\n=== Changelog ===")
    print(manager.generate_changelog(release))
