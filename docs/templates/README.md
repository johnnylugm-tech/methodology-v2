# Documentation Templates

> methodology-v2 標準文檔模板庫

## 📋 可用模板

| 模板 | 檔名 | ASPICE 參考 | 狀態 |
|------|------|-------------|------|
| 需求規格 | SRS_TEMPLATE.md | SWE.5 | ✅ |
| 架構設計 | SAD_TEMPLATE.md | SWE.5 | ✅ |
| 測試計畫 | TEST_PLAN_TEMPLATE.md | SWE.7 | ✅ |
| 品質報告 | QUALITY_REPORT_TEMPLATE.md | SUP.9 | ✅ |
| 風險評估 | RISK_ASSESSMENT_TEMPLATE.md | MAN.5 | ✅ |

## 🚀 使用方式

1. 選擇適當的模板
2. 複製到專案目錄
3. 填入專案資訊
4. 依據模板結構編寫內容

## 📝 命名規範

參考 `docs/naming_convention.md`

## ✅ Quality Gate

使用 quality_gate/doc_checker.py 檢查文檔完整性

```bash
python quality_gate/doc_checker.py
```

