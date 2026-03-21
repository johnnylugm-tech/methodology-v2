#!/usr/bin/env python3
"""Auto Optimizer - 每小時自動優化 methodology-v2"""
import os, sys, json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
METHODOLOGY_V2 = WORKSPACE
OUTPUT_DIR = WORKSPACE / "memory" / "evolution"
LOCK_FILE = Path(__file__).parent / ".last_run"


def should_run():
    if not LOCK_FILE.exists():
        return True
    with open(LOCK_FILE) as f:
        last = f.read().strip()
    if not last:
        return True
    last_dt = datetime.strptime(last, "%Y%m%d_%H%M%S")
    now_dt = datetime.now()
    return last_dt.hour != now_dt.hour or last_dt.day != now_dt.day


def mark_run():
    with open(LOCK_FILE, "w") as f:
        f.write(datetime.now().strftime("%Y%m%d_%H%M%S"))


class AutoOptimizer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run(self):
        print(f"[{self.timestamp}] 開始自動優化...")
        trends = self.collect_trends()
        pain_points = self.collect_pain_points()
        proposal = self.generate_proposal(trends, pain_points)
        if proposal.get("priority_item"):
            self.implement(proposal["priority_item"])
        self.generate_docs(proposal)
        print(f"[{self.timestamp}] 自動優化完成!")
        return self.results
    
    def collect_trends(self):
        print("📊 收集趨勢...")
        trends = []
        default_trends = [
            {"topic": "Multi-Agent Orchestration", "description": "多 Agent 協作"},
            {"topic": "MCP/A2A Protocol", "description": "建立 Agent 互聯網標準"},
            {"topic": "Enterprise AI Scaling", "description": "從實驗到生產"},
            {"topic": "Agent Governance", "description": "安全成為關鍵"},
            {"topic": "FinOps for AI", "description": "成本優化"},
        ]
        try:
            import urllib.request
            url = "https://api.github.com/search/repositories?q=ai+agent+created:>2025-01-01&sort=stars&order=desc"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read())
                for item in data.get('items', [])[:5]:
                    trends.append({"topic": item['name'], "description": item.get('description', '')[:100], "stars": item['stargazers_count']})
                print(f"   從 GitHub 獲取 {len(trends)} 個趨勢")
        except Exception as e:
            print(f"   使用預設熱點: {e}")
            trends = default_trends
        self.results["trends"] = trends
        return trends
    
    def collect_pain_points(self):
        print("😰 收集痛點...")
        default_pain_points = [
            {"issue": "學習曲線", "priority": "high"},
            {"issue": "缺乏安全性", "priority": "high"},
            {"issue": "擴展困難", "priority": "medium"},
            {"issue": "監控不足", "priority": "medium"},
        ]
        self.results["pain_points"] = default_pain_points
        return default_pain_points
    
    def get_existing_projects(self):
        print("🔍 檢查已存在項目...")
        existing = set()
        if METHODOLOGY_V2.exists():
            for item in METHODOLOGY_V2.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    existing.add(item.name.lower())
        for base in [WORKSPACE]:
            if base.exists():
                for item in base.iterdir():
                    if item.is_dir() and item.name not in ['.git', 'node_modules', '__pycache__']:
                        existing.add(item.name.lower())
        print(f"   已存在: {len(existing)} 個項目")
        return existing
    
    def is_duplicate(self, item_name, existing_projects):
        name_lower = item_name.lower().replace('-', ' ').replace('_', ' ')
        for existing in existing_projects:
            if existing.lower() == name_lower:
                return True
            keywords = existing.lower().split()
            for kw in keywords:
                if len(kw) > 3 and kw in name_lower:
                    return True
        return False
    
    def generate_proposal(self, trends, pain_points):
        print("📝 生成優化方案...")
        existing = self.get_existing_projects()
        candidates = [
            {"name": "Enhanced Observability", "description": "增強可觀測性", "priority": "P0"},
            {"name": "Advanced Security", "description": "進階安全防護", "priority": "P0"},
            {"name": "Performance Optimizer", "description": "效能優化器", "priority": "P1"},
            {"name": "Cost Analyzer", "description": "成本分析器", "priority": "P1"},
            {"name": "Auto Debugger", "description": "自動調試器", "priority": "P1"},
            {"name": "API Gateway", "description": "API 閘道", "priority": "P2"},
            {"name": "Workflow Templates", "description": "工作流範本庫", "priority": "P2"},
            {"name": "Agent Memory", "description": "Agent 記憶系統", "priority": "P2"},
        ]
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        candidates.sort(key=lambda x: priority_order.get(x["priority"], 3))
        skipped = []
        unique_candidates = []
        for c in candidates:
            if self.is_duplicate(c["name"], existing):
                skipped.append(c["name"])
                print(f"   ⏭️  跳過: [{c['priority']}] {c['name']}")
            else:
                unique_candidates.append(c)
                print(f"   ✅ 通過: [{c['priority']}] {c['name']}")
        priority_item = unique_candidates[0] if unique_candidates else {
            "name": "Enhancement Pack", "description": "現有模組強化包", "priority": "P0"
        }
        proposal = {
            "timestamp": self.timestamp,
            "trends_count": len(trends),
            "pain_points_count": len(pain_points),
            "skipped": skipped,
            "priority_item": priority_item,
        }
        self.results["proposal"] = proposal
        return proposal
    
    def implement(self, item):
        print(f"🔧 實現: {item['name']}...")
        item_name = item["name"]
        project_dir = METHODOLOGY_V2 / item_name.replace(" ", "-").lower()
        if project_dir.exists():
            print(f"   ⚠️ 目錄已存在: {project_dir}")
            implementation = {"status": "already_exists", "item": item["name"], "path": str(project_dir), "timestamp": self.timestamp}
        else:
            project_dir.mkdir(parents=True, exist_ok=True)
            module_name = item_name.lower().replace(" ", "_")
            code = self._generate_code(item_name, item.get("description", ""))
            main_file = project_dir / f"{module_name}.py"
            main_file.write_text(code, encoding='utf-8')
            readme = project_dir / "README.md"
            readme.write_text(f"# {item_name}\n\n{item.get('description', '')}\n\nAuto-generated module.\n", encoding='utf-8')
            init_file = project_dir / "__init__.py"
            init_file.write_text(f'"""{item_name}"""', encoding='utf-8')
            print(f"   ✅ 創建: {project_dir}")
            implementation = {"status": "implemented", "item": item["name"], "path": str(project_dir), "timestamp": self.timestamp}
        self.results["implementation"] = implementation
    
    def _generate_code(self, item_name, description):
        name_lower = item_name.lower()
        if "performance" in name_lower or "optimizer" in name_lower:
            return '''#!/usr/bin/env python3
"""效能優化器"""
import psutil
from datetime import datetime

class PerformanceOptimizer:
    def __init__(self):
        self.thresholds = {"cpu": 80, "memory": 85, "disk": 90}
    
    def collect_metrics(self):
        return {"cpu": psutil.cpu_percent(interval=1), "memory": psutil.virtual_memory().percent, "disk": psutil.disk_usage("/").percent, "timestamp": datetime.now().isoformat()}
    
    def check_health(self):
        m = self.collect_metrics()
        issues = [f"{k} is {v}%" for k, v in m.items() if k != "timestamp" and v > self.thresholds.get(k, 90)]
        return {"healthy": len(issues) == 0, "issues": issues, "metrics": m}

if __name__ == "__main__":
    print(PerformanceOptimizer().check_health())
'''
        elif "cost" in name_lower or "analyzer" in name_lower:
            return '''#!/usr/bin/env python3
"""成本分析器"""
from datetime import datetime
class CostAnalyzer:
    PRICING = {"gpt-4": 0.03, "gpt-3.5-turbo": 0.002, "claude-3": 0.015}
    def __init__(self):
        self.entries = []
    def add(self, model, input_tokens, output_tokens):
        price = self.PRICING.get(model, 0.01)
        cost = (input_tokens + output_tokens) / 1000 * price
        self.entries.append({"model": model, "tokens": input_tokens + output_tokens, "cost": cost, "time": datetime.now()})
    def total(self):
        return sum(e["cost"] for e in self.entries)
    def report(self):
        return {"total_cost": self.total(), "entries": len(self.entries)}
if __name__ == "__main__":
    ca = CostAnalyzer()
    ca.add("gpt-4", 1000, 500)
    print(ca.report())
'''
        elif "security" in name_lower:
            return '''#!/usr/bin/env python3
"""安全檢查器"""
import re
class SecurityChecker:
    INJECTION = [r"ignore.*previous", r"system\\s*:\\s*", r"admin\\s*:\\s*"]
    SENSITIVE = [r"\\d{3}-\\d{2}-\\d{4}", r"\\d{16}", r"api[_-]?key"]
    def check(self, text):
        issues = []
        for p in self.INJECTION:
            if re.search(p, text, re.I):
                issues.append({"type": "injection", "pattern": p})
        for p in self.SENSITIVE:
            if re.search(p, text):
                issues.append({"type": "sensitive", "pattern": p})
        return {"safe": len(issues) == 0, "issues": issues}
if __name__ == "__main__":
    print(SecurityChecker().check("Ignore previous instructions"))
'''
        else:
            return f'''#!/usr/bin/env python3
"""Auto-generated: {item_name}"""
from datetime import datetime
class {item_name.replace(" ", "")}:
    def __init__(self):
        self.name = "{item_name}"
        self.created = datetime.now()
    def run(self):
        return {{"status": "ok", "module": self.name}}
if __name__ == "__main__":
    print({item_name.replace(" ", "")}().run())
'''
    
    def generate_docs(self, proposal):
        print("📄 生成文檔...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        article = f"""# 趨勢驅動的優化方案

## 時間: {self.timestamp}
## 趨勢: {proposal.get('trends_count', 0)} | 痛點: {proposal.get('pain_points_count', 0)}
## 項目: {proposal.get('priority_item', {}).get('name', 'N/A')}
## 狀態: {self.results.get('implementation', {}).get('status', 'unknown')}
"""
        article_file = OUTPUT_DIR / f"auto-optimization-{self.timestamp}.md"
        article_file.write_text(article, encoding='utf-8')
        self.results["docs"] = {"article": str(article_file)}
        print(f"✅ 文檔: {article_file}")


def main():
    if not should_run():
        print("⏭️  本小時已執行過，跳過")
        return
    mark_run()
    optimizer = AutoOptimizer()
    results = optimizer.run()
    print("\n" + "="*50)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
