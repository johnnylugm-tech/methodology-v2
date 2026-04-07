#!/usr/bin/env python3
"""
自動化腳本工具模組
"""

from .openclaw_api import OpenClawAPI, api, spawn, wait, history
from .async_wait import AsyncWaiter, waiter, wait_for_agent, wait_with_retry
from .qg_parser import QualityGateParser, parser, parse_qg_output
from .phase_checker import PhaseCompletionChecker, checker, check_phase1, can_proceed
from .domain_loader import DomainLoader, domain_loader, load_domain, get_checklist, generate_context

__all__ = [
    # OpenClaw API
    "OpenClawAPI",
    "api",
    "spawn",
    "wait",
    "history",
    # Async Wait
    "AsyncWaiter",
    "waiter",
    "wait_for_agent",
    "wait_with_retry",
    # QG Parser
    "QualityGateParser",
    "parser",
    "parse_qg_output",
    # Phase Checker
    "PhaseCompletionChecker",
    "checker",
    "check_phase1",
    "can_proceed",
    # Domain Loader
    "DomainLoader",
    "domain_loader",
    "load_domain",
    "get_checklist",
    "generate_context",
]
