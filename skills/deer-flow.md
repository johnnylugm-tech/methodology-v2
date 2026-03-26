# SKILL.md - DeerFlow

> 字節跳動開源 Deep Research 框架 (46,703 ⭐)
> 
> **一句话**：開源版 Perplexity，讓 AI 為你做深度研究

---

## 一句话总结

DeerFlow 是字節跳動開源的 SuperAgent 框架，專注於「深度研究」場景，結合網路搜索、爬蟲、Python 執行，讓 AI 自動完成複雜的研究任務。

---

## 核心功能

| 功能 | 說明 |
|------|------|
| **網路搜索** | 整合多源搜尋引擎 |
| **網頁抓取** | 自動抓取網頁內容 |
| **檔案操作** | 讀寫本地檔案 |
| **程式執行** | 執行 Python 程式碼 |
| **MCP 擴展** | 支援 MCP 伺服器擴展工具 |
| **記憶系統** | 長期記憶和上下文管理 |

---

## 架構設計

```
┌─────────────────────────────────────┐
│           DeerFlow Core             │
├─────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌──────┐ │
│  │ Planner │  │ Memory  │  │Tool  │ │
│  │ 規劃器   │  │  記憶系統 │  │ 工具集 │ │
│  └────┬────┘  └─────────┘  └──────┘ │
│       │                              │
│  ┌────┴────────────────────────┐    │
│  │     Subagents (子代理)       │    │
│  │  Searcher / Coder / Writer   │    │
│  └──────────────────────────────┘    │
└─────────────────────────────────────┘
```

---

## 安裝方式

```bash
# 方式一：快速安裝
pip install deer-flow

# 方式二：從 GitHub 安裝
git clone https://github.com/bytedance/deer-flow
cd deer-flow
pip install -e .

# 方式三：使用官方 Installer
git clone https://github.com/bytedance-deerflow/deer-flow-installer
cd deer-flow-installer
./install.sh
```

---

## 使用方式

```bash
# 啟動 DeerFlow
deer-flow

# 或使用配置檔
deer-flow --config config.yaml

# 範例：深度研究任務
deer-flow research "2026 年 AI Agent 發展趨勢報告"
```

---

## DeerFlow 2.0 新特性

| 新特性 | 說明 |
|--------|------|
| **沙盒隔離** | 安全執行不信任的程式碼 |
| **長期記憶** | 跨會話記住用戶偏好 |
| **技能系統** | 自定義 Agent 技能 |
| **子代理架構** | 多 Agent 分工合作 |

---

## 與其他研究工具比較

| 工具 | 定位 | 特色 |
|------|------|------|
| **DeerFlow** | 開源 Deep Research | 完全自託管、MCP 擴展 |
| **Perplexity** | 商業 AI 搜尋引擎 | 付費、精美介面 |
| **GPT Researcher** | 開源研究 Agent | 較老、生態較小 |
| **You.com** | AI 搜尋引擎 | 整合多種 AI |

**DeerFlow 優勢**：
- 完全開源免費 (MIT License)
- 可自部署
- MCP 工具擴展
- 字節跳動技術支援

---

## 應用場景

1. **學術研究** - 自動蒐集論文、分析趨勢
2. **市場分析** - 競爭對手分析、行業報告
3. **技術調研** - 新技術評估、可行性分析
4. **新聞摘要** - 追蹤事件、生成簡報

---

## 資源

- [官網](https://deerflow.tech/)
- [GitHub](https://github.com/bytedance/deer-flow)
- [官方範例](https://github.com/bytedance/deer-flow/tree/main/examples)

---

*建立日期：2026-03-26*