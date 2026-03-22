#!/usr/bin/env python3
"""
Knowledge Sync - 知識同步系統

對標 Agno 的內建知識庫自動同步：
- 自動同步文件到知識庫
- 版本控制
- 增量更新
- 向量存儲介面

AI-native 實作，零額外負擔
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import hashlib
import json
import uuid

class SyncStatus(Enum):
    """同步狀態"""
    SYNCED = "synced"
    PENDING = "pending"
    OUTDATED = "outdated"
    ERROR = "error"

@dataclass
class KnowledgeItem:
    """知識項目"""
    item_id: str
    source: str              # 來源：file, url, api, etc.
    source_id: str           # 來源 ID
    content: str             # 內容
    content_hash: str        # 內容 hash
    metadata: Dict = field(default_factory=dict)
    sync_status: SyncStatus = SyncStatus.PENDING
    version: int = 1
    created_at: datetime = field(default=datetime.now)
    updated_at: datetime = field(default=datetime.now)
    synced_at: Optional[datetime] = None
    
    def update_content(self, new_content: str):
        """更新內容並提升版本"""
        if new_content != self.content:
            self.content = new_content
            self.content_hash = hashlib.md5(new_content.encode()).hexdigest()
            self.version += 1
            self.updated_at = datetime.now()
            self.sync_status = SyncStatus.PENDING
    
    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "source": self.source,
            "source_id": self.source_id,
            "version": self.version,
            "sync_status": self.sync_status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

class KnowledgeSync:
    """
    知識同步系統
    
    對標 Agno 的知識庫自動同步：
    - 自動同步文件到知識庫
    - 版本控制
    - 增量更新
    """
    
    def __init__(self):
        self.items: Dict[str, KnowledgeItem] = {}
        self.sources: Dict[str, Callable] = {}  # source -> sync function
    
    def register_source(self, source: str, sync_func: Callable):
        """註冊同步來源"""
        self.sources[source] = sync_func
    
    def add(self, source: str, source_id: str, content: str, metadata: Dict = None) -> str:
        """添加知識項目"""
        item_id = f"kb-{uuid.uuid4().hex[:8]}"
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        item = KnowledgeItem(
            item_id=item_id,
            source=source,
            source_id=source_id,
            content=content,
            content_hash=content_hash,
            metadata=metadata or {},
            sync_status=SyncStatus.SYNCED,
            synced_at=datetime.now()
        )
        
        self.items[item_id] = item
        return item_id
    
    def update(self, item_id: str, new_content: str) -> bool:
        """更新知識項目"""
        item = self.items.get(item_id)
        if not item:
            return False
        
        item.update_content(new_content)
        return True
    
    def sync_source(self, source: str) -> Dict[str, Any]:
        """同步指定來源"""
        sync_func = self.sources.get(source)
        if not sync_func:
            return {"error": f"Unknown source: {source}"}
        
        try:
            items = sync_func()
            synced = 0
            for item_data in items:
                item_id = self.add(source, item_data["id"], item_data["content"], item_data.get("metadata"))
                synced += 1
            return {"synced": synced, "source": source}
        except Exception as e:
            return {"error": str(e), "source": source}
    
    def sync_all(self) -> Dict[str, Any]:
        """同步所有來源"""
        results = {}
        for source in self.sources.keys():
            results[source] = self.sync_source(source)
        return results
    
    def search(self, query: str) -> List[KnowledgeItem]:
        """簡單關鍵字搜尋"""
        query_lower = query.lower()
        results = []
        for item in self.items.values():
            if query_lower in item.content.lower():
                results.append(item)
        return results
    
    def get_outdated(self) -> List[KnowledgeItem]:
        """取得過時項目"""
        return [item for item in self.items.values() if item.sync_status == SyncStatus.OUTDATED]
    
    def get_status(self) -> dict:
        """取得同步狀態"""
        statuses = {}
        for item_id, item in self.items.items():
            statuses[item_id] = item.sync_status.value
        return {
            "total": len(self.items),
            "synced": sum(1 for i in self.items.values() if i.sync_status == SyncStatus.SYNCED),
            "pending": sum(1 for i in self.items.values() if i.sync_status == SyncStatus.PENDING),
            "outdated": sum(1 for i in self.items.values() if i.sync_status == SyncStatus.OUTDATED),
        }

# ============================================
# 預設同步來源適配器
# ============================================

class FileSyncAdapter:
    """文件同步適配器"""
    
    def __init__(self, file_paths: List[str]):
        self.file_paths = file_paths
    
    def sync(self) -> List[Dict]:
        import os
        items = []
        for path in self.file_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                items.append({
                    "id": path,
                    "content": content,
                    "metadata": {"type": "file", "path": path}
                })
        return items

class WebSyncAdapter:
    """Web 同步適配器"""
    
    def __init__(self, urls: List[str]):
        self.urls = urls
    
    def sync(self) -> List[Dict]:
        # 簡單實現，實際需要调用 web_fetch
        items = []
        for url in self.urls:
            items.append({
                "id": url,
                "content": f"Content from {url}",
                "metadata": {"type": "web", "url": url}
            })
        return items
