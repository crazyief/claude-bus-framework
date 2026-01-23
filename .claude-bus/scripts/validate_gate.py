#!/usr/bin/env python3
"""
Gate Validation Script - Defense in Depth Layer 3

Validates that gate records follow the required format and contain
all mandatory information from actual agent invocations.

Usage:
    python validate_gate.py <gate-record-file.md>
    python validate_gate.py <gate-record-file.md> --json

Exit codes:
    0 = VALID (gate record passes all checks)
    1 = INVALID (gate record has errors)
    2 = WARNINGS (gate record has warnings but no errors)

Refactored: 2025-12-14 (TD-S5-003: Split from 702 lines to modular design)
- gate_config.py: Configuration constants and data classes
- gate_validators.py: All validation functions
- gate_output.py: Output formatting
- validate_gate.py: Main entry point (this file)

Author: PM-Architect-Agent
"""

import sys

from gate_config import ValidationResult
from gate_validators import (
    read_file,
    check_required_sections,
    check_metadata,
    check_agent_invocation,
    check_agent_responses,
    check_consolidated_checklist,
    check_unresolved_issues,
    check_signoffs,
    check_gate_decision,
    check_validation_section,
    check_unfilled_placeholders,
    # P1-003: Anti-fabrication checks
    check_timestamp_consistency,
    check_content_integrity,
    check_sequential_consistency,
    # P2-005: Git checkpoint verification
    check_git_checkpoint,
)
from gate_output import print_result, print_json_result


def validate_gate(file_path: str) -> ValidationResult:
    """
    Main validation function.

    Args:
        file_path: Path to the gate record file

    Returns:
        ValidationResult with errors, warnings, and info
    """
    result = ValidationResult(valid=True)

    try:
        content = read_file(file_path)
    except FileNotFoundError as e:
        result.valid = False
        result.errors.append(str(e))
        return result
    except ValueError as e:
        result.valid = False
        result.errors.append(str(e))
        return result
    except PermissionError as e:
        result.valid = False
        result.errors.append(f"Permission denied: {e}")
        return result
    except Exception as e:
        result.valid = False
        result.errors.append(f"Unexpected error: {type(e).__name__}: {e}")
        return result

    # Run all validation checks
    check_required_sections(content, result)
    check_metadata(content, result)
    check_agent_invocation(content, result)
    check_agent_responses(content, result)
    check_consolidated_checklist(content, result)
    check_unresolved_issues(content, result)
    check_signoffs(content, result)
    check_gate_decision(content, result)
    check_validation_section(content, result)
    check_unfilled_placeholders(content, result)

    # P1-003: Anti-fabrication checks
    check_timestamp_consistency(content, file_path, result)
    check_content_integrity(content, result)
    check_sequential_consistency(content, result)

    # P2-005: Git checkpoint verification
    check_git_checkpoint(content, result)

    # Determine overall validity
    result.valid = len(result.errors) == 0

    return result


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ["-h", "--help"]:
        print("Usage: python validate_gate.py <gate-record-file.md> [--json]")
        print()
        print("Options:")
        print("  --json    Output in JSON format (for CI/CD integration)")
        print()
        print("Example:")
        print("  python validate_gate.py .claude-bus/gates/stage5/phase2-output-gate.md")
        sys.exit(0 if args and args[0] in ["-h", "--help"] else 1)

    file_path = args[0]
    json_output = "--json" in args

    result = validate_gate(file_path)

    if json_output:
        print_json_result(result, file_path)
    else:
        print_result(result, file_path)

    # Exit code based on result
    if not result.valid:
        sys.exit(1)
    elif result.warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
