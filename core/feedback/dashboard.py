"""
ASCII / CLI Dashboard.

Prints a human-readable feedback loop dashboard to the terminal.
Uses `rich` if available for enhanced rendering, falls back to plain ASCII.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import TextIO

from .feedback import StandardFeedback, FeedbackStore, get_store
from .metrics import get_dashboard_metrics, _SEVERITY_EMOJI

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rprint

    _HAS_RICH = True
    _console = Console()
except ImportError:
    _HAS_RICH = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_delta(deadline_iso: str | None, now: datetime | None = None) -> str:
    """Return 'Nh overdue' or 'Nm at-risk' string for a deadline."""
    if not deadline_iso:
        return "no deadline"
    if now is None:
        now = datetime.now(timezone.utc)
    try:
        deadline = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
    except ValueError:
        return "invalid deadline"

    delta = deadline - now
    total_minutes = int(delta.total_seconds() / 60)
    hours = total_minutes // 60
    days = hours // 24
    remainder_hours = hours % 24

    if delta.total_seconds() < 0:
        # Overdue
        overdue_minutes = abs(total_minutes)
        overdue_hours = overdue_minutes // 60
        overdue_days = overdue_hours // 24
        rem_h = overdue_hours % 24
        if overdue_days > 0:
            return f"{overdue_days}d {rem_h}h overdue"
        return f"{overdue_hours}h overdue"
    else:
        # At risk
        if days > 0:
            return f"{days}d {remainder_hours}h remaining"
        if hours > 0:
            return f"{hours}h remaining"
        return f"{total_minutes}m remaining"


def _severity_emoji(sev: str) -> str:
    return _SEVERITY_EMOJI.get(sev, f"[{sev}]")


# ---------------------------------------------------------------------------
# Plain ASCII rendering
# ---------------------------------------------------------------------------

BOX_WIDTH = 70
DIVIDER = "═" * (BOX_WIDTH - 2)


def _print_ascii_dashboard(metrics, out: TextIO = sys.stdout) -> None:
    """Render dashboard using plain ASCII box-drawing characters."""
    print("╔" + DIVIDER + "╗", file=out)
    print("║" + f" FEEDBACK LOOP DASHBOARD — Last {metrics.total_feedback} items ".center(BOX_WIDTH - 2) + "║", file=out)
    print("╠" + DIVIDER + "╣", file=out)

    # Overview row
    overview = (
        f"TOTAL: {metrics.total_feedback}  │  PENDING: {metrics.pending}  │  "
        f"RESOLVED: {metrics.resolved}  │  CLOSED: {metrics.closed}"
    )
    print("║" + overview.center(BOX_WIDTH - 2) + "║", file=out)
    print("╠" + DIVIDER + "╣", file=out)

    # Rate row
    rate_str = (
        f"Resolution Rate: {metrics.resolution_rate * 100:.1f}%  │  "
        f"Avg Time: {metrics.avg_resolution_time_hours:.1f}h"
    )
    print("║" + rate_str.center(BOX_WIDTH - 2) + "║", file=out)
    print("╠" + DIVIDER + "╣", file=out)

    # Three-column breakdown
    # Build column strings
    def col(label: str, items: list[tuple[str, int]]) -> list[str]:
        lines = [label]
        for k, v in items:
            lines.append(f"  {k}: {v}")
        return lines

    sev_items = list(metrics.by_severity.items())
    src_items = list(metrics.by_source.items())
    sta_items = list(metrics.by_status.items())

    # Pad each column to same height
    max_rows = max(len(sev_items), len(src_items), len(sta_items), 1)
    for lst in [sev_items, src_items, sta_items]:
        while len(lst) < max_rows:
            lst.append(("", 0))

    header = "║  BY SEVERITY".ljust(23) + "║  BY SOURCE".ljust(23) + "║  BY STATUS".ljust(23) + "║"
    print("╠" + DIVIDER + "╣", file=out)
    print(header, file=out)
    print("║" + "─" * 23 + "╬" + "─" * 23 + "╬" + "─" * 23 + "║", file=out)

    for sev, sv in sev_items:
        src, sc = src_items[sev_items.index((sev, sv))] if sev_items[sev_items.index((sev, sv))] == (sev, sv) else ("", 0)
        # Find matching index
        src_idx = sev_items.index((sev, sv))
        src_val = src_items[src_idx] if src_idx < len(src_items) else ("", 0)
        sta_val = sta_items[src_idx] if src_idx < len(sta_items) else ("", 0)

        sev_emoji = _severity_emoji(sev)
        sev_line = f"  {sev_emoji} {sev}: {sv}".ljust(21)
        src_line = f"  {src}: {sc}".ljust(21)
        sta_line = f"  {sta_val[0]}: {sta_val[1]}".ljust(21)
        print(f"║{sev_line}║{src_line}║{sta_line}║", file=out)

    print("╠" + DIVIDER + "╣", file=out)

    # Overdue section
    if metrics.overdue:
        overdue_count = len(metrics.overdue)
        print(f"║  ⚠️  OVERDUE ({overdue_count})".ljust(BOX_WIDTH - 2) + "║", file=out)
        print("║" + "─" * (BOX_WIDTH - 2) + "║", file=out)
        for fb in metrics.overdue[:10]:  # cap at 10
            label = f"[{fb.severity}] {fb.source}/{fb.source_detail}"
            delta = _fmt_delta(fb.sla_deadline)
            line = f"  {label} — {delta}".ljust(BOX_WIDTH - 4)
            print(f"║{line}║", file=out)
        if len(metrics.overdue) > 10:
            print(f"║  ... and {len(metrics.overdue) - 10} more".ljust(BOX_WIDTH - 2) + "║", file=out)
    else:
        print("║  ✅ NO OVERDUE FEEDBACK".ljust(BOX_WIDTH - 2) + "║", file=out)

    print("╠" + DIVIDER + "╣", file=out)

    # At-risk section
    if metrics.at_risk:
        print(f"║  🔶 AT-RISK ({len(metrics.at_risk)}) — approaching SLA".ljust(BOX_WIDTH - 2) + "║", file=out)
        print("║" + "─" * (BOX_WIDTH - 2) + "║", file=out)
        for fb in metrics.at_risk[:10]:
            label = f"[{fb.severity}] {fb.source}/{fb.source_detail}"
            delta = _fmt_delta(fb.sla_deadline)
            line = f"  {label} — {delta}".ljust(BOX_WIDTH - 4)
            print(f"║{line}║", file=out)

    print("╠" + DIVIDER + "╣", file=out)

    # Recurring issues
    if metrics.recurring:
        print(f"║  📈 RECURRING ISSUES (>=3 occurrences)".ljust(BOX_WIDTH - 2) + "║", file=out)
        print("║" + "─" * (BOX_WIDTH - 2) + "║", file=out)
        for rec in metrics.recurring[:10]:
            line = f"  • {rec['key']}: {rec['count']}x — {rec['recommendation']}".ljust(BOX_WIDTH - 4)
            print(f"║{line}║", file=out)
        if len(metrics.recurring) > 10:
            print(f"║  ... and {len(metrics.recurring) - 10} more".ljust(BOX_WIDTH - 2) + "║", file=out)
    else:
        print("║  ✅ NO RECURRING ISSUES".ljust(BOX_WIDTH - 2) + "║", file=out)

    print("╚" + DIVIDER + "╝", file=out)


# ---------------------------------------------------------------------------
# Rich rendering
# ---------------------------------------------------------------------------

def _print_rich_dashboard(metrics, out: TextIO = sys.stdout) -> None:
    """Render dashboard using the rich library."""
    table = Table(title="Feedback Loop Dashboard", expand=True)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Total Feedback", str(metrics.total_feedback))
    table.add_row("Pending", str(metrics.pending))
    table.add_row("Resolved", str(metrics.resolved))
    table.add_row("Closed", str(metrics.closed))
    table.add_row("Resolution Rate", f"{metrics.resolution_rate * 100:.1f}%")
    table.add_row("Avg Resolution Time", f"{metrics.avg_resolution_time_hours:.1f}h")

    _console.print(table)

    # Severity breakdown
    sev_table = Table(title="By Severity")
    sev_table.add_column("Severity", style="yellow")
    sev_table.add_column("Count", style="cyan", justify="right")
    for sev, count in sorted(metrics.by_severity.items(), key=lambda x: x[1], reverse=True):
        sev_table.add_row(sev, str(count))
    _console.print(sev_table)

    # SLA section
    if metrics.overdue or metrics.at_risk:
        sla_panel_lines = []
        if metrics.overdue:
            sla_panel_lines.append("[red]OVERDUE:[/red]")
            for fb in metrics.overdue[:5]:
                sla_panel_lines.append(f"  [{fb.severity}] {fb.source}/{fb.source_detail} — {_fmt_delta(fb.sla_deadline)}")
        if metrics.at_risk:
            sla_panel_lines.append("[yellow]AT-RISK:[/yellow]")
            for fb in metrics.at_risk[:5]:
                sla_panel_lines.append(f"  [{fb.severity}] {fb.source}/{fb.source_detail} — {_fmt_delta(fb.sla_deadline)}")
        _console.print(Panel("\n".join(sla_panel_lines), title="SLA Status"))

    # Recurring
    if metrics.recurring:
        rec_lines = [f"[bold]Key[/bold]           [bold]Count[/bold]  [bold]Recommendation[/bold]"]
        for rec in metrics.recurring[:10]:
            rec_lines.append(f"{rec['key']}  {rec['count']}x  {rec['recommendation']}")
        _console.print(Panel("\n".join(rec_lines), title="Recurring Issues (3+)"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def print_dashboard(
    store: FeedbackStore | None = None,
    days: int = 30,
    output: TextIO = sys.stdout,
) -> None:
    """
    Print the full ASCII dashboard to *output*.

    Args:
        store: FeedbackStore to analyze. Uses global store if None.
        days: Time window in days for trend data.
        output: File-like object to print to (default sys.stdout).
    """
    metrics = get_dashboard_metrics(store, days)
    # If rich is available and output is a TTY-capable file (not StringIO),
    # use rich rendering; otherwise fall back to ASCII.
    if _HAS_RICH and hasattr(output, "isatty") and output.isatty():
        _print_rich_dashboard(metrics, output)
    else:
        _print_ascii_dashboard(metrics, output)


def print_feedback_list(
    store: FeedbackStore | None = None,
    filters: dict | None = None,
    output: TextIO = sys.stdout,
) -> None:
    """
    Print a list of feedback items, optionally filtered.

    Args:
        store: FeedbackStore to query.
        filters: Dict with optional keys: status, severity, source, assignee, category.
        output: Output stream.
    """
    if store is None:
        store = get_store()

    all_fb = store.list_all()

    if filters:
        if filters.get("status"):
            all_fb = [fb for fb in all_fb if fb.status == filters["status"]]
        if filters.get("severity"):
            all_fb = [fb for fb in all_fb if fb.severity == filters["severity"]]
        if filters.get("source"):
            all_fb = [fb for fb in all_fb if fb.source == filters["source"]]
        if filters.get("assignee"):
            all_fb = [fb for fb in all_fb if fb.assignee == filters["assignee"]]
        if filters.get("category"):
            all_fb = [fb for fb in all_fb if fb.category == filters["category"]]

    now = datetime.now(timezone.utc)
    print(f"{'ID':<38} {'SEV':<8} {'STATUS':<12} {'SOURCE':<15} {'DEADLINE':<25} {'ASSIGNEE'}", file=output)
    print("─" * 120, file=output)
    for fb in sorted(all_fb, key=lambda x: x.timestamp, reverse=True):
        delta = _fmt_delta(fb.sla_deadline, now)
        assignee = fb.assignee or "unassigned"
        print(
            f"{fb.id:<38} {fb.severity:<8} {fb.status:<12} {fb.source:<15} "
            f"{delta:<25} {assignee}",
            file=output,
        )


def print_sla_status(
    store: FeedbackStore | None = None,
    output: TextIO = sys.stdout,
) -> None:
    """
    Print SLA status — overdue and at-risk feedback.

    Args:
        store: FeedbackStore to query.
        output: Output stream.
    """
    metrics = get_dashboard_metrics(store)
    now = datetime.now(timezone.utc)

    print("═" * 60, file=output)
    print("  SLA STATUS", file=output)
    print("═" * 60, file=output)

    if metrics.overdue:
        print(f"\n⚠️  OVERDUE ({len(metrics.overdue)} items):", file=output)
        for fb in metrics.overdue:
            delta = _fmt_delta(fb.sla_deadline, now)
            print(f"  [{fb.severity}] {fb.source}/{fb.source_detail} — {delta}", file=output)

    if metrics.at_risk:
        print(f"\n🔶 AT-RISK ({len(metrics.at_risk)} items):", file=output)
        for fb in metrics.at_risk:
            delta = _fmt_delta(fb.sla_deadline, now)
            print(f"  [{fb.severity}] {fb.source}/{fb.source_detail} — {delta}", file=output)

    if not metrics.overdue and not metrics.at_risk:
        print("✅ All feedback within SLA.", file=output)

    print("═" * 60, file=output)


def print_trend(
    store: FeedbackStore | None = None,
    days: int = 30,
    output: TextIO = sys.stdout,
) -> None:
    """
    Print a simple ASCII trend chart (daily feedback counts).

    Args:
        store: FeedbackStore to query.
        days: Number of days to show.
        output: Output stream.
    """
    metrics = get_dashboard_metrics(store, days)
    trend = metrics.trend_daily

    if not trend:
        print("No trend data available.", file=output)
        return

    sorted_dates = sorted(trend.keys())
    max_val = max(trend.values()) if trend.values() else 1
    bar_width = 50

    print(f"  FEEDBACK TREND — Last {days} days", file=output)
    print("─" * (bar_width + 20), file=output)
    print(f"  {'Date':<12} {'Count':>6}  {'Bar':<50}", file=output)
    print("─" * (bar_width + 20), file=output)

    for date_str in sorted_dates[-days:]:
        count = trend[date_str]
        bar_len = int((count / max_val) * bar_width) if max_val > 0 else 0
        bar = "█" * bar_len
        print(f"  {date_str:<12} {count:>6}  {bar}", file=output)

    print("─" * (bar_width + 20), file=output)
    print(f"  Max: {max_val}  |  Total: {sum(trend.values())}", file=output)
