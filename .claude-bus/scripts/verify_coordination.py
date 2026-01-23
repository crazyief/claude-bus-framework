#!/usr/bin/env python3
"""
Multi-Agent Coordination Verifier - P2-002

Verifies that multi-agent coordination follows the expected patterns.
Checks events.jsonl for proper agent invocation sequences.

Usage:
    python verify_coordination.py                    # Verify recent events
    python verify_coordination.py --stage 5 --phase 2  # Verify specific phase
    python verify_coordination.py --json             # Output as JSON

Author: PM-Architect-Agent
Created: 2025-12-14 (P2-002)
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
EVENTS_FILE = PROJECT_ROOT / ".claude-bus" / "events.jsonl"

REQUIRED_AGENTS = [
    "PM-Architect-Agent",
    "Backend-Agent",
    "Frontend-Agent",
    "QA-Agent",
    "Document-RAG-Agent",
    "Super-AI-UltraThink-Agent",
    "frontend-debug-agent",
]

# Expected coordination patterns
EXPECTED_PATTERNS = {
    "gate_validation": {
        "description": "Gate validation should invoke all 6 agents",
        "required_agents": REQUIRED_AGENTS[1:],  # Exclude PM (PM triggers it)
        "min_agents": 6,
    },
    "phase_2_development": {
        "description": "Phase 2 should invoke development agents in parallel",
        "required_agents": ["Backend-Agent", "Frontend-Agent", "Document-RAG-Agent"],
        "min_agents": 2,
    },
    "phase_3_review": {
        "description": "Phase 3 should invoke QA-Agent for review",
        "required_agents": ["QA-Agent"],
        "min_agents": 1,
    },
}


# =============================================================================
# EVENT PARSING
# =============================================================================

def parse_events(limit: int = 500) -> List[dict]:
    """Parse events from events.jsonl."""
    events = []

    if not EVENTS_FILE.exists():
        return events

    try:
        with open(EVENTS_FILE, "r") as f:
            lines = f.readlines()[-limit:]

        for line in lines:
            try:
                event = json.loads(line.strip())
                events.append(event)
            except json.JSONDecodeError:
                continue

    except Exception:
        pass

    return events


def extract_agent_invocations(events: List[dict]) -> Dict[str, List[dict]]:
    """Extract agent invocation events grouped by context."""
    invocations = defaultdict(list)

    for event in events:
        event_str = json.dumps(event).lower()

        # Look for agent mentions
        for agent in REQUIRED_AGENTS:
            if agent.lower() in event_str:
                # Determine context (gate, phase, etc.)
                context = "unknown"
                if "gate" in event_str:
                    context = "gate"
                elif "phase" in event_str:
                    # Extract phase number
                    phase_match = re.search(r"phase\s*(\d+)", event_str)
                    if phase_match:
                        context = f"phase_{phase_match.group(1)}"
                elif "task" in event_str:
                    context = "task"

                invocations[context].append({
                    "agent": agent,
                    "timestamp": event.get("timestamp", ""),
                    "event_type": event.get("type", ""),
                })

    return dict(invocations)


def verify_gate_coordination(events: List[dict]) -> dict:
    """Verify that gate validations have proper agent coordination."""
    result = {
        "pattern": "gate_validation",
        "verified": False,
        "findings": [],
        "agent_count": 0,
        "agents_found": [],
    }

    # Look for gate-related events
    gate_events = [e for e in events if "gate" in json.dumps(e).lower()]

    if not gate_events:
        result["findings"].append("No gate events found in recent history")
        return result

    # Check which agents were involved
    agents_found = set()
    for event in gate_events:
        event_str = json.dumps(event).lower()
        for agent in REQUIRED_AGENTS:
            if agent.lower() in event_str:
                agents_found.add(agent)

    result["agents_found"] = list(agents_found)
    result["agent_count"] = len(agents_found)

    expected = EXPECTED_PATTERNS["gate_validation"]
    if len(agents_found) >= expected["min_agents"]:
        result["verified"] = True
        result["findings"].append(f"Found {len(agents_found)}/6 agents in gate events")
    else:
        result["findings"].append(
            f"Only {len(agents_found)}/6 agents found. Missing: {set(REQUIRED_AGENTS) - agents_found}"
        )

    return result


def verify_phase_coordination(events: List[dict], phase: int) -> dict:
    """Verify coordination for a specific phase."""
    result = {
        "pattern": f"phase_{phase}",
        "verified": False,
        "findings": [],
        "agents_found": [],
    }

    # Look for phase-specific events
    phase_events = [
        e for e in events
        if f"phase {phase}" in json.dumps(e).lower()
        or f"phase{phase}" in json.dumps(e).lower()
    ]

    if not phase_events:
        result["findings"].append(f"No events found for Phase {phase}")
        return result

    # Check which agents were involved
    agents_found = set()
    for event in phase_events:
        event_str = json.dumps(event).lower()
        for agent in REQUIRED_AGENTS:
            if agent.lower() in event_str:
                agents_found.add(agent)

    result["agents_found"] = list(agents_found)

    # Determine expected pattern based on phase
    if phase == 2:
        expected = EXPECTED_PATTERNS["phase_2_development"]
    elif phase == 3:
        expected = EXPECTED_PATTERNS["phase_3_review"]
    else:
        expected = {"required_agents": [], "min_agents": 1}

    # Check if required agents are present
    required = set(expected.get("required_agents", []))
    missing = required - agents_found

    if not missing and len(agents_found) >= expected.get("min_agents", 1):
        result["verified"] = True
        result["findings"].append(f"All expected agents found for Phase {phase}")
    else:
        if missing:
            result["findings"].append(f"Missing required agents: {missing}")
        result["findings"].append(f"Found: {agents_found}")

    return result


def generate_coordination_report(events: List[dict]) -> dict:
    """Generate a comprehensive coordination report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "events_analyzed": len(events),
        "verifications": [],
        "overall_status": "UNKNOWN",
    }

    # Verify gate coordination
    gate_result = verify_gate_coordination(events)
    report["verifications"].append(gate_result)

    # Verify phase coordination for phases 2 and 3
    for phase in [2, 3]:
        phase_result = verify_phase_coordination(events, phase)
        report["verifications"].append(phase_result)

    # Determine overall status
    verified_count = sum(1 for v in report["verifications"] if v["verified"])
    total = len(report["verifications"])

    if verified_count == total:
        report["overall_status"] = "VERIFIED"
    elif verified_count > 0:
        report["overall_status"] = "PARTIAL"
    else:
        report["overall_status"] = "UNVERIFIED"

    return report


