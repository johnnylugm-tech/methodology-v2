#!/usr/bin/env python3
"""
領域知識動態載入模組
功能：根據專案類型（TTS/Web/API/其他）動態載入領域知識檢查清單
"""

import os
# import yaml  # 移除 yaml 依賴，改用 JSON
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class DomainLoader:
    """領域知識載入器"""
    
    def __init__(self, templates_path: Optional[str] = None):
        """
        初始化
        
        Args:
            templates_path: 領域模板目錄路徑
        """
        if templates_path:
            self.templates_path = Path(templates_path)
        else:
            # 預設路徑
            self.templates_path = Path(__file__).parent.parent / "domain_templates"
        
        # 確保目錄存在
        self.templates_path.mkdir(parents=True, exist_ok=True)
        
        # 內建領域模板
        self.builtin_templates = {
            "tts": {
                "name": "文字轉語音 (TTS)",
                "checks": [
                    {"id": "D-TTS-01", "name": "標點保留", "description": "標點=停頓信號，刪除會破壞韻律", "verify": "輸出長度 ≤ 輸入長度"},
                    {"id": "D-TTS-02", "name": "合併不多於原文", "description": "合併時不插入額外字符", "verify": "合併後字符數 ≤ 原始字符數"},
                    {"id": "D-TTS-03", "name": "格式一致性", "description": "單一檔案與多檔案格式相同", "verify": "檢查 bitrate/codec 一致"},
                    {"id": "D-TTS-04", "name": "Lazy Check", "description": "外部依賴不在 __init__ 直接呼叫", "verify": "初始化不崩潰"}
                ]
            },
            "web": {
                "name": "網頁開發 (Web)",
                "checks": [
                    {"id": "D-WEB-01", "name": "響應式設計", "description": "支援不同螢幕尺寸", "verify": "媒體查詢測試"},
                    {"id": "D-WEB-02", "name": "安全性", "description": "XSS/CSRF 防護", "verify": "輸入驗證"},
                    {"id": "D-WEB-03", "name": "效能", "description": "載入時間優化", "verify": "資源壓縮"},
                    {"id": "D-WEB-04", "name": "無障礙", "description": "ARIA 標籤支援", "verify": "a11y 測試"}
                ]
            },
            "api": {
                "name": "API 開發 (API)",
                "checks": [
                    {"id": "D-API-01", "name": "RESTful 規範", "description": "遵循 REST 設計原則", "verify": "HTTP 方法正確"},
                    {"id": "D-API-02", "name": "錯誤處理", "description": "統一的錯誤格式", "verify": "Error schema"},
                    {"id": "D-API-03", "name": "認證授權", "description": "JWT/OAuth 正確實作", "verify": "Token 驗證"},
                    {"id": "D-API-04", "name": "速率限制", "description": "防止 API 濫用", "verify": "Rate limit 測試"}
                ]
            },
            "generic": {
                "name": "通用領域",
                "checks": [
                    {"id": "D-GEN-01", "name": "輸出≤輸入", "description": "字串操作不插入額外字符", "verify": "字符數比對"},
                    {"id": "D-GEN-02", "name": "分支一致", "description": "邊界情況與一般情况一致", "verify": "邊界測試"},
                    {"id": "D-GEN-03", "name": "Lazy Init", "description": "外部依賴在實際需要時才檢查", "verify": "延遲初始化"},
                    {"id": "D-GEN-04", "name": "錯誤處理", "description": "異常情況正確處理", "verify": "Exception 測試"}
                ]
            }
        }
    
    def get_template(self, domain: str) -> Dict[str, Any]:
        """
        取得領域模板
        
        Args:
            domain: 領域名稱 (tts/web/api/generic)
            
        Returns:
            領域模板內容
        """
        # 優先使用內建模板
        if domain in self.builtin_templates:
            template = self.builtin_templates[domain].copy()
            template["source"] = "builtin"
            return template
        
        # 嘗試從檔案載入
        custom_path = self.templates_path / f"{domain}.yaml"
        if custom_path.exists():
            with open(custom_path, "r", encoding="utf-8") as f:
                template = json.load(f)
                template["source"] = "custom"
                return template
        
        # 預設返回 generic
        generic = self.builtin_templates["generic"].copy()
        generic["source"] = "fallback"
        return generic
    
    def get_checklist(self, domain: str) -> List[Dict[str, Any]]:
        """
        取得領域檢查清單
        
        Args:
            domain: 領域名稱
            
        Returns:
            檢查項目列表
        """
        template = self.get_template(domain)
        return template.get("checks", [])
    
    def generate_prompt_context(self, domain: str) -> str:
        """
        生成 Prompt 使用的領域知識上下文
        
        Args:
            domain: 領域名稱
            
        Returns:
            Markdown 格式的領域知識
        """
        template = self.get_template(domain)
        checks = template.get("checks", [])
        
        lines = [
            f"## 領域知識檢查清單（{template['name']}）",
            ""
        ]
        
        for check in checks:
            lines.append(f"### {check['id']}: {check['name']}")
            lines.append(f"- **說明**: {check['description']}")
            lines.append(f"- **驗證方法**: `{check['verify']}`")
            lines.append(f"- [ ] 已檢查")
            lines.append("")
        
        return "\n".join(lines)
    
    def list_domains(self) -> List[str]:
        """列出所有可用領域"""
        domains = list(self.builtin_templates.keys())
        
        # 加入自訂領域
        if self.templates_path.exists():
            for f in self.templates_path.glob("*.yaml"):
                domain_name = f.stem
                if domain_name not in domains:
                    domains.append(domain_name)
        
        return domains
    
    def create_custom_template(self, domain: str, name: str, checks: List[Dict[str, Any]]) -> bool:
        """
        建立自訂領域模板
        
        Args:
            domain: 領域 ID
            name: 領域名稱
            checks: 檢查項目列表
            
        Returns:
            是否成功
        """
        template = {
            "domain": domain,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "checks": checks
        }
        
        custom_path = self.templates_path / f"{domain}.yaml"
        
        try:
            with open(custom_path, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 建立自訂模板失敗: {e}")
            return False


# 全域實例
domain_loader = DomainLoader()


# 便捷函數
def load_domain(domain: str) -> Dict[str, Any]:
    """快速載入領域模板"""
    return domain_loader.get_template(domain)


def get_checklist(domain: str) -> List[Dict[str, Any]]:
    """快速取得檢查清單"""
    return domain_loader.get_checklist(domain)


def generate_context(domain: str) -> str:
    """快速生成 Prompt 上下文"""
    return domain_loader.generate_prompt_context(domain)


# 測試
if __name__ == "__main__":
    print("=== DomainLoader 測試 ===")
    
    # 列出所有領域
    domains = domain_loader.list_domains()
    print(f"\n可用領域: {domains}")
    
    # 測試 TTS 領域
    print("\n--- TTS 領域 ---")
    tts = load_domain("tts")
    print(f"名稱: {tts['name']}")
    print(f"檢查項目數: {len(tts['checks'])}")
    
    # 測試生成 Prompt 上下文
    print("\n--- Prompt 上下文 ---")
    context = generate_context("tts")
    print(context[:500] + "...")
    
    print("\n✅ DomainLoader 測試完成")