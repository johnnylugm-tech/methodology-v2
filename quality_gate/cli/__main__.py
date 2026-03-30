#!/usr/bin/env python3
"""
Quality CLI __main__ module
===========================
允許使用 python -m quality_gate.cli quality 執行
"""

from .quality import main

if __name__ == "__main__":
    main()