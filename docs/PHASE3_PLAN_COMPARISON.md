# Phase 3 執行計劃比較：Original (v6.45) vs Current (v6.49)

> **日期**: 2026-04-05
> **Original**: v6.45.0 生成的計劃
> **Current**: v6.49.5 生成的計劃

---

## 摘要比較

| 面向 | Original (v6.45) | Current (v6.49) | 改進 |
|------|-----------------|-----------------|------|
| **章節數** | 18 章節 | 19 章節 | +1 (Section 9.5) |
| **@covers 語法** | `@covers: FR-01` ❌ | docstring `[FR-01]` ✅ | Bug 1 已修復 |
| **路徑支援** | 僅 `03-implementation/` | `03-implementation/` + `app/` ✅ | Bug 2 已修復 |
| **Sub-Agent 管理** | 基本描述 | 完整 Need-to-Know + On-Demand ✅ | 新增 9.5 節 |
| **Tool Timing** | 一般原則 | Phase-specific 工具時機 ✅ | 細化 |
| **Version** | v6.45.0 | v6.49.5 | +4 版本 |

---

## Section 9.5 Sub-Agent Management（新功能）

### Original (v6.45)

沒有這個章節。

---

### Current (v6.49.5)

```
## 9.5 Sub-Agent Management（Need-to-Know + On-Demand）

**Phase 3: 代碼實現**

### Agent 角色
- **Agent A（developer）**: 實作 FR-XX
- **Agent B（reviewer）**: 審查 FR-XX 代碼

### Need-to-Know（只給必要資訊）

| 檔案 | 章節 | 原因 |
|------|------|------|
| SRS.md | §FR-XX 需求描述 | 只實作這個 FR 的功能 |
| SAD.md | §Module 邊界對照表 | 知道 Module 介面和邊界 |

**Skip**: `完整 SRS.md, 完整 SAD.md, 其他 FR 的實作`
**Context**: single_fr

### On-Demand（需要時才請求）
- **觸發條件**: 當需要知道其他 FR 的實作細節時
- **請求對象**: N/A（不該發生，每個 FR 獨立）
- **格式**: 返回錯誤：違反 Need-to-Know

### 工具調用時機

| 事件 | 工具 | 參數 |
|------|------|------|
| spawn | 派遣 Sub-agent | {'role': 'developer', 'fr_id': '{fr}'} |
| knowledge_curator | KnowledgeCurator | verify_coverage |
| context_manager | ContextManager | 訊息 >30 時 L1 壓縮 |
| checkpoint | SessionManager | 每 FR 完成後 save |

### 隔離方法
- **Method**: `SubagentIsolator.spawn`
- **Fresh Messages**: `SRS.md §FR-XX, SAD.md §Module`
```

---

## Bug 修復對照

### Bug 1: @covers 語法

| 版本 | 內容 |
|------|------|
| **Original (v6.45)** | `@covers: FR-01` ❌ (Python 語法錯誤) |
| **Current (v6.49)** | docstring `[FR-01]` ✅ |

### Bug 2: 路徑支援

| 版本 | 路徑 |
|------|------|
| **Original (v6.45)** | `03-implementation/src/` ❌ (hardcoded) |
| **Current (v6.49)** | `03-implementation/` + `app/` ✅ (動態支援) |

---

## FR-by-FR 任務表格比較

### Original (v6.45)

| FR | 模組 | 產出檔案 | 測試檔案 |
|------|------|---------|----------|
| FR-01 | lexicon_mapper | `app/processing/lexicon_mapper.py` | `tests/test_fr01*.py` |
| ... | ... | ... | ... |

### Current (v6.49.5) - 相同格式

| FR | 模組 | 產出檔案 | 測試檔案 |
|------|------|---------|----------|
| FR-01 | lexicon_mapper | `app/processing/lexicon_mapper.py` | `tests/test_fr01*.py` |
| ... | ... | ... | ... |

**結論**: FR 表格格式相同，內容無變化。

---

## Developer Prompt 比較

### Original (v6.45) - 有語法錯誤

