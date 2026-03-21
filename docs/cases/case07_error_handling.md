# 案例七：錯誤處理與例外情境

## 概述

本案例收錄所有工作流程的錯誤處理範例，涵蓋 L1-L4 錯誤分類、Timeout 處理、資源限制、認證失敗等常見情境。

---

## 6 大工作流程錯誤處理

| 工作流程 | 錯誤類型 | 處理方式 |
|---------|---------|---------|
| 1. Setup Wizard | 初始化失敗、參數錯誤 | 友好提示、重試 |
| 2. Development | 編譯錯誤、測試失敗 | 分類+修復 |
| 3. Evaluation | 評估超時、模型無回應 | 重試+降級 |
| 4. Data Flow | 格式錯誤、解析失敗 | 驗證+跳過 |
| 5. Enterprise | SSO 失敗、權限不足 | 認證+提示 |
| 6. Migration | 遷移失敗、相容性問題 | 回滾+紀錄 |

---

## 案例 7.1：Setup Wizard 錯誤處理

### 錯誤 7.1.1：初始化失敗

```python
from methodology import SetupWizard

wizard = SetupWizard()

try:
    config = wizard.create_project(
        name="my-project",
        use_case="customer_service"
    )
except wizard.InitError as e:
    if e.code == "DIR_EXISTS":
        print(f"目錄已存在: {e.path}")
        # 解決：使用現有目錄或刪除
        config = wizard.create_project(
            name="my-project",
            use_case="customer_service",
            force=True  # 強制覆寫
        )
    elif e.code == "INVALID_USE_CASE":
        print(f"不支援的 Use Case: {e.value}")
        # 解決：列出可用選項
        print("可用選項:", wizard.get_use_cases())
```

### 錯誤 7.1.2：參數驗證失敗

```python
try:
    config = wizard.create_project(
        name="123-invalid",  # 不允許數字開頭
        use_case="customer_service"
    )
except wizard.ValidationError as e:
    print(f"驗證失敗: {e.field}")
    print(f"原因: {e.message}")
    # 輸出: 驗證失敗: name
    # 原因: 必須以字母開頭，長度 3-50 字元
```

---

## 案例 7.2：Development Flow 錯誤處理

### 錯誤 7.2.1：編譯錯誤

```python
from methodology import TaskSplitter, ErrorClassifier

splitter = TaskSplitter()
classifier = ErrorClassifier()

try:
    tasks = splitter.split_from_goal("開發登入功能")
except splitter.CompileError as e:
    level = classifier.classify(e)
    
    if level == ErrorLevel.L1:
        # 語法錯誤，立即顯示
        print(f"語法錯誤: {e.line}:{e.column} - {e.message}")
        # 解決：修正語法
        
    elif level == ErrorLevel.L2:
        # 依賴錯誤，重試解析
        print(f"依賴錯誤: {e.package}")
        for i in range(3):
            try:
                tasks = splitter.retry()
                break
            except Exception as retry_err:
                if i == 2:
                    raise
                time.sleep(2 ** i)  # 指數退避
```

### 錯誤 7.2.2：測試失敗

```python
from methodology import QualityGate, ErrorHandler

gate = QualityGate()
handler = ErrorHandler()

result = gate.run_tests("tests/login_test.py")

if not result.passed:
    for failure in result.failures:
        level = classifier.classify(failure)
        action = handler.get_action(level)
        
        print(f"測試失敗: {failure.test_name}")
        print(f"  等級: {level.value}")
        print(f"  錯誤: {failure.error_message}")
        
        if level == ErrorLevel.L1:
            # 輸入驗證錯誤，立即修復
            fix = gate.suggest_fix(failure)
            print(f"  建議: {fix}")
            
        elif level == ErrorLevel.L3:
            # 執行環境問題，降級處理
            print(f"  行動: {action}")
            gate.skip_test(failure.test_name)
```

---

## 案例 7.3：Evaluation Flow 錯誤處理

### 錯誤 7.3.1：評估超時

```python
from methodology import AgentEvaluator, ErrorLevel

evaluator = AgentEvaluator()

try:
    result = evaluator.run_evaluation(
        agent=my_agent,
        test_cases=test_suite,
        timeout=30  # 30 秒超時
    )
except evaluator.TimeoutError as e:
    print(f"評估超時: {e.elapsed}s / {e.limit}s")
    
    if e.elapsed > e.limit * 0.8:
        # 接近超時，降級處理
        result = evaluator.run_evaluation(
            agent=my_agent,
            test_cases=test_suite[:5],  # 只跑前 5 個
            timeout=60
        )
        print(f"降級執行: {len(result.passed)}/{len(test_suite[:5])} 通過")
```

### 錯誤 7.3.2：模型無回應

```python
try:
    result = evaluator.evaluate_agent(
        agent=my_agent,
        prompt="複雜的分析任務"
    )
except evaluator.ModelNotRespondingError as e:
    print(f"模型無回應: {e.model}")
    
    # 切換到備用模型
    evaluator.set_backup_model("claude-3")
    result = evaluator.evaluate_agent(
        agent=my_agent,
        prompt="複雜的分析任務",
        use_backup=True
    )
    print(f"備用模型結果: {result.score}")
```

---

## 案例 7.4：Data Flow 錯誤處理

### 錯誤 7.4.1：資料格式錯誤

