# Integration Guide — Connect to Your Existing Toolchain

**No new tools. No new channels. Add to what you already have.**

---

## 1. GitHub Actions — Add Quality Gate as a PR Check

Add this job to any existing `.github/workflows/*.yml`. Runs before merge, blocks on failure.

### Minimal Version (5 lines of YAML)

```yaml
jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -q quality-gate && python -m quality_gate run --target ./src --phase 2
```

### Full Version with Fail Threshold

```yaml
jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Quality Gate
        run: python -m quality_gate run --target ./src --phase 2 --fail-threshold 0.8
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Upload Report
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: quality-gate-report
          path: quality_gate_report.json
```

**Where to add it:**
- In the same file as your existing CI workflow (don't create a new file)
- As a `jobs:` entry alongside your existing `build`, `test`, `lint` jobs
- The `needs:` dependency is optional — if you want it to run only after tests pass, add `needs: [test]`

---

## 2. Slack — Pipe Results to an Existing Webhook

Uses your existing Slack webhook. No new channel, no new app.

### Bash Script (existing CI → Slack)

```bash
#!/bin/bash
# Run quality gate, pipe result to Slack webhook
python -m quality_gate run --target ./src --phase 2 --json > qg_result.json

# Parse result and send to Slack
RESULT=$(cat qg_result.json | jq -r '.passed // false')
if [ "$RESULT" = "false" ]; then
  curl -s -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"❌ Quality Gate Failed on PR: $(git rev-parse --abbrev-ref HEAD)\"}" \
    "$SLACK_WEBHOOK_URL"
fi
```

### GitHub Actions with Slack (6 lines)

```yaml
- name: Notify Slack on Failure
  if: failure()
  run: |
    curl -s -X POST -H 'Content-type: application/json' \
      --data "{\"text\":\"❌ QG failed: ${{ github.ref }} by ${{ github.actor }}\"}" \
      "${{ secrets.SLACK_WEBHOOK_URL }}"
```

**Setup:**
1. Get your existing webhook URL (any channel — doesn't need to be new)
2. Set it as a secret in GitHub: `Settings → Secrets → Actions → New secret`
3. Reference it as `${{ secrets.SLACK_WEBHOOK_URL }}` in your workflow

---

## 3. Jira — Use Existing Tickets for Tracking

Don't create a new issue type or project. Link quality gate failures to existing Jira tickets.

### Link Failure to Existing Ticket (2 fields)

```bash
python -m quality_gate run --target ./src --phase 2 \
  --jira-link "https://your-org.atlassian.net/browse/PROJ-123"
```

This adds the quality gate result as a comment on the existing ticket. No new system.

### Jira Webhook Payload (for automation server)

```json
{
  "webhookEvent": "comment_created",
  "issue": {
    "key": "PROJ-123"
  },
  "comment": {
    "body": "Quality Gate Result: FAILED\nFiles checked: 12\nViolations: 2\nSpec: SRS.md"
  }
}
```

**What to track (existing ticket fields):**
- Add results as a **comment** on the ticket you're already working
- Use the ticket's **labels** to filter quality gate results (e.g., add label `qg-failed`)
- Link the PR to the existing ticket — no new Jira project needed

**Don't create:**
- Don't create new "Quality Gate" tickets
- Don't create new "AI Review" issue types
- Don't set up separate QA tracking in Jira

**Do this instead:**
- Reuse existing sprint/feature tickets
- Add quality gate results as comments
- Use existing labels for filtering

---

## Integration Priority

| If you already have... | Add this first... |
|------------------------|-------------------|
| GitHub Actions | QG as PR check (Job 1) |
| Slack webhook | Slack notification (Script 1) |
| Jira tickets | Link to existing ticket (Step 3) |

All three are additive. Start with whichever tool you're already using daily.

---

## Files in This Kit

- [Value Proposition](./VALUE_PROPOSITION.md) — Why this matters to engineers
- [Quick Wins](./QUICK_WINS.md) — 3 things to try today
- [Case Study Template](../CASE_STUDIES/template.json) — Measure your own results
