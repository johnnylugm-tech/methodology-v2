# Auto Optimizer Cron 設定

## 問題

此平台沒有安裝 crond 服務，無法直接使用 crontab。

## 替代方案

### 方案 1: 使用 Heartbeat（推薦）

在 HEARTBEAT.md 中新增每小時任務：

```markdown
### 每小時任務 (10:00-22:00)

#### 10. Auto Optimization
- [ ] 執行趨勢分析
- [ ] 收集痛點
- [ ] 生成優化方案
- [ ] 實現優先級項目
- [ ] 產出文檔
```

### 方案 2: 手動 Cron（需要管理權限）

如果管理員安裝了 crontab：

```bash
# 安裝 crontab
apt-get install cron

# 設定每小時執行
echo '0 * * * * python3 /workspace/auto_optimizer/auto_optimizer.py' | crontab -
```

### 方案 3: 使用 systemd timer（需要 root）

```bash
# 建立 service
cat > /etc/systemd/system/auto-optimizer.service << EOF
[Unit]
Description=Auto Optimizer for methodology-v2

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /workspace/auto_optimizer/auto_optimizer.py
WorkingDirectory=/workspace
EOF

# 建立 timer
cat > /etc/systemd/system/auto-optimizer.timer << EOF
[Unit]
Description=Run auto-optimizer every hour

[Timer]
OnBootSec=1h
OnUnitActiveSec=1h
Unit=auto-optimizer.service

[Install]
WantedBy=timers.target
EOF

# 啟用
systemctl enable --now auto-optimizer.timer
```

## 目前狀態

- ✅ Auto Optimizer 腳本已創建
- ✅ 包含完整流程：趨勢→痛點→方案→實現→文檔
- ✅ **新增去重邏輯**：跳過已存在的項目（本地或 GitHub）
- ⏳ Cron 設定需管理權限

## 去重邏輯

```python
def is_duplicate(item_name, existing_projects):
    # 1. 精確匹配
    # 2. 關鍵字匹配
    # 3. 常見變體檢查
    # 回傳 True 表示重複，會跳過
```

### 檢查範圍
- `/workspace/methodology-v2/` 所有目錄
- `/workspace/` 根目錄其他相關目錄

### 強化版邏輯
如果是現有項目的強化版（如 "Enhanced Observability" 基於 "Observability"），可以實現：
```python
if 'enhance' in item_name.lower() or 'advanced' in item_name.lower():
    return False  # 允許強化版
```

## 手動執行

```bash
python3 /workspace/auto_optimizer/auto_optimizer.py
```

## 輸出

- 技術文章: `/workspace/evolution/auto-optimization-*.md`
- 日誌: `/workspace/evolution/cron.log`
