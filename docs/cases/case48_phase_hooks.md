# Case 48: Phase Hooks - 階段強制鉤子

## 問題背景

在傳統的開發流程中，階段之間的轉換往往缺乏強制性的驗證：

- Development 完成後沒有確保測試通過就進入 Verification
- Verification 跳過安全掃描直接進入 Release
- Release 沒有確認審批就直接發布

這些漏洞導致品質把關淪為形式，技術債不斷累積。

---

## 解決方案：Phase Hooks

### 核心設計

```
階段轉換邏輯：
┌─────────────┐    execute_phase()    ┌─────────────┐
│  Development │ ──────────────────→ │  Verifiction │
└─────────────┘                       └─────────────┘
      ↑                                       ↑
      │          can_proceed()                 │
      └───────────────────────────────────────┘
      
只有在所有 required hooks 通過後才能進入下一階段
```

### 鉤子執行流程

```
鉤子執行：
hook_1 ──→ PASS ──→ hook_2 ──→ PASS ──→ hook_3
              │                              │
              └── FAIL (required) ──→ STOP ←─┘
```

### 預設鉤子配置

| 階段 | 鉤子 ID | 名稱 | 命令 | 必填 |
|------|---------|------|------|------|
| development | dev-lint | 語法檢查 | `python3 -m py_compile` | ✓ |
| development | dev-test | 單元測試 | `python3 -m unittest` | ✓ |
| development | dev-constitution | Constitution 合規 | `python3 cli.py constitution check` | ✓ |
| verification | verify-quality | Quality Gate | `python3 cli.py quality gate` | ✓ |
| verification | verify-security | 安全掃描 | `python3 cli.py guardrails scan` | ✓ |
| verification | verify-coverage | 覆蓋率檢查 | `python3 -m coverage report` | ✗ |
| release | release-approval | 審批確認 | `python3 cli.py approval pending` | ✓ |
| release | release-version | 版本確認 | `echo $VERSION` | ✓ |
| release | release-changelog | 更新日誌 | `cat CHANGELOG.md` | ✓ |

---

## 使用範例

### 1. 初始化並執行鉤子

```python
from anti_shortcut import PhaseHooks, Phase

# 初始化
hooks = PhaseHooks()

# 執行 development 階段
result = hooks.execute_phase(Phase.DEVELOPMENT)

print(f"Phase: {result.phase.value}")
print(f"Status: {result.status.value}")
print(f"Completed: {result.completed_at}")

for hook in result.hooks:
    print(f"  - {hook.name}: {hook.status.value}")
```

**輸出：**
```
Phase: development
Status: passed
Completed: 2026-03-23T18:30:00
  - 語法檢查: passed
  - 單元測試: passed
  - Constitution 合規: passed
```

### 2. 檢查階段轉換

```python
# 檢查是否可以進入下一階段
can_proceed, reason = hooks.can_proceed(
    from_phase=Phase.DEVELOPMENT,
    to_phase=Phase.VERIFICATION
)

if can_proceed:
    print("✓ 可以進入 Verification 階段")
else:
    print(f"✗ 阻止：{reason}")
```

### 3. 取得失敗的鉤子

```python
failed = hooks.get_failed_hooks(Phase.DEVELOPMENT)

for hook in failed:
    print(f"Failed: {hook.name}")
    print(f"Error: {hook.error}")
```

### 4. 取得完整狀態

```python
# 單一階段狀態
status = hooks.get_status(Phase.DEVELOPMENT)
print(status)

# 所有階段狀態
all_status = hooks.get_status()
```

### 5. 跳過鉤子（有理由）

```python
# 緊急情況下可跳過非必填鉤子
success = hooks.skip_hook(
    hook_id="verify-coverage",
    reason="緊急 hotfix，coverage 稍後補上"
)

if success:
    print("鉤子已標記為跳過")
```

---

## 與 Anti-Shortcut Enforcer 的整合

Phase Hooks 是 Anti-Shortcut 系統的延伸：

```python
from anti_shortcut import PhaseHooks, AntiShortcutEnforcer

hooks = PhaseHooks()
enforcer = AntiShortcutEnforcer()

# 在執行鉤子前檢查是否有未確認的違規
violations = enforcer.get_unacknowledged_violations()

if violations:
    print(f"Warning: {len(violations)} unacknowledged violations")
    # 可以選擇阻止或警告
```

---

## 設計理念

### 為什麼要強制鉤子？

1. **防止遺漏**：人類會忘記執行檢查，自動化不會
2. **一致性**：每次階段轉換都執行相同的驗證
3. **可追溯**：鉤子執行結果都有記錄
4. **阻擋捷徑**：沒有通過驗證就不能繼續

### 為什麼非必填鉤子？

有些檢查是「最好有」但不是「必須有」：

- 覆蓋率檢查：可以接受低覆蓋率，但要記錄
- 某些安全掃描：在緊急修復時可以跳過

關鍵是：**跳過必須是可見的、有理由的，而不是默默發生的。**

---

## CLI 整合

```bash
# 執行 development 階段的鉤子
python3 cli.py phase execute development

# 檢查狀態
python3 cli.py phase status

# 檢查是否可以轉換階段
python3 cli.py phase can-proceed development verification

# 跳過鉤子
python3 cli.py phase skip verify-coverage "緊急修復"
```

---

## 總結

Phase Hooks 為每個階段轉換提供了強制性的品質關卡：

```
沒有鉤子：階段轉換靠自覺
有鉤子：階段轉換靠驗證
鉤子通過：才能繼續前進
```

這確保了：
- Development 的產出經過測試和合規檢查
- Verification 的產出經過品質和安全驗證
- Release 的產出經過審批和版本確認
