# 案例 33：工作產品追蹤 (Work Products)

## 情境描述

在多 Agent 協作環境中，每個 Agent 都會產生各種產出：代碼、文檔、測試結果、配置等。如何確保這些產出被正確追蹤、驗證和管理？

---

## 案例 33.1：基本工作產品註冊

### 背景
當 Agent 完成任務時，自動將其產出註冊為結構化的工作產品。

### 使用方式

```python
from work_product import (
    WorkProductRegistry, 
    WorkProduct, 
    ProductType, 
    VerificationStatus,
    register_product
)

# 初始化註冊表
registry = WorkProductRegistry()

# 手動建立產品
product = WorkProduct(
    product_id="WP-001",
    name="用戶認證模組",
    type=ProductType.CODE,
    owner_agent_id="agent-dev-001",
    content="def authenticate(user, passwd): ...",
    produced_at=datetime.now()
)

# 註冊
registry.register(product)

# 或使用快速函數
product2 = register_product(
    name="API 文檔",
    product_type=ProductType.DOCUMENT,
    owner_agent_id="agent-doc-001",
    content="# API Documentation\n\n## Endpoints...",
    metadata={"version": "1.0", "api_version": "v2"}
)
```

### 查詢產品

```python
# 依 Agent 查詢
agent_products = registry.get_by_agent("agent-dev-001")

# 依類型查詢
code_products = registry.get_by_type(ProductType.CODE)

# 取得未驗證產品
pending = registry.get_unverified()

# 驗證摘要
summary = registry.get_verification_summary()
print(f"總產品數: {summary['total']}")
print(f"已驗證: {summary['verified']}")
print(f"驗證率: {summary['verification_rate']}")
```

---

## 案例 33.2：與 HITL 整合

### 背景
當 HITL Controller 審批通過一個產出時，自動註冊為已驗證的工作產品。

### 使用方式

```python
from hitl_controller import HITLController
from work_product import (
    WorkProductRegistry, 
    ProductType, 
    register_product
)

# 初始化
controller = HITLController()
registry = WorkProductRegistry()

# 假設這是 HITL 審批通過的回調
def on_approval(output_id: str, output_data: dict, approver_id: str):
    """當產出被審批通過時自動註冊"""
    product = register_product(
        name=output_data.get("name", f"Output-{output_id}"),
        product_type=_map_output_type(output_data.get("type")),
        owner_agent_id=output_data.get("agent_id"),
        content=output_data.get("content"),
        metadata={
            "output_id": output_id,
            "approver_id": approver_id,
            "approved_at": datetime.now().isoformat()
        }
    )
    product.verify(approver_id)
    return product

def _map_output_type(output_type: str) -> ProductType:
    """將輸出類型映射為產品類型"""
    mapping = {
        "code": ProductType.CODE,
        "document": ProductType.DOCUMENT,
        "test": ProductType.TEST_RESULT,
        "config": ProductType.CONFIG,
    }
    return mapping.get(output_type, ProductType.DOCUMENT)
```

---

## 案例 33.3：自動化驗證流程

### 背景
當新產品註冊時，自動觸發品質檢查，並根據結果更新驗證狀態。

### 使用方式

```python
from work_product import WorkProductRegistry, ProductType, VerificationStatus

class AutomatedVerification:
    """自動化驗證系統"""
    
    def __init__(self, registry: WorkProductRegistry):
        self.registry = registry
    
    def check_code_quality(self, product: WorkProduct) -> bool:
        """檢查代碼品質"""
        if product.type != ProductType.CODE:
            return True
        # 簡化的品質檢查邏輯
        content = str(product.content)
        has_docstring = '"""' in content or "'''" in content
        return has_docstring
    
    def process_new_products(self):
        """處理所有未驗證的產品"""
        pending = self.registry.get_unverified()
        for product in pending:
            if self.check_code_quality(product):
                product.verify("automated-verifier")
            else:
                product.fail("automated-verifier", "Missing documentation")
        
        # 輸出摘要
        summary = self.registry.get_verification_summary()
        print(f"處理完成: {summary['total']} 產品, {summary['verified']} 已驗證")
```

---

## 案例 33.4：產品血統追蹤

### 背景
追蹤產品的來源和依賴關係，建立完整的產品血統圖。

### 使用方式

