# SKILL.md - Gemini CLI

> Google 終端 AI 工具 (99,114 ⭐)
> 
> **發布日期**：2025年6月25日
> 
> **一句话**：把 Gemini AI 帶進終端機的開源 Agent

---

## 一句话总结

Google 推出的開源終端 AI 工具，讓開發者直接用自然語言在命令行操作程式碼庫、生成應用、自動化工作流。

---

## 核心功能

| 功能 | 說明 |
|------|------|
| **程式碼查詢** | 用自然語言查詢和編輯大型程式碼庫 |
| **應用生成** | 從圖片或 PDF 生成應用 |
| **工作流自動化** | 自動化複雜開發工作流 |
| **即時分析** | 即時程式碼分析能力 |
| **OAuth 認證** | 支援 Google 帳戶認證 |

---

## 安裝方式

```bash
# 方法一：npm 全域安裝
npm install -g @google/gemini-cli

# 方法二：從源碼編譯
git clone https://github.com/google-gemini/gemini-cli
cd gemini-cli
npm install
npm run build
```

---

## 使用方式

```bash
# 啟動互動模式
gemini

# 查詢程式碼
gemini "Find all usage of async/await in this project"

# 生成應用
gemini "Create a React app from this mockup.png"

# 自動化任務
gemini "Refactor all console.log to use structured logger"
```

---

## 與現有工具比較

| 工具 | 定位 | 適用場景 |
|------|------|----------|
| **Gemini CLI** | 終端 AI Agent | 快速開發、程式碼查詢 |
| **ChatGPT** | 對話式 AI | 創意發想、學習 |
| **Claude Code** | 程式碼專用 Agent | 重構、測試生成 |

**Gemini CLI 優勢**：
- Google 生態系整合
- 免費開源
- 終端無縫體驗

---

## 應用場景

1. **快速原型開發** - 用自然語言描述需求，自動生成程式碼
2. **程式碼探索** - 快速理解陌生程式碼庫
3. **自動化重構** - 批量修改程式碼風格
4. **文件生成** - 自動生成 README、API 文檔

---

## 相關連結

- [官網](https://geminicli.com/)
- [GitHub](https://github.com/google-gemini/gemini-cli)
- [Google Blog](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-gemini-cli-open-source-ai-agent/)

---

*建立日期：2026-03-26*