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
