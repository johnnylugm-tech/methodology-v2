#!/usr/bin/env python3
"""Local Deployment Suite for methodology-v2"""

import os
import subprocess
import json
from dataclasses import dataclass

DOCKER_COMPOSE = '''version: '3.8'
services:
  api:
    image: methodology-v2-api
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3
    volumes:
      - ./data:/data
    depends_on:
      - ollama
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
volumes:
  ollama-data:
'''

class LocalDeployer:
    def __init__(self, project_dir="./methodology-v2-local"):
        self.project_dir = project_dir
    
    def init(self):
        os.makedirs(self.project_dir, exist_ok=True)
        with open(f"{self.project_dir}/docker-compose.yml", "w") as f:
            f.write(DOCKER_COMPOSE)
        print(f"Initialized at {self.project_dir}")
    
    def start(self):
        subprocess.run(["docker", "compose", "-f", f"{self.project_dir}/docker-compose.yml", "up", "-d"])
        print("Started!")
    
    def stop(self):
        subprocess.run(["docker", "compose", "-f", f"{self.project_dir}/docker-compose.yml", "down"])
        print("Stopped!")
    
    def status(self):
        result = subprocess.run(
            ["docker", "compose", "-f", f"{self.project_dir}/docker-compose.yml", "ps"],
            capture_output=True, text=True
        )
        print(result.stdout)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["init", "start", "stop", "status"])
    args = parser.parse_args()
    
    deployer = LocalDeployer()
    
    if args.cmd == "init":
        deployer.init()
    elif args.cmd == "start":
        deployer.start()
    elif args.cmd == "stop":
        deployer.stop()
    elif args.cmd == "status":
        deployer.status()
