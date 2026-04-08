# 5-Minute Quick Start Guide

This guide gets you from zero to running your first Phase-gate workflow in under 5 minutes.

---

## Step 1: Initialize Your Project (30 seconds)

```bash
cd your-project-directory
python /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/cli.py init my-first-project
```

Expected output:
```
✅ Project 'my-first-project' initialized
   Created: .methodology/
   Created: .methodology/tasks/
   Created: .methodology/sprints/
```

---

## Step 2: Start Quality Watch (15 seconds)

```bash
python /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/quality_watch.py start --project .
```

Keep it running in background. Quality watch monitors your artifacts in real-time.

---

## Step 3: Run the Onboarding Wizard (2-3 minutes)

```bash
python /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/cli.py onboarding --project . --phase 1
```

The wizard will:
1. ✅ Check project initialization
2. ✅ Verify quality gate setup
3. ✅ Create SRS.md (if not exists)
4. ✅ Set up constitution

If any step fails, the wizard shows a hint on how to fix it.

---

## Step 4: Resume if Interrupted (instant)

```bash
python /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/cli.py onboarding --project . --phase 1 --resume
```

Resume picks up from where you left off. Progress is saved to `.methodology/onboarding_progress.json`.

---

## Common Errors & Fixes

### Error: `state.json not found`
```bash
python cli.py init "project-name"
```
You must initialize first.

### Error: `SRS.md not found`
```bash
cp templates/SRS.md ./SRS.md
# Then edit it with your requirements
```

### Error: `quality_watch not running`
```bash
python quality_watch.py start --project .
```

### Error: `constitution/CONSTITUTION.md not found`
```bash
mkdir -p constitution
cp templates/CONSTITUTION.md constitution/
```

### Error: `Phase already completed`
The progress file has locked the phase. Reset with:
```bash
rm .methodology/onboarding_progress.json
python cli.py onboarding --project . --phase 1
```

---

## What to Do Next

After Phase 1 is complete:

| Next Step | Command |
|-----------|---------|
| Check project status | `python cli.py status` |
| Start Phase 2 | `python cli.py onboarding --project . --phase 2` |
| View board | `python cli.py board` |
| Check quality gate | `python cli.py quality-gate status` |

---

## Project Structure After Setup

```
your-project/
├── .methodology/
│   ├── state.json              # Project state
│   ├── onboarding_progress.json  # Wizard progress
│   ├── quality_gate/           # Quality gate config
│   └── tasks/                 # Task backlog
├── constitution/
│   └── CONSTITUTION.md        # Project constitution
├── SRS.md                     # Requirements spec
├── SPEC_TRACKING.md           # Specification tracking
└── TRACEABILITY_MATRIX.md     # Requirements traceability
```

---

## Keyboard Shortcuts (CLI)

| Shortcut | Action |
|----------|--------|
| `--project .` | Use current directory |
| `--phase N` | Target specific phase |
| `--resume` | Continue from last checkpoint |
| `--help` | Show all options |

---

## Getting Help

```bash
# General help
python cli.py --help

# Specific command help
python cli.py onboarding --help
python cli.py quality-gate --help
python cli.py constitution --help
```