```python
from methodology import StructuredOutputEngine, ErrorLevel

engine = StructuredOutputEngine()

result = engine.parse(
    prompt="擷取用戶資訊",
    llm_call=llm_fn,
    schema=user_schema
)

if not result.success:
    error = result.error
    
    if error.type == "JSONDecodeError":
        # JSON 解析失敗
        print(f"解析失敗: {error.raw_text[:50]}...")
        # 嘗試修復
        fixed = engine.repair_json(error.raw_text)
        result = engine.parse_with_fixed(fixed)
        
    elif error.type == "ValidationError":
        # 欄位驗證失敗
        print(f"欄位錯誤: {error.field}")
        print(f"預期: {error.expected}")
        print(f"實際: {error.actual}")
        
        # 使用預設值
        result = engine.parse_with_defaults(
            prompt="擷取用戶資訊",
            llm_call=llm_fn,
            schema=user_schema,
            use_defaults=True
        )
```

### 錯誤 7.4.2：資料品質問題

```python
from methodology import DataQualityChecker, ErrorLevel

checker = DataQualityChecker()

report = checker.analyze(data, field_types)

for issue in report.issues:
    level = classifier.classify(issue)
    
    if level == ErrorLevel.L1:
        # 格式錯誤，跳過該筆資料
        print(f"跳過: Row {issue.row_id} - {issue.field}")
        
    elif level == ErrorLevel.L2:
        # 可修復問題，自動清理
        if issue.type == "missing_value":
            data[issue.row_id][issue.field] = checker.fill_null(
                data, issue.field, strategy="median"
            )
```

---

## 案例 7.5：Enterprise Flow 錯誤處理

### 錯誤 7.5.1：SSO 認證失敗

```python
from methodology import SSOIntegration, ErrorLevel

sso = SSOIntegration()

try:
    token = sso.authenticate(
        provider="okta",
        domain="company.okta.com",
        client_id="xxx"
    )
except sso.AuthError as e:
    if e.code == "INVALID_CREDENTIALS":
        print("認證失敗: 請檢查憑證")
        # 解決：重新輸入或重置密碼
        
    elif e.code == "TOKEN_EXPIRED":
        print("Token 過期: 自動刷新")
        token = sso.refresh_token(e.refresh_token)
        
    elif e.code == "PERMISSION_DENIED":
        print(f"權限不足: {e.required_permission}")
        # 解決：聯繫管理員
        sso.request_permission(e.required_permission)
```

### 錯誤 7.5.2：API 配額超限

```python
try:
    result = enterprise.call_api("create_user", data=user_data)
except enterprise.QuotaExceededError as e:
    print(f"API 配額超限: {e.used}/{e.limit}")
    
    # 計算等待時間
    wait_time = e.reset_time - datetime.now()
    print(f"等待重置: {wait_time.seconds} 秒")
    
    # 或使用備用方案
    result = enterprise.call_api(
        "create_user",
        data=user_data,
        use_backup=True  # 切換到備用 API Key
    )
```

---

## 案例 7.6：Migration Flow 錯誤處理

### 錯誤 7.6.1：遷移失敗

```python
from methodology import LangGraphMigrationTool

tool = LangGraphMigrationTool()

result = tool.migrate_file(
    source="old_agent.py",
    target="new_agent.py"
)

if not result.success:
    for error in result.errors:
        print(f"遷移錯誤: {error.location}")
        print(f"  類型: {error.type}")
        print(f"  訊息: {error.message}")
        
        if error.type == "UNSUPPORTED_NODE":
            # 不支援的節點類型
            print(f"  建議: 手動遷移或忽略")
            result.ignore_error(error.location)
            
        elif error.type == "TYPE_INFERENCE":
            # 類型推斷失敗
            print(f"  建議: 明確指定類型")
            tool.add_type_hint(error.location, expected_type="str")
```

### 錯誤 7.6.2：遷移後驗證失敗

```python
result = tool.migrate_and_validate(
    source="old_agent.py",
    target="new_agent.py"
)

if not result.validation_passed:
    print("驗證失敗:")
    for failure in result.validation_failures:
        print(f"  - {failure.check}: {failure.message}")
    
    # 回滾到遷移前狀態
    print("執行回滾...")
    tool.rollback()
    print("已回滾至遷移前狀態")
    
    # 或繼續修復
    result = tool.migrate_with_fixes(
        source="old_agent.py",
        target="new_agent.py",
        fixes=result.validation_failures
    )
```

---

## L1-L4 錯誤分類速查表

| 等級 | 類型 | 範例 | 處理方式 |
|------|------|------|---------|
| **L1** | 輸入錯誤 | 格式錯誤、參數無效 | 立即返回、提示用戶 |
| **L2** | 工具錯誤 | 網路超時、API 錯誤 | 重試 3 次、指數退避 |
| **L3** | 執行錯誤 | 記憶體不足、超時 | 降級處理、釋放資源 |
| **L4** | 系統錯誤 | 服務癱瘓、認證系統崩潰 | 熔斷電路、發送警報 |

---

## 相關功能

| 功能 | 模組 |
|------|------|
| 錯誤分類 | `ErrorClassifier` |
| 錯誤處理 | `ErrorHandler` |
| 熔斷管理 | `FailoverManager` |
| 資料品質 | `DataQualityChecker` |
| SSO 整合 | `SSOIntegration` |
| 遷移工具 | `LangGraphMigrationTool` |
