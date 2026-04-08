# Phase Sub-Agent Management - All 8 Phases
# Includes: Need-to-Know, On-Demand, Tool Timing, Context Isolation

PHASE_SUBAGENT = {
    1: {
        "name": "需求規格",
        "agent_a": {"role": "architect", "task": "制定 SRS"},
        "agent_b": {"role": "reviewer", "task": "審查 SRS"},
        
        # Need-to-Know: 只給這個 phase 必要的資訊
        "need_to_know": {
            "read": [
                {"path": "TASK_INITIALIZATION_PROMPT.md", "section": "專案目標和約束", "why": "需要知道專案範圍"}
            ],
            "skip": ["SRS.md", "SAD.md", "Phase 3-8 產出"],
            "context": "single_phase"  # 只專注 Phase 1
        },
        
        # On-Demand: 需要時才請求額外資訊
        "on_demand": {
            "trigger": "當現有資訊不足以制定 FR 時",
            "request_to": "Johnny",
            "format": "列舉缺少的資訊（介面/效能/約束）"
        },
        
        # Tool timing: 何時用什麼工具
        "tool_timing": {
            "spawn": {
                "when": "一開始就派遣 architect",
                "tool": "sessions_spawn",
                "params": {"role": "architect", "fresh_messages": []}
            },
            "knowledge_curator": {
                "when": "派遣前",
                "tool": "KnowledgeCurator.verify_coverage",
                "check": "FR 覆蓋率 ≥80%"
            },
            "context_manager": {
                "when": "訊息 >50",
                "tool": "ContextManager.compress",
                "level": "L1"
            },
            "checkpoint": {
                "when": "每個 FR 完成後",
                "tool": "SessionManager.save",
                "path": ".methodology/checkpoints/p1-{fr}.json"
            }
        },
        
        # sessions_spawn isolation
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": [],  # 乾淨的 context
            "log_format": '{"timestamp","role","task","session_id","commit"}'
        }
    },
    
    2: {
        "name": "架構設計",
        "agent_a": {"role": "architect", "task": "制定 SAD+ADR"},
        "agent_b": {"role": "reviewer", "task": "審查 SAD"},
        
        "need_to_know": {
            "read": [
                {"path": "SRS.md", "section": "FR 需求和介面規格", "why": "需要對應每個 FR 到 Module"},
                {"path": "TASK_INITIALIZATION_PROMPT.md", "section": "約束", "why": "架構不能違背約束"}
            ],
            "skip": ["Phase 3-8 產出", "完整 SRS.md"],
            "context": "single_phase"
        },
        
        "on_demand": {
            "trigger": "當 SAD 某個 Module 對應不到 SRS 的 FR 時",
            "request_to": "Johnny 或回 Phase 1 修正",
            "format": "標註哪個 FR 遺漏或需要新增"
        },
        
        "tool_timing": {
            "spawn": {
                "when": "在 SRS Phase APPROVE 後",
                "tool": "sessions_spawn",
                "params": {"role": "architect", "fresh_messages": []}
            },
            "knowledge_curator": {
                "when": "派遣前",
                "tool": "KnowledgeCurator.verify_coverage",
                "check": "SRS→SAD trace 完整"
            },
            "context_manager": {
                "when": "訊息 >50",
                "tool": "ContextManager.compress",
                "level": "L1"
            },
            "quality_gate": {
                "when": "SAD 完成後",
                "tool": "sad_constitution_checker",
                "threshold": "≥80%"
            }
        },
        
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": [],
            "log_format": '{"timestamp","role","task","session_id","commit"}'
        }
    },
    
    3: {
        "name": "代碼實現",
        "agent_a": {"role": "developer", "task": "實作 FR-XX"},
        "agent_b": {"role": "reviewer", "task": "審查 FR-XX 代碼"},
        
        "need_to_know": {
            "read": [
                {"path": "SRS.md", "section": "§FR-XX 需求描述", "why": "只實作這個 FR 的功能"},
                {"path": "SAD.md", "section": "§Module 邊界對照表", "why": "知道 Module 介面和邊界"}
            ],
            "skip": ["完整 SRS.md", "完整 SAD.md", "其他 FR 的實作"],
            "context": "single_fr"  # 每個 FR 隔離
        },
        
        "on_demand": {
            "trigger": "當需要知道其他 FR 的實作細節時",
            "request_to": "N/A（不該發生，每個 FR 獨立）",
            "format": "返回錯誤：違反 Need-to-Know"
        },
        
        "tool_timing": {
            "spawn": {
                "when": "對於每個 FR，分別派遣 developer",
                "tool": "sessions_spawn",
                "params": {"role": "developer", "fr_id": "{fr}"}
            },
            "parallel": {
                "when": "多個 FR 無依賴時",
                "tool": "SubagentIsolator.parallel_spawn",
                "max_parallel": 3
            },
            "knowledge_curator": {
                "when": "派遣前",
                "tool": "KnowledgeCurator.verify_coverage",
                "check": "FR 已被理解"
            },
            "context_manager": {
                "when": "訊息 >30",  # 降低因為每個 FR 獨立
                "tool": "ContextManager.compress",
                "level": "L1"
            },
            "test_runner": {
                "when": "代碼完成後",
                "tool": "pytest",
                "params": {"path": "tests/test_{fr}.py", "cov": "≥70%"}
            },
            "quality_gate": {
                "when": "Reviewer APPROVE 後",
                "tool": "stage_pass",
                "check": "commit + push"
            }
        },
        
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": ["SRS.md §FR-XX", "SAD.md §Module"],
            "log_format": '{"timestamp","role","task","session_id","fr","confidence","commit"}'
        }
    },
    
    4: {
        "name": "測試規劃與執行",
        "agent_a": {"role": "qa", "task": "制定 TEST_PLAN + 執行"},
        "agent_b": {"role": "reviewer", "task": "審查測試"},
        
        "need_to_know": {
            "read": [
                {"path": "SRS.md", "section": "FR 需求和驗收標準", "why": "測試案例要對應 FR"},
                {"path": "SAD.md", "section": "Module 介面", "why": "測試介面邊界"},
                {"path": "src/", "section": "導出的公開介面", "why": "知道哪些要測試"}
            ],
            "skip": ["Phase 5-8 產出", "完整代碼庫"],
            "context": "single_phase"
        },
        
        "on_demand": {
            "trigger": "當需要特定單元測試的實現細節時",
            "request_to": "回到 Phase 3 的 developer",
            "format": "透過 GitHub commit 請求"
        },
        
        "tool_timing": {
            "spawn": {
                "when": "Phase 3 全部 APPROVE 後",
                "tool": "sessions_spawn",
                "params": {"role": "qa"}
            },
            "test_runner": {
                "when": "TEST_PLAN 完成後",
                "tool": "pytest",
                "params": {"markers": "integration"}
            },
            "coverage": {
                "when": "測試執行後",
                "tool": "CoverageReport",
                "check": "FR↔測試 映射率 ≥90%"
            }
        },
        
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": [],
            "log_format": '{"timestamp","role","task","session_id","commit"}'
        }
    },
    
    5: {
        "name": "驗證交付",
        "agent_a": {"role": "devops", "task": "建立 Baseline + Monitoring"},
        "agent_b": {"role": "architect", "task": "審查 Baseline"},
        
        "need_to_know": {
            "read": [
                {"path": "TEST_RESULTS.md", "section": "通過/失敗統計", "why": "建立效能基準"},
                {"path": "SRS.md", "section": "效能需求和約束", "why": "確保 Baseline 符合要求"}
            ],
            "skip": ["Phase 6-8 產出", "詳細測試案例"],
            "context": "single_phase"
        },
        
        "on_demand": {
            "trigger": "當測試結果與 SRS 效能約束不符時",
            "request_to": "回到 Phase 3/4 修正",
            "format": "建立 Issue 追蹤"
        },
        
        "tool_timing": {
            "spawn": {
                "when": "Phase 4 APPROVE 後",
                "tool": "sessions_spawn",
                "params": {"role": "devops"}
            },
            "monitoring": {
                "when": "Baseline 建立後",
                "tool": "setup_monitoring",
                "check": "警報閾值合理"
            }
        },
        
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": [],
            "log_format": '{"timestamp","role","task","session_id","commit"}'
        }
    },
    
    6: {
        "name": "品質保證",
        "agent_a": {"role": "qa", "task": "生成 QUALITY_REPORT"},
        "agent_b": {"role": "architect", "task": "審查品質"},
        
        "need_to_know": {
            "read": [
                {"path": "TEST_RESULTS.md", "section": "失敗案例", "why": "分析品質問題"},
                {"path": "BASELINE.md", "section": "效能數據", "why": "對比品質趨勢"}
            ],
            "skip": ["Phase 7-8 產出", "完整測試日誌"],
            "context": "single_phase"
        },
        
        "on_demand": {
            "trigger": "當需要根本原因分析時",
            "request_to": "回到 Phase 3/4 請求詳細日誌",
            "format": "透過 GitHub Issue"
        },
        
        "tool_timing": {
            "spawn": {
                "when": "Phase 5 APPROVE 後",
                "tool": "sessions_spawn",
                "params": {"role": "qa"}
            },
            "quality_gate": {
                "when": "QUALITY_REPORT 完成後",
                "tool": "ConstitutionRunner",
                "threshold": "≥80%"
            }
        },
        
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": [],
            "log_format": '{"timestamp","role","task","session_id","commit"}'
        }
    },
    
    7: {
        "name": "風險管理",
        "agent_a": {"role": "qa", "task": "識別風險 + 制定緩解"},
        "agent_b": {"role": "pm", "task": "審查風險"},
        
        "need_to_know": {
            "read": [
                {"path": "QUALITY_REPORT.md", "section": "問題和風險章節", "why": "識別已知風險"},
                {"path": "SRS.md", "section": "約束和假設", "why": "識別潛在風險"}
            ],
            "skip": ["Phase 8 產出", "詳細程式碼"],
            "context": "single_phase"
        },
        
        "on_demand": {
            "trigger": "當需要具體技術風險的細節時",
            "request_to": "回到 Phase 3 的 developer",
            "format": "透過 GitHub commit comment"
        },
        
        "tool_timing": {
            "spawn": {
                "when": "Phase 6 APPROVE 後",
                "tool": "sessions_spawn",
                "params": {"role": "qa"}
            },
            "risk_matrix": {
                "when": "風險識別完成後",
                "tool": "calculate_risk_score",
                "check": "機率 × 影響"
            }
        },
        
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": [],
            "log_format": '{"timestamp","role","task","session_id","commit"}'
        }
    },
    
    8: {
        "name": "配置管理",
        "agent_a": {"role": "devops", "task": "建立配置管理系統"},
        "agent_b": {"role": "pm", "task": "審查配置"},
        
        "need_to_know": {
            "read": [
                {"path": "RISK_REGISTER.md", "section": "已知風險", "why": "配置要支援風險緩解"},
                {"path": "BASELINE.md", "section": "配置快照", "why": "確保可重現"},
                {"path": "QUALITY_REPORT.md", "section": "問題", "why": "配置要避免已知問題"}
            ],
            "skip": ["其他 Phase 產出"],
            "context": "single_phase"
        },
        
        "on_demand": {
            "trigger": "當需要特定元件的版本歷史時",
            "request_to": "查閱 Git history",
            "format": "git log --oneline"
        },
        
        "tool_timing": {
            "spawn": {
                "when": "Phase 7 APPROVE 後",
                "tool": "sessions_spawn",
                "params": {"role": "devops"}
            },
            "lock_deps": {
                "when": "配置完成後",
                "tool": "pip freeze > requirements.lock",
                "check": "與 BASELINE.md 一致"
            },
            "deployment_check": {
                "when": "所有配置完成後",
                "tool": "verify_deployment_checklist",
                "check": "100% 可執行"
            }
        },
        
        "isolation": {
            "method": "SubagentIsolator.spawn",
            "fresh_messages": [],
            "log_format": '{"timestamp","role","task","session_id","commit"}'
        }
    }
}


