# Case 38: Knowledge Sync - 知識同步系統

## 目標
對標 Agno 的內建知識庫自動同步，實現 AI-native 知識管理。

## 問題背景

Agno 提供了內建的知識庫同步機制，自動同步文件到向量存儲。本系統對標此功能，提供：
- 自動同步文件到知識庫
- 版本控制
- 增量更新
- 向量存儲介面

## 實作架構

### 核心類

```
KnowledgeSync
├── KnowledgeItem (數據模型)
│   ├── item_id: 唯一識別
│   ├── source: 來源類型 (file/url/api)
│   ├── content: 內容
│   ├── content_hash: 內容指紋
│   ├── version: 版本號
│   └── sync_status: 同步狀態
│
├── SyncStatus (枚舉)
│   ├── SYNCED: 已同步
│   ├── PENDING: 待同步
│   ├── OUTDATED: 過時
│   └── ERROR: 錯誤
│
└── 適配器
    ├── FileSyncAdapter: 文件同步
    └── WebSyncAdapter: Web同步
```

## 使用範例

### 基本使用

```python
from knowledge_sync import KnowledgeSync, FileSyncAdapter

# 初始化
kb = KnowledgeSync()

# 註冊文件同步來源
kb.register_source("docs", FileSyncAdapter([
    "/path/to/doc1.md",
    "/path/to/doc2.md"
]).sync)

# 同步所有來源
results = kb.sync_all()

# 搜尋知識庫
results = kb.search("Prompt Engineering")

# 查看狀態
status = kb.get_status()
```

### 版本控制

```python
# 更新內容，自動提升版本
kb.update(item_id, new_content)

# 查看過時項目
outdated = kb.get_outdated()
```

## 對標 Agno 知識庫

| Agno Feature | 本系統實現 |
|--------------|-----------|
| Auto-sync files | FileSyncAdapter |
| Version control | KnowledgeItem.version |
| Incremental update | content_hash 變更檢測 |
| Vector store interface | 預留介面 |
| Source tracking | source + source_id |

## 應用場景

1. **文件知識庫**：自動同步 markdown 文件
2. **Web 知識庫**：定時抓取網頁內容
3. **API 知識庫**：從 API 動態更新知識
4. **增量同步**：只同步有變化的內容

## 擴展方向

- 向量嵌入整合
- 多來源統一管理
- 同步衝突解決
- 增量更新優化
