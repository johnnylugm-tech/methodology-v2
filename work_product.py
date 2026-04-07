#!/usr/bin/env python3
"""
Work Products - 工作產品

AI-native 特點：
- 結構化產出，定義明確
- 自動分類，無需額外努力
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class ProductType(Enum):
    """產品類型"""
    CODE = "code"
    DOCUMENT = "document"
    REPORT = "report"
    TEST_RESULT = "test_result"
    CONFIG = "config"
    MODEL = "model"
    DATA = "data"

class VerificationStatus(Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"

@dataclass
class WorkProduct:
    """
    AI Agent 工作產品
    
    結構化定義：
    - 明確的類型
    - 明確的擁有者
    - 明確的驗證狀態
    """
    product_id: str
    name: str
    type: ProductType
    owner_agent_id: str
    content: Any
    produced_at: datetime
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_by: str = None
    verified_at: datetime = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "type": self.type.value,
            "owner_agent_id": self.owner_agent_id,
            "produced_at": self.produced_at.isoformat(),
            "verification_status": self.verification_status.value,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "metadata": self.metadata,
        }
    
    def verify(self, verifier_id: str):
        """驗證產品"""
        self.verification_status = VerificationStatus.VERIFIED
        self.verified_by = verifier_id
        self.verified_at = datetime.now()
    
    def fail(self, verifier_id: str, reason: str = None):
        """標記產品驗證失敗"""
        self.verification_status = VerificationStatus.FAILED
        self.verified_by = verifier_id
        self.verified_at = datetime.now()
        if reason:
            self.metadata["failure_reason"] = reason

class WorkProductRegistry:
    """
    工作產品註冊表
    
    AI-native 特點：
    - 自動註冊所有產品
    - 查詢方便
    """
    
    def __init__(self):
        self.products: Dict[str, WorkProduct] = {}
        self.agent_products: Dict[str, List[str]] = {}  # agent_id -> product_ids
    
    def register(self, product: WorkProduct):
        """註冊產品"""
        self.products[product.product_id] = product
        self.agent_products.setdefault(product.owner_agent_id, []).append(product.product_id)
    
    def get(self, product_id: str) -> Optional[WorkProduct]:
        """取得單一產品"""
        return self.products.get(product_id)
    
    def get_by_agent(self, agent_id: str) -> List[WorkProduct]:
        """取得某 Agent 的所有產品"""
        product_ids = self.agent_products.get(agent_id, [])
        return [self.products[pid] for pid in product_ids if pid in self.products]
    
    def get_by_type(self, product_type: ProductType) -> List[WorkProduct]:
        """取得某類型的所有產品"""
        return [p for p in self.products.values() if p.type == product_type]
    
    def get_unverified(self) -> List[WorkProduct]:
        """取得所有未驗證的產品"""
        return [p for p in self.products.values() if p.verification_status == VerificationStatus.UNVERIFIED]
    
    def get_verification_summary(self) -> dict:
        """取得驗證摘要"""
        total = len(self.products)
        verified = sum(1 for p in self.products.values() if p.verification_status == VerificationStatus.VERIFIED)
        failed = sum(1 for p in self.products.values() if p.verification_status == VerificationStatus.FAILED)
        return {
            "total": total,
            "verified": verified,
            "failed": failed,
            "unverified": total - verified - failed,
            "verification_rate": f"{(verified/total*100):.1f}%" if total > 0 else "N/A"
        }
    
    def list_all(self) -> List[WorkProduct]:
        """列出所有產品"""
        return list(self.products.values())


# 全域註冊表實例
_global_registry: Optional[WorkProductRegistry] = None

def get_registry() -> WorkProductRegistry:
    """取得全域註冊表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = WorkProductRegistry()
    return _global_registry

def register_product(
    name: str,
    product_type: ProductType,
    owner_agent_id: str,
    content: Any,
    metadata: Dict = None
) -> WorkProduct:
    """快速註冊產品的便捷函數"""
    registry = get_registry()
    product = WorkProduct(
        product_id=f"WP-{uuid.uuid4().hex[:8]}",
        name=name,
        type=product_type,
        owner_agent_id=owner_agent_id,
        content=content,
        produced_at=datetime.now(),
        metadata=metadata or {}
    )
    registry.register(product)
    return product