```python
from work_product import WorkProduct, ProductType, WorkProductRegistry

class ProductLineage:
    """產品血統追蹤"""
    
    def __init__(self):
        self.lineage: Dict[str, List[str]] = {}  # product_id -> parent_ids
    
    def add_parent(self, child_id: str, parent_id: str):
        """添加父子關係"""
        self.lineage.setdefault(child_id, []).append(parent_id)
    
    def get_ancestors(self, product_id: str) -> List[str]:
        """取得所有祖先"""
        ancestors = []
        queue = [product_id]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            parents = self.lineage.get(current, [])
            for parent in parents:
                ancestors.append(parent)
                queue.append(parent)
        
        return ancestors
    
    def get_descendants(self, product_id: str) -> List[str]:
        """取得所有後代"""
        descendants = []
        for child_id, parents in self.lineage.items():
            if product_id in parents:
                descendants.append(child_id)
        return descendants

# 使用範例
lineage = ProductLineage()
lineage.add_parent("WP-002", "WP-001")  # WP-002 基於 WP-001
lineage.add_parent("WP-003", "WP-002")  # WP-003 基於 WP-002

print(lineage.get_ancestors("WP-003"))  # ["WP-002", "WP-001"]
print(lineage.get_descendants("WP-001")) # ["WP-002", "WP-003"]
```

---

## 案例 33.5：產出儀表板

### 背景
為工作產品生成視覺化儀表板，展示團隊產出狀態。

### 使用方式

```python
from work_product import WorkProductRegistry, ProductType

def generate_product_dashboard(registry: WorkProductRegistry) -> str:
    """生成產品狀態儀表板"""
    summary = registry.get_verification_summary()
    all_products = registry.list_all()
    
    # 按類型分組
    by_type = {}
    for p in all_products:
        type_name = p.type.value
        by_type.setdefault(type_name, []).append(p)
    
    # 生成 Markdown
    lines = [
        "# 📦 工作產品儀表板",
        f"\n## 總覽",
        f"- **總產品數**: {summary['total']}",
        f"- **已驗證**: {summary['verified']} ✅",
        f"- **失敗**: {summary['failed']} ❌",
        f"- **待驗證**: {summary['unverified']} ⏳",
        f"- **驗證率**: {summary['verification_rate']}",
        "\n## 按類型分佈",
    ]
    
    for type_name, products in sorted(by_type.items()):
        verified = sum(1 for p in products if p.verification_status.value == "verified")
        lines.append(f"- **{type_name}**: {len(products)} 個 ({verified} 已驗證)")
    
    lines.append("\n## 待驗證產品")
    pending = registry.get_unverified()
    for p in pending:
        lines.append(f"- `{p.product_id}` - {p.name} (by {p.owner_agent_id})")
    
    return "\n".join(lines)

# 使用
registry = WorkProductRegistry()
dashboard = generate_product_dashboard(registry)
print(dashboard)
```

### 輸出範例
```
# 📦 工作產品儀表板

## 總覽
- **總產品數**: 5
- **已驗證**: 3 ✅
- **失敗**: 0 ❌
- **待驗證**: 2 ⏳
- **驗證率**: 60.0%

## 按類型分佈
- **code**: 2 個 (1 已驗證)
- **document**: 2 個 (1 已驗證)
- **test_result**: 1 個 (1 已驗證)

## 待驗證產品
- `WP-a1b2c3d4` - 用戶認證模組 (by agent-dev-001)
- `WP-e5f6g7h8` - API 文檔 (by agent-doc-001)
```

---

## 設計原則

### AI-Native 設計

1. **結構化勝於非結構化**
   - 所有產出都有明確類型和擁有者
   - 不需要額外 Effort 就能分類

2. **驗證即代碼**
   - 驗證狀態是產品的一等公民
   - 追蹤誰驗證、何時驗證

3. **查詢友好**
   - 支援依 Agent、類型、狀態查詢
   - 輕量級 API，無需復雜設定

### 使用時機

- ✅ 當需要追蹤多 Agent 產出時
- ✅ 當需要驗證流程時
- ✅ 當需要產品血統時

- ❌ 簡單腳本，不需要此複雜度
- ❌ 單一 Agent 環境（過度工程）

---

## 整合點

| 模組 | 整合方式 |
|------|----------|
| HITLController | 審批通過後自動註冊 |
| AgentOutputValidator | 驗證結果寫入產品狀態 |
| AuditLogger | 產品操作寫入審計日誌 |
| Dashboard | 讀取產品數據展示 |