def get_subagent_config(phase: int) -> dict:
    """取得指定 Phase 的子代理配置"""
    return PHASE_SUBAGENT.get(phase, PHASE_SUBAGENT[3])


def get_tool_timing(phase: int, event: str) -> dict:
    """取得特定 Phase 在特定事件時應使用的工具"""
    config = get_subagent_config(phase)
    return config.get("tool_timing", {}).get(event, {})


def get_need_to_know(phase: int) -> dict:
    """取得指定 Phase 的 Need-to-Know 規範"""
    config = get_subagent_config(phase)
    return config.get("need_to_know", {})


def get_on_demand_config(phase: int) -> dict:
    """取得指定 Phase 的 On-Demand 規範"""
    config = get_subagent_config(phase)
    return config.get("on_demand", {})


# Phase-specific Four-Dimensional Goals and Iteration Rounds
# This extends PHASE_SUBAGENT with iteration-specific information

PHASE_ITERATION = {
    1: {
        "name": "需求規格",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "HR-15 citations", "method": "grep -c '\\[FR-' SRS.md"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "Traceability": {"target": "10/10", "metric": "FR↔NFR 映射", "method": "每個 FR 有對應 NFR"}
        },
        "rounds": [
            {"round": 1, "goal": "基礎 FR 識別", "deliverable": "FR 列表 + 初步描述"},
            {"round": 2, "goal": "NFR 補充", "deliverable": "NFR 列表 + 約束條件"},
            {"round": 3, "goal": "介面規格", "deliverable": "API 規格 + 錯誤處理"},
            {"round": 4, "goal": "Traceability 建立", "deliverable": "TRACEABILITY_MATRIX.md"},
            {"round": 5, "goal": "完整審查", "deliverable": "SRS.md APPROVE"}
        ]
    },
    2: {
        "name": "架構設計",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "SAD↔SRS 一致性", "method": "每個 FR 有對應 Module"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "模組化": {"target": "10/10", "metric": "Module 邊界清晰", "method": "每個 Module 單一職責"}
        },
        "rounds": [
            {"round": 1, "goal": "基礎架構", "deliverable": "SAD.md 初步架構"},
            {"round": 2, "goal": "Module 邊界", "deliverable": "Module 介面定義"},
            {"round": 3, "goal": "介面定義", "deliverable": "API 規格 + 資料流"},
            {"round": 4, "goal": "ADR 記錄", "deliverable": "ADR.md 關鍵決策"},
            {"round": 5, "goal": "SAD↔SRS 驗證", "deliverable": "SAD.md APPROVE"}
        ]
    },
    3: {
        "name": "代碼實現",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "HR-15 citations + docstring [FR-XX]", "method": "grep -c '\\[FR-' app/**/*.py"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "測試覆蓋率": {"target": "10/10", "metric": "pytest PASS + coverage ≥80%", "method": "pytest --cov=app/ -v"}
        },
        "rounds": [
            {"round": 1, "goal": "基礎實作", "deliverable": "代碼 + 測試 + pytest PASS"},
            {"round": 2, "goal": "Production-ready", "deliverable": "logging + error handling"},
            {"round": 3, "goal": "穩定化", "deliverable": "pytest 持續 PASS"},
            {"round": 4, "goal": "HR-15 落實", "deliverable": "citations 含行號"},
            {"round": 5, "goal": "A/B 協作", "deliverable": "sessions_spawn.log 完整"}
        ]
    },
    4: {
        "name": "測試規劃",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "FR↔測試 映射率 ≥90%", "method": "每個 FR 有對應測試案例"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "關鍵路徑覆蓋": {"target": "10/10", "metric": "關鍵路徑覆蓋 100%", "method": "測試覆蓋率報告"}
        },
        "rounds": [
            {"round": 1, "goal": "測試策略", "deliverable": "TEST_PLAN.md 測試策略"},
            {"round": 2, "goal": "測試案例", "deliverable": "測試案例覆蓋所有 FR"},
            {"round": 3, "goal": "環境設置", "deliverable": "測試環境隔離"},
            {"round": 4, "goal": "執行與記錄", "deliverable": "TEST_RESULTS.md"},
            {"round": 5, "goal": "覆蓋率分析", "deliverable": "COVERAGE_REPORT.md"}
        ]
    },
    5: {
        "name": "驗證交付",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "Baseline 符合 SRS 約束", "method": "效能數據對照 SRS"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "監控覆蓋": {"target": "10/10", "metric": "監控指標覆蓋 100%", "method": "MONITORING_PLAN.md 完整性"}
        },
        "rounds": [
            {"round": 1, "goal": "效能基準", "deliverable": "BASELINE.md 效能基準"},
            {"round": 2, "goal": "監控設置", "deliverable": "監控指標定義"},
            {"round": 3, "goal": "警報配置", "deliverable": "警報閾值合理"},
            {"round": 4, "goal": "驗證報告", "deliverable": "VERIFICATION_REPORT.md"},
            {"round": 5, "goal": "交付準備", "deliverable": "交付檢查清單完成"}
        ]
    },
    6: {
        "name": "品質保證",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "Constitution ≥80%", "method": "Constitution runner"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "邏輯正確性": {"target": "10/10", "metric": "邏輯正確性 ≥90%", "method": "QUALITY_REPORT.md"}
        },
        "rounds": [
            {"round": 1, "goal": "品質維度定義", "deliverable": "品質維度列表"},
            {"round": 2, "goal": "指標測量", "deliverable": "指標數據收集"},
            {"round": 3, "goal": "問題分析", "deliverable": "問題清單 + 優先級"},
            {"round": 4, "goal": "修復計畫", "deliverable": "修復計畫文件"},
            {"round": 5, "goal": "最終報告", "deliverable": "QUALITY_REPORT.md APPROVE"}
        ]
    },
    7: {
        "name": "風險管理",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "所有風險有緩解計畫", "method": "RISK_REGISTER.md 完整性"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "風險評估合理性": {"target": "10/10", "metric": "機率×影響 合理", "method": "風險分數對照"}
        },
        "rounds": [
            {"round": 1, "goal": "風險識別", "deliverable": "風險清單"},
            {"round": 2, "goal": "評估與分類", "deliverable": "風險分數 + 等級"},
            {"round": 3, "goal": "緩解計畫", "deliverable": "RISK_MITIGATION_PLANS.md"},
            {"round": 4, "goal": "責任分配", "deliverable": "每個風險有負責人"},
            {"round": 5, "goal": "追蹤機制", "deliverable": "追蹤機制文件化"}
        ]
    },
    8: {
        "name": "配置管理",
        "four_dimensional": {
            "規範符合度": {"target": "10/10", "metric": "requirements.lock 一致性", "method": "pip freeze == requirements.lock"},
            "A/B 協作": {"target": "10/10", "metric": "sessions_spawn.log", "method": "developer + reviewer 各 1 筆記錄"},
            "子代理管理": {"target": "10/10", "metric": "SubagentIsolator", "method": "fresh_messages 隔離"},
            "部署檢查覆蓋": {"target": "10/10", "metric": "部署檢查清單 100%", "method": "DEPLOYMENT_CHECKLIST.md 完整性"}
        },
        "rounds": [
            {"round": 1, "goal": "配置審計", "deliverable": "CONFIG_RECORDS.md"},
            {"round": 2, "goal": "依賴鎖定", "deliverable": "requirements.lock"},
            {"round": 3, "goal": "環境規格", "deliverable": "ENVIRONMENT_SPEC.md"},
            {"round": 4, "goal": "部署腳本", "deliverable": "部署腳本可用"},
            {"round": 5, "goal": "最終驗證", "deliverable": "DEPLOYMENT_CHECKLIST.md APPROVE"}
        ]
    }
}


def get_phase_iteration(phase: int) -> dict:
    """取得指定 Phase 的迭代配置"""
    return PHASE_ITERATION.get(phase, PHASE_ITERATION[3])


def get_four_dimensional_table(phase: int) -> str:
    """產生四維度 Markdown 表格"""
    iteration = get_phase_iteration(phase)
    lines = []
    lines.append("| 維度 | 目標 | 指標 | 評估方法 |")
    lines.append("|------|------|------|---------|")
    for dim, info in iteration["four_dimensional"].items():
        lines.append(f"| **{dim}** | {info['target']} | {info['metric']} | {info['method']} |")
    return "\n".join(lines)


def get_iteration_rounds_table(phase: int) -> str:
    """產生迭代輪次 Markdown 表格"""
    iteration = get_phase_iteration(phase)
    lines = []
    lines.append("### 每輪目標")
    lines.append("")
    lines.append("| Round | 目標 | 交付物 |")
    lines.append("|-------|------|--------|")
    for r in iteration["rounds"]:
        lines.append(f"| Round {r['round']} | {r['goal']} | {r['deliverable']} |")
    return "\n".join(lines)
