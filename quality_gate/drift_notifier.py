"""
DriftNotifier — 當有 Alert 時發送通知。
支援多種頻道：log、email、slack（可擴展）。

Usage:
    from quality_gate.drift_notifier import DriftNotifier, LogChannel, EmailChannel

    # Basic: log to file
    notifier = DriftNotifier()

    # With email
    notifier = DriftNotifier(channels=[
        LogChannel(),
        EmailChannel(
            smtp_host="smtp.example.com",
            smtp_port=587,
            from_addr="drift@example.com",
            to_addrs=["admin@example.com"],
        ),
    ])

    # Send alert
    notifier.notify(alert)
"""

from pathlib import Path
from typing import Protocol

from quality_gate.drift_monitor import DriftAlert


class NotificationChannel(Protocol):
    """Protocol for notification channels."""

    def send(self, alert: DriftAlert) -> None:
        """Send an alert through this channel."""
        ...


class LogChannel:
    """Write alerts to a log file."""

    def __init__(self, log_path: str = "logs/drift_alerts.log"):
        self.log_path = Path(log_path)
        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, alert: DriftAlert) -> None:
        """Append alert to log file."""
        with open(self.log_path, "a") as f:
            f.write(
                f"[{alert.timestamp}] {alert.severity.upper()}: {alert.message}\n"
            )
            f.write(f"  Alert ID: {alert.id}\n")
            f.write(f"  Drift Score: {alert.drift_score}\n")
            f.write(f"  Artifacts: {', '.join(alert.artifacts)}\n")
            f.write(f"  Recommended Action: {alert.recommended_action}\n")
            f.write(f"  Source: {alert.source}\n")
            f.write("-" * 60 + "\n")


class EmailChannel:
    """Send alerts via email using SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        from_addr: str,
        to_addrs: list[str],
        use_tls: bool = True,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.use_tls = use_tls

    def send(self, alert: DriftAlert) -> None:
        """Send alert as email."""
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)
        msg["Subject"] = f"[DRIFT ALERT] {alert.severity.upper()}: Architecture Drift Detected"
        msg.set_content(
            f"""
Drift Alert Details
===================
Alert ID: {alert.id}
Severity: {alert.severity.upper()}
Drift Score: {alert.drift_score}
Timestamp: {alert.timestamp}
Source: {alert.source}

Message
-------
{alert.message}

Artifacts Affected
-------------------
{', '.join(alert.artifacts) if alert.artifacts else 'None'}

Recommended Action
------------------
{alert.recommended_action}

---
This is an automated alert from DriftMonitor.
        """
        )

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            server.send_message(msg)


class SlackChannel:
    """
    Send alerts to Slack via webhook.
    
    Requires: pip install requests
    """

    def __init__(self, webhook_url: str, channel: str | None = None):
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, alert: DriftAlert) -> None:
        """Send alert to Slack webhook."""
        import json
        import urllib.request

        # Color based on severity
        color_map = {
            "critical": "#FF0000",
            "high": "#FF4500",
            "medium": "#FFA500",
            "low": "#00BFFF",
        }
        color = color_map.get(alert.severity, "#00BFFF")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"[{alert.severity.upper()}] Architecture Drift",
                    "text": alert.message,
                    "fields": [
                        {"title": "Drift Score", "value": str(alert.drift_score), "short": True},
                        {"title": "Alert ID", "value": alert.id, "short": True},
                        {"title": "Artifacts", "value": ", ".join(alert.artifacts) if alert.artifacts else "None", "short": False},
                        {"title": "Recommended Action", "value": alert.recommended_action, "short": False},
                    ],
                    "footer": "DriftMonitor",
                    "ts": int(
                        __import__("datetime")
                        .datetime.fromisoformat(alert.timestamp.replace("Z", "+00:00"))
                        .timestamp()
                    )
                    if alert.timestamp
                    else None,
                }
            ]
        }

        if self.channel:
            payload["channel"] = self.channel

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as response:
            response.read()


class DriftNotifier:
    """
    Drift Alert notifier with support for multiple channels.

    Usage:
        notifier = DriftNotifier([
            LogChannel("logs/drift_alerts.log"),
            EmailChannel(
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                from_addr="alerts@example.com",
                to_addrs=["admin@example.com"],
            ),
        ])
        notifier.notify(alert)
    """

    def __init__(self, channels: list[NotificationChannel] | None = None):
        """
        Initialize with a list of notification channels.

        Args:
            channels: List of NotificationChannel implementations.
                     Defaults to [LogChannel()] if None.
        """
        self.channels = channels or [LogChannel()]

    def notify(self, alert: DriftAlert) -> None:
        """
        Send alert through all configured channels.

        Args:
            alert: The DriftAlert to send.
        """
        for channel in self.channels:
            try:
                channel.send(alert)
            except Exception as e:
                # Log error but continue with other channels
                print(
                    f"[DriftNotifier] Failed to notify via {channel.__class__.__name__}: {e}",
                    file=__import__("sys").stderr,
                )

    def add_channel(self, channel: NotificationChannel) -> None:
        """Add a notification channel at runtime."""
        self.channels.append(channel)
