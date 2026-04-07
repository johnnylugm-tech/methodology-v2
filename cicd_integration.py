#!/usr/bin/env python3
"""
CI/CD Integration - 自動化部署框架

支援 GitHub Actions、Jenkins、GitLab CI
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PipelineStep:
    """管線步驟"""
    name: str
    command: str
    condition: str = None  # 執行條件
    timeout: int = 300  # 秒
    retry: int = 0


@dataclass
class Pipeline:
    """部署管線"""
    name: str
    stages: List[str] = field(default_factory=list)
    steps: Dict[str, List[PipelineStep]] = field(default_factory=dict)


class CICDIntegration:
    """CI/CD 整合管理器"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.pipelines: Dict[str, Pipeline] = {}
    
    # ==================== GitHub Actions ====================
    
    def generate_github_actions(self, 
                               workflow_name: str = "CI",
                               trigger: str = "push",
                               python_version: str = "3.11") -> str:
        """
        生成 GitHub Actions 配置
        
        Args:
            workflow_name: 工作流名稱
            trigger: 觸發條件 (push, pull_request, etc)
            python_version: Python 版本
            
        Returns:
            YAML 配置內容
        """
        yaml = f"""name: {workflow_name}

on:
  {trigger}:
    branches: [main, develop]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '{python_version}'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --junitxml=report.xml
    
    - name: Run linter
      run: |
        pylint src/ --output-format=text
    
    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        files: ./coverage.xml
    
    - name: Security scan
      run: |
        safety check || true
        bandit -r src/ -f json -o security-report.json || true

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
      run: |
        ./scripts/deploy.sh
"""
        return yaml
    
    def create_github_actions_workflow(self, 
                                     workflow_name: str = "CI",
                                     path: str = None) -> str:
        """建立 GitHub Actions 工作流"""
        path = path or f"{self.project_path}/.github/workflows/{workflow_name.lower().replace(' ', '-')}.yml"
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        content = self.generate_github_actions(workflow_name)
        
        with open(path, 'w') as f:
            f.write(content)
        
        return path
    
    # ==================== Jenkins ====================
    
    def generate_jenkinsfile(self, 
                           pipeline_name: str = "methodology-pipeline",
                           stages: List[str] = None) -> str:
        """
        生成 Jenkinsfile
        
        Args:
            pipeline_name: 管線名稱
            stages: 階段列表
            
        Returns:
            Jenkinsfile 內容
        """
        if stages is None:
            stages = ["build", "test", "deploy"]
        
        stage_blocks = []
        for stage in stages:
            stage_blocks.append(f"""        stage('{stage.title()}') {{
            steps {{
                sh '''
                    echo "Running {stage}..."
                    // Add stage-specific commands
                '''
            }}
        }}""")
        
        jenkinsfile = f"""pipeline {{
    agent any
    
    environment {{
        PROJECT_NAME = '{pipeline_name}'
        VERSION = '{datetime.now().strftime('%Y.%m.%d')}'
    }}
    
    stages {{
        {chr(10).join(stage_blocks)}
    }}
    
    post {{
        always {{
            junit '**/report.xml'
            publishHTML target {{
                reportDir: 'htmlcov'
                reportFiles: 'index.html'
                reportName: 'Coverage Report'
            }}
        }}
        success {{
            echo 'Pipeline completed successfully!'
        }}
        failure {{
            echo 'Pipeline failed!'
        }}
    }}
}}"""
        return jenkinsfile
    
    def create_jenkinsfile(self, path: str = None) -> str:
        """建立 Jenkinsfile"""
        path = path or f"{self.project_path}/Jenkinsfile"
        
        content = self.generate_jenkinsfile()
        
        with open(path, 'w') as f:
            f.write(content)
        
        return path
    
    # ==================== GitLab CI ====================
    
    def generate_gitlab_ci(self,
                          image: str = "python:3.11",
                          stages: List[str] = None) -> str:
        """
        生成 GitLab CI 配置
        
        Args:
            image: Docker image
            stages: 階段列表
            
        Returns:
            .gitlab-ci.yml 內容
        """
        if stages is None:
            stages = ["build", "test", "deploy"]
        
        stage_block = "\n".join([f"  - {s}" for s in stages])
        
        gitlab_ci = f"""stages:
{stage_block}

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/

before_script:
  - pip install -r requirements.txt

build:
  stage: build
  script:
    - echo "Building..."
    - python setup.py build
  artifacts:
    paths:
      - dist/
    expire_in: 1 day

test:
  stage: test
  script:
    - echo "Testing..."
    - pytest tests/ --junitxml=report.xml --cov=src
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

deploy:
  stage: deploy
  only:
    - main
  script:
    - echo "Deploying..."
    - ./scripts/deploy.sh
  environment:
    name: production
"""
        return gitlab_ci
    
    def create_gitlab_ci(self, path: str = None) -> str:
        """建立 GitLab CI 配置"""
        path = path or f"{self.project_path}/.gitlab-ci.yml"
        
        content = self.generate_gitlab_ci()
        
        with open(path, 'w') as f:
            f.write(content)
        
        return path
    
    # ==================== Docker Compose ====================
    
    def generate_docker_compose(self,
                             services: List[str] = None,
                             port: int = 8000) -> str:
        """
        生成 Docker Compose 配置
        
        Args:
            services: 服務列表
            port: 對外端口
            
        Returns:
            docker-compose.yml 內容
        """
        if services is None:
            services = ["api", "worker", "monitor"]
        
        service_blocks = []
        for svc in services:
            service_blocks.append(f"""  {svc}:
    build: ./services/{svc}
    ports:
      - "{port}:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/app
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache
    restart: unless-stopped""")
            port += 1
        
        compose = f"""version: '3.8'

services:
{chr(10).join(service_blocks)}

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password

  cache:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
"""
        return compose
    
    # ==================== 統一介面 ====================
    
    def setup_all(self, provider: str = "github"):
        """
        設定所有 CI/CD
        
        Args:
            provider: CI/CD 供應商 (github/jenkins/gitlab)
        """
        if provider == "github":
            self.create_github_actions_workflow()
            print("✅ GitHub Actions workflow created")
        
        elif provider == "jenkins":
            self.create_jenkinsfile()
            print("✅ Jenkinsfile created")
        
        elif provider == "gitlab":
            self.create_gitlab_ci()
            print("✅ GitLab CI created")
        
        # Docker Compose
        compose_path = f"{self.project_path}/docker-compose.yml"
        with open(compose_path, 'w') as f:
            f.write(self.generate_docker_compose())
        print("✅ docker-compose.yml created")
        
        return True


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cicd = CICDIntegration(project_path=tmpdir)
        
        print("=== GitHub Actions ===")
        print(cicd.generate_github_actions("Test Workflow")[:500])
        print()
        
        print("=== Jenkinsfile ===")
        print(cicd.generate_jenkinsfile()[:500])
        print()
        
        print("=== GitLab CI ===")
        print(cicd.generate_gitlab_ci()[:500])
        print()
        
        print("=== Setup All ===")
        cicd.setup_all("github")
