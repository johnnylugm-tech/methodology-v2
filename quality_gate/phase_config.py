#!/usr/bin/env python3
"""
Phase Configuration - Phase 1-8 詳細設定

定義每個 Phase 的名稱、AB 角色、所需產物等設定。
"""

# Phase 1-8 設定
PHASE_CONFIG = {
    1: {
        "name": "Phase 1 - 需求規格",
        "skill_section": "Phase 1 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "architect",
                "responsibility": "撰寫 SRS.md"
            },
            "agent_b": {
                "persona": "reviewer",
                "responsibility": "審查 FR 完整性"
            },
        },
        "required_artifacts": [
            "01-requirements/SRS.md",
            "01-requirements/SPEC_TRACKING.md",
            "DEVELOPMENT_LOG.md",
            "Phase1_STAGE_PASS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
        ],
    },
    2: {
        "name": "Phase 2 - 架構設計",
        "skill_section": "Phase 2 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "architect",
                "responsibility": "設計 SAD.md"
            },
            "agent_b": {
                "persona": "reviewer",
                "responsibility": "審查架構決策"
            },
        },
        "required_artifacts": [
            "02-architecture/SAD.md",
            "02-architecture/adr/",
            "DEVELOPMENT_LOG.md",
            "Phase2_STAGE_PASS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
            "ASPICE_COMPLETE",
        ],
    },
    3: {
        "name": "Phase 3 - 實作",
        "skill_section": "Phase 3 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "developer",
                "responsibility": "實作功能代碼"
            },
            "agent_b": {
                "persona": "reviewer",
                "responsibility": "Code Review"
            },
        },
        "required_artifacts": [
            "03-development/src/",
            "03-development/tests/",
            "DEVELOPMENT_LOG.md",
            "sessions_spawn.log",
            "Phase3_STAGE_PASS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
            "COVERAGE_THRESHOLD",
        ],
    },
    4: {
        "name": "Phase 4 - 驗證",
        "skill_section": "Phase 4 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "qa",
                "responsibility": "撰寫測試計畫"
            },
            "agent_b": {
                "persona": "tester",
                "responsibility": "執行測試"
            },
        },
        "required_artifacts": [
            "DEVELOPMENT_LOG.md",
            "Phase4_STAGE_PASS.md",
        ],
        "produced_artifacts": [
            "04-verification/TEST_PLAN.md",
            "04-verification/TEST_RESULTS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
            "TRACEABILITY_COMPLETE",
        ],
    },
    5: {
        "name": "Phase 5 - 系統測試",
        "skill_section": "Phase 5 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "qa",
                "responsibility": "執行系統測試"
            },
            "agent_b": {
                "persona": "developer",
                "responsibility": "修復系統測試問題"
            },
        },
        "required_artifacts": [
            "05-system-test/BASELINE.md",
            "05-system-test/SYSTEM_TEST_RESULTS.md",
            "DEVELOPMENT_LOG.md",
            "Phase5_STAGE_PASS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
            "ASPICE_COMPLETE",
        ],
    },
    6: {
        "name": "Phase 6 - 品質評估",
        "skill_section": "Phase 6 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "qa",
                "responsibility": "品質評估報告"
            },
            "agent_b": {
                "persona": "pm",
                "responsibility": "審查品質指標"
            },
        },
        "required_artifacts": [
            "06-quality/QUALITY_REPORT.md",
            "DEVELOPMENT_LOG.md",
            "Phase6_STAGE_PASS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
            "ASPICE_PHASE_TRACE",
        ],
    },
    7: {
        "name": "Phase 7 - 風險管理",
        "skill_section": "Phase 7 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "pm",
                "responsibility": "風險評估"
            },
            "agent_b": {
                "persona": "architect",
                "responsibility": "風險審查"
            },
        },
        "required_artifacts": [
            "07-risk/RISK_ASSESSMENT.md",
            "07-risk/RISK_REGISTER.md",
            "DEVELOPMENT_LOG.md",
            "Phase7_STAGE_PASS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
            "ASPICE_COMPLETE",
        ],
    },
    8: {
        "name": "Phase 8 - 配置管理",
        "skill_section": "Phase 8 詳細說明",
        "ab_roles": {
            "agent_a": {
                "persona": "devops",
                "responsibility": "配置記錄"
            },
            "agent_b": {
                "persona": "qa",
                "responsibility": "配置審查"
            },
        },
        "required_artifacts": [
            "08-configuration/CONFIG_RECORDS.md",
            "DEVELOPMENT_LOG.md",
            "Phase8_STAGE_PASS.md",
        ],
        "block_checks": [
            "SPEC_TRACKING",
            "CONSTITUTION_SCORE",
            "ASPICE_PHASE_TRACE",
        ],
    },
}


def get_phase_config(phase: int) -> dict:
    """取得指定 Phase 的設定"""
    return PHASE_CONFIG.get(phase, {})


def get_phase_name(phase: int) -> str:
    """取得指定 Phase 的名稱"""
    return PHASE_CONFIG.get(phase, {}).get("name", f"Phase {phase}")


def get_all_phases() -> list:
    """取得所有 Phase 設定"""
    return PHASE_CONFIG
