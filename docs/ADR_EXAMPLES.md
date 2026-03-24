# ADR 常見範例

## ADR-001: 使用 PostgreSQL 作為主要資料庫

**Status**: accepted  
**Date**: 2026-03-24  
**Author**: Johnny

### Context

專案需要一個關聯式資料庫來存儲使用者資料和交易記錄。

### Decision

選擇 PostgreSQL 15 作為主要資料庫。

### Consequences

**正面：**
- 成熟的 ACID 支援
- 豐富的生態系統
- JSON 支援

**負面：**
- 需要管理資料庫基礎設施
- 學習曲線

### Alternatives Considered

- MySQL - 被拒絕（功能較少）
- SQLite - 被拒絕（不適合多使用者場景）
