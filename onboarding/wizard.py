#!/usr/bin/env python3
"""
Interactive Onboarding Wizard for Methodology v2

Guides engineers through their first Phase-gate workflow in ~30 minutes.
Each checkpoint calls the actual CLI tools to verify real state.

Usage:
    python wizard.py --project . --phase 1
    python wizard.py --project . --phase 1 --resume
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

import click

# Resolve the methodology-v2 root (parent of this file's directory)
ONBOARDING_DIR = Path(__file__).parent
METHODOLOGY_ROOT = ONBOARDING_DIR.parent
CLI_PATH = METHODOLOGY_ROOT / "cli.py"
CHECKPOINTS_DIR = ONBOARDING_DIR / "checkpoints"
PROGRESS_FILE = ".methodology/onboarding_progress.json"


# ─────────────────────────────────────────────────────────────────────────────
# Progress persistence
# ─────────────────────────────────────────────────────────────────────────────

def load_progress(project_path: Path) -> dict:
    """Load progress from .methodology/onboarding_progress.json"""
    progress_file = project_path / PROGRESS_FILE
    if progress_file.exists():
        with open(progress_file) as f:
            return json.load(f)
    return {"phases": {}, "last_updated": None}


def save_progress(project_path: Path, progress: dict) -> None:
    """Save progress to .methodology/onboarding_progress.json"""
    progress["last_updated"] = str(Path(__file__).stat().st_mtime)
    progress_file = project_path / PROGRESS_FILE
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# YAML checkpoint loading
# ─────────────────────────────────────────────────────────────────────────────

def load_phase_checkpoints(phase: int) -> dict:
    """Load checkpoint definitions for a phase"""
    import yaml

    checkpoint_file = CHECKPOINTS_DIR / f"phase{phase}.yaml"
    if not checkpoint_file.exists():
        click.echo(f"❌ No checkpoint definition found for phase {phase}: {checkpoint_file}")
        sys.exit(1)

    with open(checkpoint_file) as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────────────────────────────────────
# CLI command execution
# ─────────────────────────────────────────────────────────────────────────────

def run_cli_command(command: str, args: list, project_path: Path) -> tuple[bool, str]:
    """
    Run a CLI command and return (success, output).
    Uses the actual cli.py from methodology-v2.
    """
    cmd = [sys.executable, str(CLI_PATH), command] + args

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=60,
        )
        success = result.returncode == 0
        output = result.stdout.strip() or result.stderr.strip()
        return success, output
    except subprocess.TimeoutExpired:
        return False, "⏱️  Command timed out after 60 seconds"
    except FileNotFoundError:
        return False, f"❌ CLI not found at {CLI_PATH}"
    except Exception as e:
        return False, f"❌ Error running command: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Artifact verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_artifacts(artifacts: list, project_path: Path) -> list:
    """Verify that required artifacts exist. Returns list of missing artifacts."""
    missing = []
    for artifact in artifacts:
        artifact_path = project_path / artifact["path"]
        if not artifact_path.exists():
            missing.append(artifact["path"])
    return missing


# ─────────────────────────────────────────────────────────────────────────────
# Checkpoint execution
# ─────────────────────────────────────────────────────────────────────────────

def run_checkpoint(
    checkpoint: dict,
    project_path: Path,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """
    Execute a single checkpoint.

    Strategy:
    1. If command is specified, run it via CLI
    2. If no command, just verify artifacts exist
    3. Also verify all listed artifacts

    Returns (passed, message)
    """
    cp_id = checkpoint["id"]
    cp_title = checkpoint["title"]
    command = checkpoint.get("command")
    args = checkpoint.get("args", [])
    artifacts = checkpoint.get("artifacts", [])

    if dry_run:
        return True, f"[dry-run] Would check: {cp_title}"

    # Run CLI command if specified
    if command:
        passed, output = run_cli_command(command, args, project_path)
        if not passed:
            hint = checkpoint.get("hint", "No hint available.")
            return False, f"{output}\n\n💡 Hint:\n{hint}"

    # Verify artifacts
    missing = verify_artifacts(artifacts, project_path)
    if missing:
        hint = checkpoint.get("hint", "No hint available.")
        return False, f"Missing artifacts: {', '.join(missing)}\n\n💡 Hint:\n{hint}"

    return True, f"✅ {cp_title} passed"


# ─────────────────────────────────────────────────────────────────────────────
# Phase execution
# ─────────────────────────────────────────────────────────────────────────────

def run_phase(phase: int, project_path: Path, resume: bool = False) -> int:
    """
    Run all checkpoints for a given phase.

    Returns 0 on success, 1 on any failure.
    """
    phase_data = load_phase_checkpoints(phase)
    phase_name = phase_data.get("name", f"Phase {phase}")
    checkpoints = phase_data.get("checkpoints", [])

    click.echo(f"\n{'='*60}")
    click.echo(f"  Phase {phase}: {phase_name}")
    click.echo(f"{'='*60}")

    progress = load_progress(project_path)

    # Determine starting checkpoint (resume support)
    start_index = 0
    if resume:
        phase_progress = progress.get("phases", {}).get(str(phase), {})
        last_completed = phase_progress.get("last_completed")
        if last_completed:
            for i, cp in enumerate(checkpoints):
                if cp["id"] == last_completed:
                    start_index = i + 1
                    click.echo(f"🔄 Resuming from checkpoint {start_index}/{len(checkpoints)}")
                    break

    all_passed = True
    completed_ids = []

    for i, checkpoint in enumerate(checkpoints):
        if i < start_index:
            completed_ids.append(checkpoint["id"])
            click.echo(f"  ⏭️  [{i+1}/{len(checkpoints)}] {checkpoint['title']} (skipped — already done)")
            continue

        cp_id = checkpoint["id"]
        cp_title = checkpoint["title"]

        click.echo(f"\n  [{i+1}/{len(checkpoints)}] {cp_title}...")
        passed, message = run_checkpoint(checkpoint, project_path)

        if passed:
            click.echo(f"  ✅ {message}")
            completed_ids.append(cp_id)
            # Update progress
            if "phases" not in progress:
                progress["phases"] = {}
            progress["phases"][str(phase)] = {
                "status": "in_progress" if i < len(checkpoints) - 1 else "completed",
                "last_completed": cp_id,
                "completed_checkpoints": completed_ids.copy(),
            }
            save_progress(project_path, progress)
        else:
            click.echo(f"  ❌ {message}")
            all_passed = False
            break

    # Summary
    click.echo(f"\n{'='*60}")
    if all_passed:
        click.echo(f"  ✅ Phase {phase} COMPLETED")
        click.echo(f"{'='*60}")
        click.echo(f"\n🎉 Great job! Phase {phase} is done.")
        click.echo(f"   Next: python cli.py onboarding --project . --phase {phase + 1}")
    else:
        click.echo(f"  ❌ Phase {phase} INCOMPLETE")
        click.echo(f"{'='*60}")
        click.echo(f"\n⚠️  Fix the failed checkpoint and run again with --resume")
        click.echo(f"   To resume: python cli.py onboarding --project . --phase {phase} --resume")

    return 0 if all_passed else 1


# ─────────────────────────────────────────────────────────────────────────────
# Click CLI
# ─────────────────────────────────────────────────────────────────────────────

@click.command()
@click.option(
    "--project",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
    help="Project directory (default: current directory)",
)
@click.option(
    "--phase",
    type=click.IntRange(1, 3),
    default=1,
    help="Phase to onboard (1, 2, or 3)",
)
@click.option(
    "--resume",
    is_flag=True,
    default=False,
    help="Resume from last interrupted checkpoint",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be checked without running",
)
@click.option(
    "--list-phases",
    is_flag=True,
    default=False,
    help="List available phases and exit",
)
def main(
    project: Path,
    phase: int,
    resume: bool,
    dry_run: bool,
    list_phases: bool,
):
    """
    Interactive Onboarding Wizard for Methodology v2.

    Guides engineers through their first Phase-gate workflow.
    Each checkpoint calls the actual CLI tools to verify real state.

    Examples:

        # Start Phase 1 onboarding
        python wizard.py --project . --phase 1

        # Resume from interruption
        python wizard.py --project . --phase 1 --resume

        # See available phases
        python wizard.py --list-phases
    """
    if list_phases:
        for p in [1, 2, 3]:
            data = load_phase_checkpoints(p)
            checkpoints = data.get("checkpoints", [])
            click.echo(f"\nPhase {p}: {data.get('name', 'Unknown')}")
            for cp in checkpoints:
                click.echo(f"  • {cp['title']}")
        return

    # Validate project path
    if not (project / ".methodology").exists() and not dry_run:
        click.echo(
            f"⚠️  Warning: .methodology/ not found in {project}.\n"
            f"   Run 'python cli.py init' first, or use --dry-run to preview."
        )

    # Show context
    click.echo(f"\n🚀 Onboarding Wizard — Phase {phase}")
    click.echo(f"   Project: {project.absolute()}")

    if resume:
        click.echo(f"   Mode: RESUME (picking up from last checkpoint)")

    sys.exit(run_phase(phase, project, resume=resume))


if __name__ == "__main__":
    main()
