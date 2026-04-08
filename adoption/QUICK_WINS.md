# Quick Wins — 3 Things You Can Do Today

**Don't try to adopt everything at once. Pick one. Do it today.**

---

## Quick Win #1: Run a Quality Gate Check on Your Last PR

**Time: 5 minutes. No setup required.**

Runs a spec-alignment check on any codebase directory. No git hooks, no CI integration — just run it and see what happens.

```bash
# From the methodology-v2 root directory
cd /path/to/methodology-v2
python cli.py quality-gate check --target /path/to/your/project --phase 2
```

**What you'll get:**
- A report showing which outputs match the spec and which don't
- File-by-file breakdown of requirement alignment
- If everything passes → green output
- If something fails → specific files and what requirements they violate

**Why this matters:**
- You see immediate value without changing anything
- You learn what the quality gate actually checks
- You can show it to your team without any commitment

---

## Quick Win #2: Run Quality Gate from Your Project Directory

**Time: 5 minutes. Point to your project from anywhere.**

If you want to run quality gate from your actual project directory (not the methodology-v2 repo):

```bash
# From your project root
cd /path/to/your/project

# Run quality gate using absolute path to methodology-v2
python /path/to/methodology-v2/cli.py quality-gate check --target ./src --phase 2
```

**What happens:**
- Quality gate reads your source files and checks them against your spec
- Results show alignment score and specific violations
- No files are modified

**Why this matters:**
- You can try it on any existing project
- No installation required — just points to the CLI
- See value in under 5 minutes

---

## Quick Win #3: Add a Quality Gate Step to an Existing GitHub Actions Workflow

**Time: 15 minutes. Adds a single job to your existing workflow file.**

Take any existing `.github/workflows/*.yml` and add one job:

```yaml
# In your existing workflow file, add this job
jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Quality Gate
        run: |
          python cli.py quality-gate check --target ./src --phase 2
        working-directory: /path/to/methodology-v2  # adjust to where methodology-v2 is checked out
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**What happens:**
- Every PR runs the quality gate as a status check
- Block merge if quality gate fails
- No new systems to monitor — just a pass/fail on your existing PR

**Why this matters:**
- The gate runs automatically on every PR
- You catch issues before they reach main branch
- Your team sees it work without changing their workflow

---

## "Don't Do Everything. Do One Thing."

| If you want... | Start with... |
|---------------|---------------|
| Quick feedback, no commitment | Quick Win #1 |
| Try on an existing project | Quick Win #2 |
| Automated blocking on PRs | Quick Win #3 |

All three are independent. Pick whichever matches your current pain point.

---

## Next Steps

Once you've tried one and seen it work:

👉 [Full Integration Guide](./INTEGRATION_GUIDE.md)
