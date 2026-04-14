#!/usr/bin/env python3
"""Fix Phase 6 template content in cli.py"""

with open('cli.py', 'r') as f:
    content = f.read()

# Fix: Phase-specific deliverable structure
old_deliverable = '''            # Generate deliverable structure from modules
            deliverable_structure = self._generate_deliverable_structure(frs, modules)
            plan = plan.replace('{DELIVERABLE_STRUCTURE}', deliverable_structure)'''

phase6_deliverable = r'''            # Phase-specific deliverable structure
            if phase == 6:
                # Phase 6: Quality deliverables
                q6_d = "### Phase 6 產出結構\n\n"
                q6_d += "```\n"
                q6_d += "06-quality/\n"
                q6_d += "├── QUALITY_REPORT.md      # 品質報告（主產出）\n"
                q6_d += "└── MONITORING_PLAN.md    # 監控計畫\n"
                q6_d += "```\n\n"
                q6_d += "### Phase 6 交付物檢查清單\n\n"
                q6_d += "```markdown\n"
                q6_d += "## Phase 6 交付物\n\n"
                q6_d += "### 品質產出\n"
                q6_d += "- [ ] `06-quality/QUALITY_REPORT.md` - 品質維度評估報告\n"
                q6_d += "- [ ] `06-quality/MONITORING_PLAN.md` - 監控計畫\n\n"
                q6_d += "### 驗證產出\n"
                q6_d += "- [ ] Constitution 分數 >= 80%\n"
                q6_d += "- [ ] 邏輯正確性 >= 90\n"
                q6_d += "- [ ] Phase Truth >= 70%\n\n"
                q6_d += "### 文檔產出\n"
                q6_d += "- [ ] `sessions_spawn.log` - A/B session 完整記錄\n"
                q6_d += "- [ ] `AB_COLLABORATION.md` - Agent 協作記錄\n"
                q6_d += "```\n"
                deliverable_structure = q6_d
            else:
                deliverable_structure = self._generate_deliverable_structure(frs, modules)
            plan = plan.replace('{DELIVERABLE_STRUCTURE}', deliverable_structure)'''

content = content.replace(old_deliverable, phase6_deliverable)

# Fix: Phase-specific FR detailed tasks
old_fr_tasks = '''            # FR detailed tasks: placeholder only if not --detailed
            if not getattr(args, 'detailed', False):
                plan = plan.replace('{FR_DETAILED_TASKS}', self._generate_fr_detailed_tasks_placeholder(frs, modules, phase))
            else:
                # Remove placeholder line, will be replaced by merge later
                plan = plan.replace('{FR_DETAILED_TASKS}', '')'''

phase6_fr_tasks = r'''            # Phase-specific §5 content
            if phase == 6:
                # Phase 6: Quality evaluation tasks (not FR implementation)
                q6_t = "## 5. 品質評估任務（共 4 項）\n\n"
                q6_t += "### 5.1 品質維度定義\n\n"
                q6_t += "| 維度 | 指標 | 目標值 | 驗證方法 |\n"
                q6_t += "|------|------|--------|---------|\n"
                q6_t += "| 可維護性 | Constitution 分數 | >= 80% | constitution runner |\n"
                q6_t += "| 邏輯正確性 | 邏輯正確性分數 | >= 90 | phase-verify |\n"
                q6_t += "| 測試覆蓋率 | Coverage | >= 80% | pytest --cov |\n"
                q6_t += "| Phase Truth | Phase Truth 分數 | >= 70% | phase-verify |\n\n"
                q6_t += "### 5.2 品質評估任務\n\n"
                q6_t += "| 任務 | 負責 | 輸入 | 輸出 |\n"
                q6_t += "|------|------|------|------|\n"
                q6_t += "| 品質維度數據蒐集 | Agent A (qa) | TEST_RESULTS.md, BASELINE.md | 品質數據 |\n"
                q6_t += "| Constitution 檢查 | Agent A (qa) | 所有 Phase 產出 | 檢查報告 |\n"
                q6_t += "| 邏輯正確性驗證 | Agent B (architect) | 代碼, TEST_RESULTS | 驗證報告 |\n"
                q6_t += "| QUALITY_REPORT 撰寫 | Agent A (qa) | 所有檢查結果 | QUALITY_REPORT.md |\n\n"
                q6_t += "### 5.3 品質閾值\n\n"
                q6_t += "| TH | 指標 | 門檻 | 驗證命令 |\n"
                q6_t += "|----|------|------|---------|\n"
                q6_t += "| TH-02 | Constitution 總分 | >= 80% | `constitution/runner.py --type all` |\n"
                q6_t += "| TH-07 | 邏輯正確性 | >= 90 | `phase-verify` |\n\n"
                plan = plan.replace('{FR_DETAILED_TASKS}', q6_t)
            elif not getattr(args, 'detailed', False):
                plan = plan.replace('{FR_DETAILED_TASKS}', self._generate_fr_detailed_tasks_placeholder(frs, modules, phase))
            else:
                plan = plan.replace('{FR_DETAILED_TASKS}', '')'''

content = content.replace(old_fr_tasks, phase6_fr_tasks)

with open('cli.py', 'w') as f:
    f.write(content)

print("✅ Fixed: Phase-specific deliverable structure and FR tasks for Phase 6")
