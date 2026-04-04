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
