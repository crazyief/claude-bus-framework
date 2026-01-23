#!/usr/bin/env python3
"""
Session Resume Script - Session Handoff Support

Generates a session context summary for new PM-Architect sessions.
Reads from three sources (Defense in Depth + Session Handoff):
1. Gate records (authoritative state)
2. PM state file (operational context)
3. Latest handoff (cognitive context)

Usage:
    python session_resume.py
    python session_resume.py --json

Output:
    - Prints session context to stdout
    - Creates .claude-bus/SESSION_CONTEXT.md for PM to read

Based on Agent recommendations (2025-12-14):
- Super-AI: Three-layer state reconstruction
- QA-Agent: Cross-validation between sources
- Document-RAG: Gate records as ground truth
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys


# =============================================================================
# CONFIGURATION
# =============================================================================

GATES_DIR = Path(".claude-bus/gates")
PM_STATE_FILE = Path(".claude-bus/pm-state.json")
HANDOFFS_DIR = Path(".claude-bus/handoffs")
OUTPUT_FILE = Path(".claude-bus/SESSION_CONTEXT.md")


# =============================================================================
# GATE RECORD SCANNING
# =============================================================================

def scan_gate_records() -> Dict[str, Any]:
    """
    Scan gate records to determine authoritative state.

    Returns:
        Dictionary with gate scan results
    """
    state = {
        "highest_stage": 0,
        "highest_phase": 0,
        "last_passed_gate": None,
        "gates_found": [],
        "scan_errors": []
    }

    if not GATES_DIR.exists():
        state["scan_errors"].append(f"Gates directory not found: {GATES_DIR}")
        return state

    for stage_dir in sorted(GATES_DIR.glob("stage*")):
        if not stage_dir.is_dir():
            continue

        try:
            stage_num = int(stage_dir.name.replace("stage", ""))
        except ValueError:
            state["scan_errors"].append(f"Invalid stage directory: {stage_dir.name}")
            continue

        for gate_file in sorted(stage_dir.glob("phase*-*-gate*.md")):
            try:
                content = gate_file.read_text(encoding="utf-8")
            except Exception as e:
                state["scan_errors"].append(f"Cannot read {gate_file}: {e}")
                continue

            # Check if PASSED - Support variations: PASS, PASSED, PASS (with tech debt)
            is_passed = (
                "**Status**: PASS" in content or
                "Status**: PASS" in content or
                "**Decision**: PASS" in content or  # Section 6 Decision
                bool(re.search(r"\*\*Status\*\*:\s*PASS(?:ED)?(?:\s*\([^)]+\))?", content, re.IGNORECASE))
            )

            # Extract phase and gate type from filename
            match = re.search(r"phase(\d+)-(input|output)", gate_file.name)
            if match:
                phase_num = int(match.group(1))
                gate_type = match.group(2)

                gate_info = {
                    "stage": stage_num,
                    "phase": phase_num,
                    "type": gate_type,
                    "file": str(gate_file),
                    "passed": is_passed
                }
                state["gates_found"].append(gate_info)

                if is_passed:
                    # Update highest if this gate is passed
                    if stage_num > state["highest_stage"]:
                        state["highest_stage"] = stage_num
                        state["highest_phase"] = phase_num
                        state["last_passed_gate"] = gate_info
                    elif stage_num == state["highest_stage"]:
                        if phase_num > state["highest_phase"]:
                            state["highest_phase"] = phase_num
                            state["last_passed_gate"] = gate_info
                        elif phase_num == state["highest_phase"]:
                            # Output gate is "later" than input gate
                            if gate_type == "output" and state["last_passed_gate"]:
                                if state["last_passed_gate"]["type"] == "input":
                                    state["last_passed_gate"] = gate_info

    return state


# =============================================================================
# PM STATE FILE
# =============================================================================

def read_pm_state() -> Optional[Dict[str, Any]]:
    """Read PM state file if exists."""
    if not PM_STATE_FILE.exists():
        return None

    try:
        content = PM_STATE_FILE.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception as e:
        return {"error": f"Cannot read PM state: {e}"}


def update_pm_state(updates: Dict[str, Any]) -> bool:
    """
    Update PM state file with new values.

    Args:
        updates: Dictionary of fields to update

    Returns:
        True if successful
    """
    try:
        if PM_STATE_FILE.exists():
            current = json.loads(PM_STATE_FILE.read_text(encoding="utf-8"))
        else:
            current = {"version": "1.0"}

        # Merge updates
        current.update(updates)
        current["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # Write atomically (write to temp, then rename)
        temp_file = PM_STATE_FILE.with_suffix(".tmp")
        temp_file.write_text(json.dumps(current, indent=2), encoding="utf-8")
        temp_file.rename(PM_STATE_FILE)

        return True
    except Exception as e:
        print(f"Error updating PM state: {e}", file=sys.stderr)
        return False


# =============================================================================
# HANDOFF FILES
# =============================================================================

def read_latest_handoff() -> Optional[str]:
    """Read most recent handoff file."""
    if not HANDOFFS_DIR.exists():
        return None

    handoffs = sorted(HANDOFFS_DIR.glob("session-*.md"), reverse=True)
    if handoffs:
        try:
            return handoffs[0].read_text(encoding="utf-8")
        except Exception:
            return None
    return None


# =============================================================================
# CROSS-VALIDATION
# =============================================================================

def cross_validate(gate_state: Dict, pm_state: Optional[Dict]) -> List[str]:
    """
    Detect inconsistencies between gate records and PM state.

    Args:
        gate_state: State derived from gate records
        pm_state: State from pm-state.json

    Returns:
        List of warning messages
    """
    warnings = []

    if not pm_state:
        warnings.append("PM state file not found - relying on gate records only")
        return warnings

    if "error" in pm_state:
        warnings.append(f"PM state file error: {pm_state['error']}")
        return warnings

    # Check stage alignment
    if pm_state.get("current_stage") != gate_state.get("highest_stage"):
        if gate_state.get("highest_stage", 0) > 0:
            warnings.append(
                f"Stage mismatch: PM state says stage {pm_state.get('current_stage')}, "
                f"gate records show stage {gate_state.get('highest_stage')}"
            )

    # Check phase alignment
    last_gate = gate_state.get("last_passed_gate")
    if last_gate and pm_state.get("current_phase"):
        expected_phase = last_gate.get("phase", 0)
        if last_gate.get("type") == "output":
            expected_phase += 1  # Output gate passed = now in next phase

        # Allow some flexibility (PM state might be ahead if work started)
        if abs(pm_state.get("current_phase", 0) - expected_phase) > 1:
            warnings.append(
                f"Phase mismatch: PM state says phase {pm_state.get('current_phase')}, "
                f"gate records suggest phase {expected_phase}"
            )

    # Check for stale PM state
    if pm_state.get("updated_at"):
        try:
            updated = datetime.fromisoformat(pm_state["updated_at"].replace("Z", "+00:00"))
            age_hours = (datetime.now(updated.tzinfo) - updated).total_seconds() / 3600
            if age_hours > 24:
                warnings.append(
                    f"PM state is {age_hours:.1f} hours old - may be outdated"
                )
        except Exception:
            pass

    return warnings


# =============================================================================
# CONTEXT GENERATION
# =============================================================================

def determine_next_steps(gate_state: Dict, pm_state: Optional[Dict], warnings: List[str]) -> List[str]:
    """Determine recommended next steps based on state."""
    steps = []

    # If there are warnings, resolve them first
    if warnings:
        steps.append("RESOLVE WARNINGS - State inconsistencies detected (see above)")

    last_gate = gate_state.get("last_passed_gate")

    if last_gate:
        stage = last_gate.get("stage", 1)
        phase = last_gate.get("phase", 1)
        gate_type = last_gate.get("type", "input")

        if gate_type == "output":
            next_phase = phase + 1
            if next_phase > 5:
                # Stage complete
                steps.append(f"Stage {stage} COMPLETE! Start Stage {stage + 1} Phase 1 Planning")
            else:
                steps.append(f"Start Phase {next_phase} Input Gate Validation")
                steps.append(f"Read phase checklist: .claude-bus/planning/stages/stage{stage}/phase{next_phase}-*-checklist.json")
        else:
            steps.append(f"Continue Phase {phase} work (Input Gate passed)")
            steps.append(f"Complete Phase {phase} tasks, then run Output Gate Validation")
    else:
        steps.append("Start Stage 1 Phase 1 Planning")
        steps.append("No passed gates found - beginning from start")

    # Always recommend reading PROJECT_STATUS
    steps.append("Read todo/PROJECT_STATUS.md for full context")

    # Check for pending actions in PM state
    if pm_state and pm_state.get("pending_actions"):
        steps.append(f"Complete {len(pm_state['pending_actions'])} pending actions (see PM state)")

    return steps


def generate_context() -> str:
    """Generate SESSION_CONTEXT.md content."""
    gate_state = scan_gate_records()
    pm_state = read_pm_state()
    handoff = read_latest_handoff()
    warnings = cross_validate(gate_state, pm_state)
    next_steps = determine_next_steps(gate_state, pm_state, warnings)

    lines = [
        "# Session Context (Auto-Generated)",
        "",
        f"**Generated**: {datetime.utcnow().isoformat()}Z",
        f"**Script**: session_resume.py",
        "",
        "---",
        "",
        "## 1. Authoritative State (from Gate Records)",
        "",
    ]

    if gate_state.get("last_passed_gate"):
        last = gate_state["last_passed_gate"]
        lines.extend([
            f"- **Last Passed Gate**: Stage {last['stage']} Phase {last['phase']} {last['type'].upper()}",
            f"- **Gate File**: `{last['file']}`",
            f"- **Total Gates Found**: {len(gate_state.get('gates_found', []))}",
            "",
        ])
    else:
        lines.extend([
            "- **No passed gates found**",
            "- Project appears to be at initial state",
            "",
        ])

    if gate_state.get("scan_errors"):
        lines.extend([
            "### Gate Scan Errors",
            "",
            *[f"- {e}" for e in gate_state["scan_errors"]],
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 2. Operational Context (from PM State)",
        "",
    ])

    if pm_state and "error" not in pm_state:
        lines.extend([
            f"- **Current Stage**: {pm_state.get('current_stage', 'Unknown')}",
            f"- **Current Phase**: {pm_state.get('current_phase', 'Unknown')}",
            f"- **Phase Status**: {pm_state.get('phase_status', 'Unknown')}",
            f"- **Last Updated**: {pm_state.get('updated_at', 'Unknown')}",
            "",
        ])

        if pm_state.get("pending_actions"):
            lines.extend([
                "### Pending Actions",
                "",
                *[f"- [{a.get('priority', 'medium').upper()}] {a.get('description', a)}"
                  for a in pm_state["pending_actions"]],
                "",
            ])

        if pm_state.get("active_blockers"):
            lines.extend([
                "### Active Blockers",
                "",
                *[f"- [{b.get('severity', 'unknown').upper()}] {b.get('description', b)}"
                  for b in pm_state["active_blockers"]],
                "",
            ])

        if pm_state.get("notes"):
            lines.extend([
                "### Notes",
                "",
                pm_state["notes"],
                "",
            ])
    else:
        lines.extend([
            "- PM state file not found or invalid",
            "- Relying on gate records for state",
            "",
        ])

    if warnings:
        lines.extend([
            "---",
            "",
            "## Warnings",
            "",
            *[f"- {w}" for w in warnings],
            "",
        ])

    if handoff:
        lines.extend([
            "---",
            "",
            "## 3. Previous Session Notes",
            "",
            handoff[:2000] if len(handoff) > 2000 else handoff,
            "",
        ])

    lines.extend([
        "---",
        "",
        "## Recommended Next Steps",
        "",
        *[f"{i+1}. {step}" for i, step in enumerate(next_steps)],
        "",
        "---",
        "",
        "*This file is auto-generated. Do not edit manually.*",
        "*Run `python .claude-bus/scripts/session_resume.py` to regenerate.*",
    ])

    return "\n".join(lines)


def generate_json_context() -> Dict[str, Any]:
    """Generate session context as JSON."""
    gate_state = scan_gate_records()
    pm_state = read_pm_state()
    warnings = cross_validate(gate_state, pm_state)
    next_steps = determine_next_steps(gate_state, pm_state, warnings)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "gate_state": {
            "highest_stage": gate_state.get("highest_stage"),
            "highest_phase": gate_state.get("highest_phase"),
            "last_passed_gate": gate_state.get("last_passed_gate"),
            "total_gates": len(gate_state.get("gates_found", [])),
            "scan_errors": gate_state.get("scan_errors", [])
        },
        "pm_state": pm_state if pm_state and "error" not in pm_state else None,
        "warnings": warnings,
        "next_steps": next_steps,
        "has_handoff": HANDOFFS_DIR.exists() and any(HANDOFFS_DIR.glob("session-*.md"))
    }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    args = sys.argv[1:]

    if "-h" in args or "--help" in args:
        print("Usage: python session_resume.py [--json]")
        print()
        print("Generates session context for new PM-Architect sessions.")
        print()
        print("Options:")
        print("  --json    Output in JSON format")
        print()
        print("Output files:")
        print(f"  {OUTPUT_FILE} - Human-readable context (always created)")
        sys.exit(0)

    json_output = "--json" in args

    if json_output:
        context = generate_json_context()
        print(json.dumps(context, indent=2))
    else:
        context = generate_context()

        # Write to file
        try:
            OUTPUT_FILE.write_text(context, encoding="utf-8")
            print(context)
            print()
            print(f"Context written to: {OUTPUT_FILE}")
        except Exception as e:
            print(context)
            print()
            print(f"Warning: Could not write to file: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
