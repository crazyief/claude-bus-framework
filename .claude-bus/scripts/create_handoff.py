#!/usr/bin/env python3
"""
Create Handoff Script - Session Handoff Support

Creates a session handoff document to preserve cognitive context
between PM-Architect sessions.

Usage:
    python create_handoff.py
    python create_handoff.py --phase-complete
    python create_handoff.py --blocker "description"

Author: PM-Architect-Agent
Created: 2025-12-14 (TD-S5-004)
"""

import json
import sys
from datetime import datetime
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

HANDOFFS_DIR = Path(".claude-bus/handoffs")
PM_STATE_FILE = Path(".claude-bus/pm-state.json")
GATES_DIR = Path(".claude-bus/gates")


def get_next_session_number() -> int:
    """Get next session number for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    existing = list(HANDOFFS_DIR.glob(f"session-{today}-*.md"))
    if not existing:
        return 1
    numbers = []
    for f in existing:
        try:
            num = int(f.stem.split("-")[-1])
            numbers.append(num)
        except ValueError:
            continue
    return max(numbers) + 1 if numbers else 1


def read_pm_state() -> dict:
    """Read current PM state."""
    if not PM_STATE_FILE.exists():
        return {}
    try:
        return json.loads(PM_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_latest_gate_info() -> dict:
    """Get info from latest gate record."""
    if not GATES_DIR.exists():
        return {}

    latest_gate = None
    latest_time = None

    for stage_dir in GATES_DIR.glob("stage*"):
        for gate_file in stage_dir.glob("phase*-*-gate*.md"):
            mtime = gate_file.stat().st_mtime
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_gate = gate_file

    if latest_gate:
        return {
            "file": str(latest_gate),
            "modified": datetime.fromtimestamp(latest_time).isoformat()
        }
    return {}


def create_handoff(
    trigger: str = "manual",
    notes: str = "",
    decisions: list = None,
    next_actions: list = None,
    blockers: list = None
) -> str:
    """
    Create a handoff document.

    Args:
        trigger: What triggered this handoff (manual, phase-complete, blocker)
        notes: Free-form notes about current state
        decisions: List of decisions made this session
        next_actions: List of recommended next actions
        blockers: List of current blockers

    Returns:
        Path to created handoff file
    """
    HANDOFFS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    session_num = get_next_session_number()
    filename = f"session-{today}-{session_num:02d}.md"
    filepath = HANDOFFS_DIR / filename

    pm_state = read_pm_state()
    gate_info = get_latest_gate_info()

    # Build content
    lines = [
        f"# Session Handoff: {today} #{session_num:02d}",
        "",
        f"**Created**: {datetime.now().isoformat()}Z",
        f"**Trigger**: {trigger}",
        "",
        "---",
        "",
        "## Current State",
        "",
        f"- **Stage**: {pm_state.get('current_stage', 'Unknown')}",
        f"- **Phase**: {pm_state.get('current_phase', 'Unknown')}",
        f"- **Status**: {pm_state.get('phase_status', 'Unknown')}",
        "",
    ]

    if gate_info:
        lines.extend([
            f"- **Latest Gate**: `{gate_info.get('file', 'Unknown')}`",
            f"- **Gate Modified**: {gate_info.get('modified', 'Unknown')}",
            "",
        ])

    if notes:
        lines.extend([
            "---",
            "",
            "## Session Notes",
            "",
            notes,
            "",
        ])

    if decisions:
        lines.extend([
            "---",
            "",
            "## Decisions Made This Session",
            "",
            *[f"- {d}" for d in decisions],
            "",
        ])

    if blockers:
        lines.extend([
            "---",
            "",
            "## Current Blockers",
            "",
            *[f"- ❌ {b}" for b in blockers],
            "",
        ])

    if next_actions:
        lines.extend([
            "---",
            "",
            "## Recommended Next Actions",
            "",
            *[f"{i+1}. {a}" for i, a in enumerate(next_actions)],
            "",
        ])

    # Add pending actions from PM state
    if pm_state.get("pending_actions"):
        lines.extend([
            "---",
            "",
            "## Pending Actions (from PM State)",
            "",
            *[f"- [{a.get('priority', 'medium').upper()}] {a.get('description', a)}"
              for a in pm_state["pending_actions"]],
            "",
        ])

    # Add tech debt
    if pm_state.get("tech_debt"):
        lines.extend([
            "---",
            "",
            "## Tech Debt",
            "",
            *[f"- {td.get('id', '?')}: {td.get('description', '?')} ({td.get('severity', '?')})"
              for td in pm_state["tech_debt"]],
            "",
        ])

    lines.extend([
        "---",
        "",
        "*This handoff was auto-generated. Edit as needed.*",
    ])

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")

    return str(filepath)


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if "-h" in args or "--help" in args:
        print("Usage: python create_handoff.py [options]")
        print()
        print("Options:")
        print("  --phase-complete    Mark handoff as phase completion")
        print("  --blocker \"desc\"    Create handoff due to blocker")
        print("  --note \"text\"       Add session notes")
        print()
        print("Example:")
        print("  python create_handoff.py --phase-complete")
        print("  python create_handoff.py --blocker \"Waiting for user input\"")
        sys.exit(0)

    trigger = "manual"
    notes = ""
    blockers = []

    # Parse arguments
    i = 0
    while i < len(args):
        if args[i] == "--phase-complete":
            trigger = "phase-complete"
        elif args[i] == "--blocker" and i + 1 < len(args):
            trigger = "blocker"
            blockers.append(args[i + 1])
            i += 1
        elif args[i] == "--note" and i + 1 < len(args):
            notes = args[i + 1]
            i += 1
        i += 1

    # Default next actions based on PM state
    pm_state = read_pm_state()
    next_actions = []

    if pm_state.get("next_required_gate"):
        gate = pm_state["next_required_gate"]
        next_actions.append(
            f"Run Phase {gate.get('phase', '?')} {gate.get('type', '?').title()} Gate Validation"
        )

    filepath = create_handoff(
        trigger=trigger,
        notes=notes,
        blockers=blockers if blockers else None,
        next_actions=next_actions if next_actions else None
    )

    print(f"✅ Handoff created: {filepath}")
    print()
    print("Contents:")
    print("-" * 40)
    print(Path(filepath).read_text())


if __name__ == "__main__":
    main()
