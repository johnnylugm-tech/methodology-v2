"""
ADR Module
=========
Architecture Decision Records

使用方式：

    from adr import ADR, ADRRegistry
    
    # 建立 ADR
    adr = ADR(
        title="使用 PostgreSQL 作為主要資料庫",
        status="accepted",
        context="需要一個關聯式資料庫",
        decision="選擇 PostgreSQL",
        consequences="需要管理資料庫基礎設施"
    )
    
    registry = ADRRegistry()
    adr_id = registry.save(adr)
    
    # 列出所有 ADR
    for adr in registry.list_all():
        print(f"{adr.id}: {adr.title}")
"""

from .adr import ADR, ADRRecord
from .registry import ADRRegistry

__all__ = ['ADR', 'ADRRecord', 'ADRRegistry']