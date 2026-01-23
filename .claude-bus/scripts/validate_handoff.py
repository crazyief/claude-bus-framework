#!/usr/bin/env python3
"""
Handoff Document Validator - P2-004

Validates handoff documents to ensure they contain required information
for session continuity.

Usage:
    python validate_handoff.py <handoff-file.md>
    python validate_handoff.py --latest

Author: PM-Architect-Agent
Created: 2025-12-14 (P2-004)
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
HANDOFFS_DIR = PROJECT_ROOT / ".claude-bus" / "handoffs"

REQUIRED_SECTIONS = [
    "# Session Handoff",
    "## Current State",
]

REQUIRED_FIELDS = [
    ("Stage", r"\*\*Stage\*\*:\s*(\d+|Unknown)"),
    ("Phase", r"\*\*Phase\*\*:\s*(\d+|Unknown)"),
    ("Status", r"\*\*Status\*\*:\s*(\w+)"),
    ("Created", r"\*\*Created\*\*:\s*(\d{4}-\d{2}-\d{2})"),
    ("Trigger", r"\*\*Trigger\*\*:\s*(\w+)"),
]


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_handoff(file_path: Path) -> dict:
    """Validate a handoff document."""
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": [],
    }

    if not file_path.exists():
        result["valid"] = False
        result["errors"].append(f"File not found: {file_path}")
        return result

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Cannot read file: {e}")
        return result

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in content:
            result["errors"].append(f"Missing section: {section}")
            result["valid"] = False

    # Check required fields
    for field_name, pattern in REQUIRED_FIELDS:
        match = re.search(pattern, content)
        if not match:
            result["warnings"].append(f"Missing field: {field_name}")
        else:
            result["info"].append(f"{field_name}: {match.group(1)}")

    # Check for timestamp validity
    created_match = re.search(r"\*\*Created\*\*:\s*(\d{4}-\d{2}-\d{2}T[\d:]+)", content)
    if created_match:
        try:
            created_time = datetime.fromisoformat(created_match.group(1).replace("Z", ""))
            if created_time > datetime.now():
                result["errors"].append("Created timestamp is in the future")
                result["valid"] = False
        except ValueError:
            result["warnings"].append("Invalid timestamp format")

    # Check for actionable content
    has_next_actions = "## Recommended Next Actions" in content or "## Pending Actions" in content
    has_notes = "## Session Notes" in content or "## Current State" in content

    if not has_next_actions and not has_notes:
        result["warnings"].append("Handoff lacks actionable content (no next actions or notes)")

    # Check for tech debt section
    if "## Tech Debt" in content:
        result["info"].append("Tech debt documented")

    return result


def get_latest_handoff() -> Path:
    """Get the most recent handoff file."""
    if not HANDOFFS_DIR.exists():
        return None

    handoffs = list(HANDOFFS_DIR.glob("session-*.md"))
    if not handoffs:
        return None

    # Sort by modification time
    handoffs.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return handoffs[0]


def validate_all_handoffs() -> dict:
    """Validate all handoff documents."""
    results = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "files": [],
    }

    if not HANDOFFS_DIR.exists():
        return results

    for handoff_file in HANDOFFS_DIR.glob("session-*.md"):
        results["total"] += 1
        validation = validate_handoff(handoff_file)

        file_result = {
            "file": str(handoff_file.name),
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
        }
        results["files"].append(file_result)

        if validation["valid"]:
            results["valid"] += 1
        else:
            results["invalid"] += 1

    return results


# =============================================================================
# CLI
# =============================================================================

def print_result(file_path: Path, result: dict) -> None:
    """Print validation result."""
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  📄 Handoff Document Validator (P2-004)                    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")
    print(f"File: {file_path}")
    print("")

    status = "✅ VALID" if result["valid"] else "❌ INVALID"
    print(f"Status: {status}")
    print("")

    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  ❌ {error}")
        print("")

    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  ⚠️  {warning}")
        print("")

    if result["info"]:
        print("Info:")
        for info in result["info"]:
            print(f"  ℹ️  {info}")
        print("")


def main():
    parser = argparse.ArgumentParser(description="Handoff Document Validator")
    parser.add_argument("file", nargs="?", help="Handoff file to validate")
    parser.add_argument("--latest", action="store_true", help="Validate latest handoff")
    parser.add_argument("--all", action="store_true", help="Validate all handoffs")

    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    if args.all:
        results = validate_all_handoffs()
        print("")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║  📄 Handoff Validation Summary                             ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("")
        print(f"Total: {results['total']}, Valid: {results['valid']}, Invalid: {results['invalid']}")
        print("")
        for file_result in results["files"]:
            status = "✅" if file_result["valid"] else "❌"
            print(f"  {status} {file_result['file']}")
        sys.exit(0 if results["invalid"] == 0 else 1)

    if args.latest:
        file_path = get_latest_handoff()
        if not file_path:
            print("No handoff files found")
            sys.exit(1)
    elif args.file:
        file_path = Path(args.file)
    else:
        parser.print_help()
        sys.exit(1)

    result = validate_handoff(file_path)
    print_result(file_path, result)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