# =============================================================================
# CLI
# =============================================================================

def print_report(report: dict) -> None:
    """Print coordination report in human-readable format."""
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤝 Multi-Agent Coordination Verifier (P2-002)             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")
    print(f"Events analyzed: {report['events_analyzed']}")
    print(f"Report time: {report['timestamp']}")
    print("")

    for verification in report["verifications"]:
        status = "✅" if verification["verified"] else "❌"
        print(f"{status} {verification['pattern']}")
        for finding in verification["findings"]:
            print(f"   └─ {finding}")
        if verification["agents_found"]:
            print(f"   └─ Agents: {', '.join(verification['agents_found'][:5])}")
        print("")

    print("=" * 60)
    print(f"Overall Status: {report['overall_status']}")
    print("")


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Coordination Verifier")
    parser.add_argument("--stage", type=int, help="Stage to verify")
    parser.add_argument("--phase", type=int, help="Phase to verify")
    parser.add_argument("--limit", type=int, default=500, help="Events to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)
    events = parse_events(args.limit)

    if not events:
        print("No events found in events.jsonl")
        sys.exit(1)

    report = generate_coordination_report(events)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    # Exit code based on status
    if report["overall_status"] == "VERIFIED":
        sys.exit(0)
    elif report["overall_status"] == "PARTIAL":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
