# 案例 52：TDAD 風格的 Graph-Based Impact Analysis

## 情境描述

傳統的變更影響分析依賴人工經驗或簡單的測試覆蓋率。TDAD 風格的 Impact Analysis 通過建立完整的依賴圖，自動預測變更會影響哪些測試，並量化回歸風險。

---

## 案例 52.1：基本使用

### 背景
在提交代碼變更前，開發者需要知道這個變更會影響哪些測試，避免遺漏重要的回歸測試。

### 使用方式

```python
from anti_shortcut.impact_analysis import ImpactAnalyzer, analyze_change_impact

# 掃描專案建立依賴圖
analyzer = ImpactAnalyzer(project_path=".")
analyzer.scan_project()

# 分析單一檔案變更的影響
impact = analyzer.analyze_change("src/core/user_service.py")

print(f"Changed file: {impact.changed_file}")
print(f"Risk score: {impact.risk_score}")
print(f"Affected tests: {len(impact.affected_tests)}")
print(f"Affected modules: {len(impact.affected_modules)}")
for rec in impact.recommendations:
    print(f"  - {rec}")
```

### 輸出範例

```
Changed file: src/core/user_service.py
Risk score: 50
Affected tests: 3
Affected modules: 5
  - 建議在提交前運行 3 個相關測試
  - 高風險變更，建議進行 code review
```

---

## 案例 52.2：便捷函數

### 背景
有時只需要快速分析一個檔案的影響，不需要重複建立分析器。

### 使用方式

```python
from anti_shortcut.impact_analysis import analyze_change_impact

# 一行代碼分析變更影響
impact = analyze_change_impact("src/api/user_handler.py")

print(f"Affected tests: {impact.affected_tests}")
```

---

## 案例 52.3：導出依賴圖

### 背景
需要視覺化專案的依賴關係，用於文檔或分析。

### 使用方式

```python
from anti_shortcut.impact_analysis import ImpactAnalyzer

analyzer = ImpactAnalyzer(project_path=".")
analyzer.scan_project()

# 取得依賴報告
report = analyzer.get_dependency_report()
print(f"Total nodes: {report['total_nodes']}")
print(f"Total edges: {report['total_edges']}")
print(f"Test files: {report['test_files']}")

# 導出 Graphviz 格式
graphviz_dot = report['graphviz']
print(graphviz_dot)
```

### Graphviz 輸出範例

```
digraph DependencyGraph {
  rankdir=LR;
  node [shape=box];
  "tests/test_user.py" [shape=ellipse];
  "src/user_service.py" [shape=box];
  "tests/test_user.py" -> "src/user_service.py" [label="calls"];
}
```

---

## 案例 52.4：CLI 命令

### 背景
通過 CLI 快速分析變更影響，適合在 CI/CD pipeline 中使用。

### 命令用法

```bash
# 分析變更影響
python3 cli.py trace impact <file>

# 導出依賴圖（Graphviz 格式）
python3 cli.py trace graphviz

# 生成風險報告
python3 cli.py trace risk-report
```

### 輸出範例

```
$ python3 cli.py trace impact src/core/user_service.py

========================================
    Impact Analysis Report
========================================
📁 Changed File: src/core/user_service.py

📊 Risk Score: 50/100 (Medium Risk)

🔴 Affected Tests (3):
   - tests/unit/test_user_service.py
   - tests/integration/test_user_api.py
   - tests/e2e/test_user_flow.py

🟡 Affected Modules (5):
   - src/api/user_handler.py
   - src/services/notification_service.py
   - ...

💡 Recommendations:
   - 建議在提交前運行 3 個相關測試
   - 高風險變更，建議進行 code review
```

---

## 核心概念

### 依賴圖 (Dependency Graph)
- **節點**：檔案、模組、測試
- **邊**：依賴關係（imports, calls, inherits, configures）
- **方向**：從依賴者指向被依賴者

### 變更影響 (Change Impact)
- 追蹤哪些測試會被某個檔案的變更影響
- 使用 BFS 遍歷依賴圖
- 識別直接和間接依賴

### 回歸風險 (Regression Risk)
- **基礎風險**：20 分
- **核心模組**：+30 分（core, base, foundation）
- **受影響測試數**：
  - >10 個：+20 分
  - 5-10 個：+10 分
- **最高 100 分**

---

## 與 Traceability Matrix 的整合

Impact Analysis 是 Traceability Matrix 的自然延伸：

| Traceability Matrix | Impact Analysis |
|---------------------|-----------------|
| "這個需求有哪些測試？" | "這個檔案變更會影響哪些測試？" |
| 靜態映射 | 動態預測 |
| 離線分析 | 提交前預檢 |

結合兩者可以实现：
- **提交前檢查**：自動檢查變更是否影響需求相關測試
- **風險評估**：根據受影響的需求計算變更風險
- **測試優先級**：根據影響範圍排序測試執行順序
