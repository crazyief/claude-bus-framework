#!/usr/bin/env python3
"""
Gate Validation Output - Defense in Depth Layer 3

Contains output formatting functions for gate validation results.

Author: PM-Architect-Agent
Created: 2025-12-14
"""

import json
from datetime import datetime

from gate_config import ValidationResult


def print_result(result: ValidationResult, file_path: str) -> None:
    """Print validation result in formatted box output."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║  Gate Validation Check (Layer 3)   " + " " * 21 + "║")
    print("╠" + "═" * 58 + "╣")
    print(f"║  File: {file_path[:48]:<48}  ║")
    print("╠" + "═" * 58 + "╣")

    if result.errors:
        print(f"║  ❌ ERRORS ({len(result.errors)}):" + " " * (44 - len(str(len(result.errors)))) + "║")
        for error in result.errors:
            wrapped = error[:52]
            print(f"║  - {wrapped:<54}║")
            if len(error) > 52:
                wrapped2 = error[52:104]
                print(f"║    {wrapped2:<54}║")
        print("║" + " " * 58 + "║")

    if result.warnings:
        print(f"║  ⚠️  WARNINGS ({len(result.warnings)}):" + " " * (40 - len(str(len(result.warnings)))) + "║")
        for warning in result.warnings:
            wrapped = warning[:52]
            print(f"║  - {wrapped:<54}║")
        print("║" + " " * 58 + "║")

    if not result.errors and not result.warnings:
        print("║  ✅ No errors or warnings found" + " " * 26 + "║")
        print("║" + " " * 58 + "║")

    print("╠" + "═" * 58 + "╣")

    if result.valid:
        print("║  Result: ✅ VALID - Gate record passes validation" + " " * 7 + "║")
    else:
        print("║  Result: ❌ INVALID - Fix errors before proceeding" + " " * 6 + "║")

    print("╚" + "═" * 58 + "╝")
    print()


def print_json_result(result: ValidationResult, file_path: str) -> None:
    """Print validation result as JSON for CI/CD integration."""
    output = {
        "file": file_path,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **result.to_dict()
    }
    print(json.dumps(output, indent=2))
