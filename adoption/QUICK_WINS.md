# Quick Wins — 3 Things You Can Do Today

**Don't try to adopt everything at once. Pick one. Do it today.**

---

## Quick Win #1: Run a Quality Gate Check on Your Last PR

**Time: 5 minutes. No setup required.**

This runs a spec-alignment check on any codebase directory. No git hooks, no CI integration — just run it and see what happens.

```bash
# From your project root
python -m quality_gate run --target ./src --phase 2
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

## Quick Win #2: Add a Slack Notification to Your Existing CI

**Time: 10 minutes. Uses existing Slack webhook — no new channel needed.**

If you already have a Slack webhook URL (any channel), you can pipe quality gate results there.

```bash
# Set your webhook once
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Run with notification
python -m quality_gate run --target ./src --notify-slack
```

**What happens:**
- After each quality gate run, a summary posts to your configured webhook
- No new channel created — goes to wherever you point it
- You see failures without checking CI logs

**Why this matters:**
- You get visibility without changing your team's notification habits
- Failures surface where engineers already look

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
          pip install -q quality-gate
          python -m quality_gate run --target ./src --phase 2
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
| Visibility in your existing tools | Quick Win #2 |
| Automated blocking on PRs | Quick Win #3 |

All three are independent. Pick whichever matches your current pain point.

---

## Next Steps

Once you've tried one and seen it work:

👉 [Full Integration Guide](./INTEGRATION_GUIDE.md)
