# 30 分鐘上手 methodology-v2

> 30-Minute Quick Start Guide

---

## 🎯 目標

30 分鐘內建立你的第一個 Agent 開發專案

---

## 📅 時間表

| 時間 | 任務 |
|------|------|
| 5 分鐘 | 環境設定 |
| 10 分鐘 | 最小可行配置 |
| 10 分鐘 | 第一個專案 |
| 5 分鐘 | 驗證成果 |

---

## Step 1: 環境設定 (5 分鐘)

```bash
# 確認 Python 版本
python3 --version  # 需要 >= 3.11

# 安裝 methodology-v2
pip install -e .

# 確認安裝
methodology --version
```

---

## Step 2: 最小可行配置 (10 分鐘)

methodology-v2 有 80+ 模組，但只需要 5 個核心：

| 模組 | 功能 | 為什麼需要 |
|------|------|-------------|
| `task_splitter.py` | 任務分解 | 把大任務拆成小任務 |
| `agent_spawner.py` | Agent 派遣 | 執行任務 |
| `quality_gate/` | 品質閘道 | 確保品質 |
| `enforcement/` | 強制執行 | 防止壞習慣 |
| `cost_allocator.py` | 成本追蹤 | 控制預算 |

```bash
# 建立專案目錄
mkdir my-first-agent-project
cd my-first-agent-project

# 初始化
python3 cli.py init "My First Project"
```

---

## Step 3: 第一個專案 (10 分鐘)

### 3.1 建立第一個任務

```python
# main.py
from task_splitter import TaskSplitter

splitter = TaskSplitter()
tasks = splitter.split("建立一個用戶登入功能")
print(f"拆分為 {len(tasks)} 個子任務")
```

### 3.2 執行品質檢查

```bash
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py
```

### 3.3 查看結果

```bash
python3 cli.py status
```

---

## Step 4: 驗證成果 (5 分鐘)

```bash
# 確認所有檢查通過
python3 quality_gate/unified_gate.py

# 預期輸出
# ✅ All checks passed!
```

---

## 🎉 完成！

你已經學會了：
- ✅ 環境設定
- ✅ 任務分解
- ✅ 品質檢查
- ✅ 強制執行

---

## 下一步

| 主題 | 文件 |
|------|------|
| 完整學習路徑 | [LEARNING_PATH.md](./docs/LEARNING_PATH.md) |
| 學習地圖 | [ROADMAP.md](./docs/ROADMAP.md) |
| CLI 命令參考 | [CLI_REFERENCE.md](./docs/CLI_REFERENCE.md) |

---

*最後更新：2026-03-25*
