# 🚀 Methodology-v2 快速上手指南

> 5 分鐘入門，10 分鐘開始開發

---

## 這是什麼？

**Methodology-v2** 是一套幫助團隊用 AI Agent 開發軟體的方法論。

簡單說：讓 AI 幫你寫代碼、測試、審查，你專心解決問題。

---

## 🎯 目標讀者

- ✅ 想用 AI 輔助開發的團隊
- ✅ 想要標準化開發流程的團隊
- ✅ 想要提升開發效率的團隊

**不需要**：
- ❌ AI 專家
- ❌ 大團隊
- ❌ 完美流程

---

## 🏁 5 分鐘快速開始

### 1. 安裝

```bash
pip install methodology-v2
```

或

```bash
git clone https://github.com/johnnylugm-tech/methodology-v2
cd methodology-v2
pip install -e .
```

### 2. 建立你的第一個任務

```python
from methodology import TaskSplitter

# 描述你想要什麼
splitter = TaskSplitter()
tasks = splitter.split_from_goal("開發一個簡單的天氣查詢系統")

# 自動幫你拆分任務
for task in tasks:
    print(f"📋 {task.name}")
```

**輸出**：
```
📋 調研與分析
📋 系統設計
📋 開發實現
📋 測試驗證
```

### 3. 選擇你的開發模式

```python
from methodology import Dashboard

# 輕鬆模式 (推薦新手)
dashboard = Dashboard(mode="light")

# 完整模式 (需要更多功能)
# dashboard = Dashboard(mode="full")

dashboard.run()
```

打開瀏覽器 http://localhost:8080 就可以看到儀表板！

---

## 💡 核心概念

### 不用學全部，先用這 3 個！

| 功能 | 什麼時候用 |
|------|-----------|
| **TaskSplitter** | 不知道怎麼開始？用它幫你拆任務 |
| **Dashboard** | 想看開發進度？打開儀表板 |
| **SmartRouter** | 不知道用哪個 AI 模型？讓它幫你選 |

### 以後想用的

| 功能 | 什麼時候用 |
|------|-----------|
| **AutoQualityGate** | 想要自動檢查代碼品質 |
| **DocGenerator** | 想要自動生成文檔 |
| **TestGenerator** | 想要自動生成測試 |
| **PredictiveMonitor** | 想要預測問題 |

---

## 🔄 開發流程（簡化版）

```
1. 用 TaskSplitter 拆分任務
      ↓
2. 讓 AI Agent 執行任務
      ↓
3. 用 AutoQualityGate 檢查品質
      ↓
4. 用 Dashboard 看進度
      ↓
5. 重複直到完成
```

就是這麼簡單！

---

## 🎓 學習路徑

### 第一天：基礎

- [x] 安裝完成
- [x] 跑第一個範例
- [ ] 用 TaskSplitter 拆分一個任務
- [ ] 打開 Dashboard 看看

### 第二天：熟悉

- [ ] 試試 SmartRouter 選模型
- [ ] 用 AutoQualityGate 檢查代碼
- [ ] 生成第一份文檔

### 第三天：進階

- [ ] 用 TestGenerator 生成測試
- [ ] 設定 PredictiveMonitor
- [ ] 用 Docker 部署

---

## ❓ 常見問題

**Q: 我需要很多 AI 知識嗎？**
A: 不用！Methodology-v2 會幫你處理。

**Q: 團隊很小可以嗎？**
A: 可以！1個人、3個人、10個人都可以用。

**Q: 一定要用全部功能嗎？**
A: 不用！從一個功能開始，漸進增加。

**Q: 免費嗎？**
A: 是的，開源免費使用。

---

## 📚 接下來

- [ ] 繼續閱讀完整文檔
- [ ] 查看範例程式碼
- [ ] 加入社群討論

---

## 💬 獲得幫助

- GitHub Issues: 報告問題
- 文件: 查看完整說明

---

**記住：不用一次學會全部，從一小步開始！**

🚀 加油！
