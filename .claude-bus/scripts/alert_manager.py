#!/usr/bin/env python3
"""
Alert Manager - Unified Notification System

This script replaces verbose CLAUDE.md alert/monitoring instructions with
deterministic code. All agents use this for consistent alert handling.

Usage:
    # Create alert
    python alert_manager.py create --severity critical --message "Service down" --actions "Restart docker"

    # Check alerts before phase transition
    python alert_manager.py check-transition --to-phase 3

    # List active alerts
    python alert_manager.py list

    # Resolve alert
    python alert_manager.py resolve --id notify-001

Author: PM-Architect-Agent
Created: 2025-12-14
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
ALERTS_FILE = PROJECT_ROOT / ".claude-bus" / "notifications" / "user-alerts.jsonl"

SEVERITY_LEVELS = ["critical", "high", "medium", "low"]
NOTIFICATION_TYPES = ["blocker_alert", "service_health", "security", "performance", "tech_debt"]


# =============================================================================
# ALERT SCHEMA
# =============================================================================

def create_alert_record(
    severity: str,
    message: str,
    notification_type: str = "blocker_alert",
    suggested_actions: List[str] = None,
    agent: str = "PM-Architect-Agent"
) -> Dict:
    """
    Create a standardized alert record.

    Args:
        severity: critical, high, medium, low
        message: Alert message
        notification_type: Type of notification
        suggested_actions: List of suggested actions
        agent: Agent creating the alert

    Returns:
        Alert record dictionary
    """
    # Generate next ID
    existing = load_alerts()
    next_id = len(existing) + 1

    return {
        "id": f"notify-{next_id:03d}",
        "timestamp": datetime.now().isoformat(),
        "severity": severity,
        "notification_type": notification_type,
        "message": message,
        "suggested_actions": suggested_actions or [],
        "agent": agent,
        "status": "active"
    }


# =============================================================================
# ALERT OPERATIONS
# =============================================================================

def load_alerts() -> List[Dict]:
    """Load all alerts from file."""
    if not ALERTS_FILE.exists():
        return []

    alerts = []
    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    alerts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return alerts


def save_alert(alert: Dict) -> None:
    """Append alert to file."""
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")


def get_active_alerts() -> List[Dict]:
    """Get only active (unresolved) alerts."""
    return [a for a in load_alerts() if a.get("status") == "active"]


def resolve_alert(alert_id: str) -> bool:
    """Mark alert as resolved."""
    alerts = load_alerts()
    updated = False

    for alert in alerts:
        if alert.get("id") == alert_id:
            alert["status"] = "resolved"
            alert["resolved_at"] = datetime.now().isoformat()
            updated = True
            break

    if updated:
        # Rewrite file
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            for alert in alerts:
                f.write(json.dumps(alert) + "\n")

    return updated


# =============================================================================
# PHASE TRANSITION CHECK (replaces CLAUDE.md verbose protocol)
# =============================================================================

def check_phase_transition(to_phase: int) -> Dict:
    """
    Check if phase transition is allowed based on active alerts.

    This replaces the verbose Phase Transition Protocol in CLAUDE.md.

    Returns:
        dict with: can_proceed, status, message, alerts
    """
    active = get_active_alerts()

    critical = [a for a in active if a.get("severity") == "critical"]
    high = [a for a in active if a.get("severity") == "high"]
    medium_low = [a for a in active if a.get("severity") in ["medium", "low"]]

    if critical:
        return {
            "can_proceed": False,
            "status": "BLOCKED",
            "message": f"Cannot proceed to Phase {to_phase}",
            "reason": f"{len(critical)} critical issue(s) must be resolved first",
            "alerts": critical
        }

    if high:
        return {
            "can_proceed": True,
            "status": "WARNING",
            "message": f"Proceed to Phase {to_phase} with caution",
            "reason": f"{len(high)} high-priority issue(s) detected",
            "alerts": high,
            "requires_confirmation": True
        }

    if medium_low:
        return {
            "can_proceed": True,
            "status": "INFO",
            "message": f"Proceeding to Phase {to_phase}",
            "reason": f"FYI: {len(medium_low)} medium/low priority issue(s)",
            "alerts": medium_low
        }

    return {
        "can_proceed": True,
        "status": "OK",
        "message": f"Clear to proceed to Phase {to_phase}",
        "alerts": []
    }


# =============================================================================
# CLI OUTPUT
# =============================================================================

def print_alert_created(alert: Dict) -> None:
    """Print alert creation confirmation."""
    severity_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵"
    }

    emoji = severity_emoji.get(alert["severity"], "❓")

    print(f"\n{emoji} Alert Created: {alert['id']}")
    print(f"   Severity: {alert['severity'].upper()}")
    print(f"   Message: {alert['message']}")

    if alert.get("suggested_actions"):
        print("   Actions:")
        for action in alert["suggested_actions"]:
            print(f"     → {action}")

    print(f"\n   Logged to: {ALERTS_FILE}")
    print()


def print_transition_check(result: Dict) -> None:
    """Print phase transition check result."""
    status_banner = {
        "BLOCKED": "❌ BLOCKED",
        "WARNING": "⚠️  WARNING",
        "INFO": "📘 INFO",
        "OK": "✅ OK"
    }

    print(f"\n{'='*60}")
    print(f"  Phase Transition Check: {status_banner.get(result['status'], '?')}")
    print(f"{'='*60}\n")

    print(f"  {result['message']}")
    if result.get("reason"):
        print(f"  Reason: {result['reason']}")

    if result.get("alerts"):
        print(f"\n  Active Issues ({len(result['alerts'])}):")
        for alert in result["alerts"]:
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(alert["severity"], "❓")
            print(f"    {emoji} [{alert['id']}] {alert['message']}")

    if result.get("requires_confirmation"):
        print("\n  ⚠️  Confirmation required to proceed.")

    print()


def print_alert_list(alerts: List[Dict]) -> None:
    """Print list of alerts."""
    if not alerts:
        print("\n  No active alerts.\n")
        return

    print(f"\n{'='*60}")
    print(f"  Active Alerts ({len(alerts)})")
    print(f"{'='*60}\n")

    for alert in alerts:
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(alert["severity"], "❓")
        status = "🔓" if alert.get("status") == "resolved" else "🔒"
        print(f"  {emoji} {status} [{alert['id']}] {alert['severity'].upper()}")
        print(f"       {alert['message']}")
        print(f"       Created: {alert.get('timestamp', 'unknown')}")
        print()


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Alert Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create alert")
    create_parser.add_argument("--severity", choices=SEVERITY_LEVELS, required=True)
    create_parser.add_argument("--message", required=True)
    create_parser.add_argument("--type", choices=NOTIFICATION_TYPES, default="blocker_alert")
    create_parser.add_argument("--actions", nargs="+", help="Suggested actions")
    create_parser.add_argument("--agent", default="PM-Architect-Agent")

    # Check transition command
    check_parser = subparsers.add_parser("check-transition", help="Check phase transition")
    check_parser.add_argument("--to-phase", type=int, required=True)
    check_parser.add_argument("--json", action="store_true")

    # List command
    list_parser = subparsers.add_parser("list", help="List alerts")
    list_parser.add_argument("--all", action="store_true", help="Include resolved")
    list_parser.add_argument("--json", action="store_true")

    # Resolve command
    resolve_parser = subparsers.add_parser("resolve", help="Resolve alert")
    resolve_parser.add_argument("--id", required=True)

    args = parser.parse_args()

    if args.command == "create":
        alert = create_alert_record(
            severity=args.severity,
            message=args.message,
            notification_type=args.type,
            suggested_actions=args.actions,
            agent=args.agent
        )
        save_alert(alert)
        print_alert_created(alert)

    elif args.command == "check-transition":
        result = check_phase_transition(args.to_phase)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_transition_check(result)

        # Exit code based on result
        if not result["can_proceed"]:
            sys.exit(1)
        elif result.get("requires_confirmation"):
            sys.exit(2)
        else:
            sys.exit(0)

    elif args.command == "list":
        alerts = load_alerts() if args.all else get_active_alerts()
        if args.json:
            print(json.dumps(alerts, indent=2))
        else:
            print_alert_list(alerts)

    elif args.command == "resolve":
        if resolve_alert(args.id):
            print(f"✅ Alert {args.id} resolved")
        else:
            print(f"❌ Alert {args.id} not found")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
