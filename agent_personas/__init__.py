"""
Agent Personas - 角色人格定義庫

提供預設的 Agent 人格定義，包括：
- Architect: 架構師
- Developer: 開發者
- Reviewer: 審查者
- QAEngineer: QA 工程師
- ProductManager: 產品經理
- DevOps: DevOps 工程師

使用方式：

    from agent_personas import Developer, Reviewer

    dev = Developer()
    prompt = dev.generate_prompt(task="寫登入功能")
"""

from .persona import Persona, generate_persona_prompt

__all__ = [
    'Persona',
    'generate_persona_prompt',
]
