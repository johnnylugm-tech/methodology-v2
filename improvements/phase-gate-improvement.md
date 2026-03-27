# Phase-Gate 改進 - 2026-03-27

## 問題
Constitution 檢查全部 8 個 Phase，不是只檢查到當前 Phase。
導致 Phase 3 時分數 23.8%（因為 Phase 4-8 不存在），但我選擇繼續。

## 解決方案
增加 `--current-phase` 參數，支援階段性檢查。

## 實作

### 修改檔案
- `quality_gate/constitution/runner.py`

### 新增參數
```bash
--current-phase {1,2,3,4,5,6,7,8}, -cp {1,2,3,4,5,6,7,8}
  只檢查到指定 Phase (1-8)。用於階段性檢查
```

### 使用範例
```bash
# Phase 3 結束後，只檢查 Phase 1-3
python runner.py --current-phase 3 --path .

# Phase 5 結束後，只檢查 Phase 1-5
python runner.py -cp 5 --path .
```

## 驗證
```bash
python3 quality_gate/constitution/runner.py --current-phase 3 --path .
```

---

*改進日期: 2026-03-27*
*改進者: Agent*

---

## 2026-03-27 11:40 修復 - 完整實現 current_phase 參數

### 問題
--current-phase 參數加了但沒有傳遞給函數，也沒有根據 phase 調整檢查範圍。

### 修復內容

#### 1. runner.py - 傳遞參數
```python
# 修改前
result = run_constitution_check(args.type, str(docs_path))

# 修改後
result = run_constitution_check(args.type, str(docs_path), args.current_phase)
```

#### 2. __init__.py - 實現邏輯
```python
def run_constitution_check(check_type: str, docs_path: str, current_phase: int = None):
    # Phase 映射
    phase_mapping = {
        1: ["srs"],
        2: ["srs", "sad"],
        3: ["srs", "sad", "implementation"],
        4: ["srs", "sad", "implementation", "test_plan"],
        5: ["srs", "sad", "implementation", "test_plan", "verification"],
        6: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report"],
        7: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report", "risk_management"],
        8: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report", "risk_management", "configuration"],
    }
    
    # 根據 current_phase 調整檢查範圍
    if current_phase is not None and current_phase in phase_mapping:
        check_types = phase_mapping[current_phase]
```

### 驗證
```bash
python3 runner.py --current-phase 3 --path /project
# 現在會只檢查 Phase 1-3 的文件
```

---