```
OUTPUT_FORMAT:
{
 "status": "success|error|unable_to_proceed",
 "result": "實際產出（路徑）",
 "confidence": 1-10,
 "citations": ["{fr['fr']}", "SRS.md#L23-L45", "SAD.md#L50-L60"],
 "summary": "50字內"
}

HR-15 強制執行：citations 必須包含「檔名#L行號」格式
═══════════════════════════════════════
```

### Current (v6.49.5) - 已修復

```
【驗證標準】
- pytest 100% 通過
- 覆蓋率 ≥70%
- 在 docstring 中標記 [FR-01]，例如：`"""[FR-01] 測試：xxx"""`

FORBIDDEN：
- ❌ dump SRS.md/SAD.md 全文
- ❌ docstring 沒有 [FR-XX] 標記

【OUTPUT_FORMAT】
{
 "status": "success|error|unable_to_proceed",
 "result": "實際產出（路徑）",
 "confidence": 1-10,
 "citations": ["{fr['fr']}", "SRS.md#L23-L45", "SAD.md#L50-L60"],
 "summary": "50字內"
}

HR-15 強制執行：citations 必須包含「檔名#L行號」格式
═══════════════════════════════════════
```

**改進**:
1. `@covers: FR-01` → docstring `[FR-01]` 標記
2. 明確說明 docstring 格式
3. FORBIDDEN 更新為 docstring 標記要求

---

## 產出結構樹比較

### Original (v6.45)

```
03-implementation/
├── app/
│ ├── app/api/
│ │ routes.py
│ ├── app/backend/
│ │ kokoro_client.py
│ ├── app/infrastructure/
│ │ audio_converter.py
│ │ circuit_breaker.py
│ │ redis_cache.py
│ ├── app/processing/
│ │ lexicon_mapper.py
│ │ ssml_parser.py
│ │ text_chunker.py
│ ├── app/synth/
│ │ synth_engine.py
├── tests/
```

### Current (v6.49.5)

相同結構，但支援 `app/` 作為 alternative。

---

## Quality Gate 比較

### Original (v6.45)

```bash
# 1. TH-06 Constitution 測試覆蓋率 >90%
python3 quality_gate/constitution/runner.py --type implementation

# 2. TH-10 測試通過率 =100%
pytest tests/ -v

# 3. TH-11 覆蓋率 ≥70%
pytest --cov=app/ -v

# 4. TH-16 代碼↔SAD =100%
python3 cli.py trace-check

# 5. TH-15 Phase Truth ≥70%
python3 cli.py phase-verify --phase 3

# 6. HR-08 stage-pass
python3 cli.py stage-pass --phase 3

# 7. HR-02 FrameworkEnforcer BLOCK
python3 cli.py enforce --level BLOCK
```

### Current (v6.49.5)

相同 Quality Gate，但 Constitution Runner 使用方式已修正：

```bash
# Constitution 使用修正後的 API
python3 -c "from quality_gate.constitution import run_constitution_check; run_constitution_check('implementation', current_phase=3)"
```

---

## 結論

### 已修復的問題

| Bug | Original | Current |
|-----|----------|---------|
| @covers 語法 | ❌ `@covers: FR-01` | ✅ docstring `[FR-01]` |
| 路徑支援 | ❌ 僅 `03-implementation/` | ✅ `03-implementation/` + `app/` |

### 新增功能

| 功能 | Original | Current |
|------|----------|---------|
| Section 9.5 | ❌ 無 | ✅ Sub-Agent Management |
| Need-to-Know | ❌ 無 | ✅ 完整表格 |
| On-Demand | ❌ 無 | ✅ 觸發條件說明 |
| Tool Timing | ⚠️ 一般原則 | ✅ Phase-specific |
| Phase-specific prompts | ⚠️ Phase 3 only | ✅ All 8 phases |

### 與 Original 計劃的差異

1. **語法修復** - @covers 改為 docstring
2. **路徑支援** - 新增 app/ 目錄支援
3. **Sub-Agent 管理** - 新增完整 9.5 章節
4. **版本更新** - v6.45 → v6.49

---

*比較完成: 2026-04-05*
