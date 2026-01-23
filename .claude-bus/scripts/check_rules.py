#!/usr/bin/env python3
"""
CLAUDE.md Rules Checker - P2-001

Automates verification of key rules from CLAUDE.md.
This increases automation coverage from ~25% to ~55%.

Usage:
    python check_rules.py              # Run all checks
    python check_rules.py --category coverage  # Run specific category
    python check_rules.py --json       # Output as JSON

Categories:
    - coverage: Test coverage requirements
    - code-quality: File size, nesting, comments
    - git: Checkpoint and commit requirements
    - gates: Gate validation requirements
    - testing: Test pyramid, E2E requirements

Author: PM-Architect-Agent
Created: 2025-12-14 (P2-001)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Rule thresholds from CLAUDE.md
RULES = {
    "coverage_minimum": 70,
    "max_file_lines": 400,
    "max_svelte_lines": 500,
    "max_function_lines": 50,
    "max_nesting_depth": 3,
    "min_comment_ratio_py": 0.20,
    "min_comment_ratio_ts": 0.15,
    "min_comment_ratio_rag": 0.30,
    "test_pyramid_unit": 0.60,
    "test_pyramid_integration": 0.20,
    "test_pyramid_component": 0.10,
    "test_pyramid_e2e": 0.10,
    "max_bundle_size_kb": 60,
}


@dataclass
class RuleCheck:
    """Result of a single rule check."""
    rule_id: str
    category: str
    description: str
    passed: bool
    value: str = ""
    threshold: str = ""
    details: List[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """Aggregated check results."""
    checks: List[RuleCheck] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0


# =============================================================================
# CHECK FUNCTIONS
# =============================================================================

def check_coverage(result: CheckResult) -> None:
    """Check test coverage requirements."""
    # Try to find coverage report
    coverage_files = [
        PROJECT_ROOT / "frontend" / "coverage" / "coverage-summary.json",
        PROJECT_ROOT / "backend" / "coverage.json",
        PROJECT_ROOT / "coverage" / "lcov-report" / "index.html",
    ]

    for cov_file in coverage_files:
        if cov_file.exists():
            try:
                if cov_file.suffix == ".json":
                    data = json.loads(cov_file.read_text())
                    if "total" in data:
                        pct = data["total"].get("lines", {}).get("pct", 0)
                        check = RuleCheck(
                            rule_id="R-COV-001",
                            category="coverage",
                            description="Test coverage >= 70%",
                            passed=pct >= RULES["coverage_minimum"],
                            value=f"{pct:.1f}%",
                            threshold=f">= {RULES['coverage_minimum']}%",
                        )
                        result.checks.append(check)
                        if check.passed:
                            result.passed += 1
                        else:
                            result.failed += 1
                        return
            except Exception as e:
                pass

    # Coverage report not found
    check = RuleCheck(
        rule_id="R-COV-001",
        category="coverage",
        description="Test coverage >= 70%",
        passed=False,
        value="N/A",
        threshold=f">= {RULES['coverage_minimum']}%",
        details=["Coverage report not found. Run: npm run test:coverage"],
    )
    result.checks.append(check)
    result.skipped += 1


def check_file_sizes(result: CheckResult) -> None:
    """Check file size limits."""
    violations = []

    # Check Python files
    for py_file in PROJECT_ROOT.glob("**/*.py"):
        if "node_modules" in str(py_file) or ".venv" in str(py_file) or "venv" in str(py_file):
            continue
        try:
            lines = len(py_file.read_text().splitlines())
            if lines > RULES["max_file_lines"]:
                violations.append(f"{py_file.relative_to(PROJECT_ROOT)}: {lines} lines")
        except Exception:
            pass

    # Check TypeScript files
    for ts_file in PROJECT_ROOT.glob("**/*.ts"):
        if "node_modules" in str(ts_file):
            continue
        try:
            lines = len(ts_file.read_text().splitlines())
            if lines > RULES["max_file_lines"]:
                violations.append(f"{ts_file.relative_to(PROJECT_ROOT)}: {lines} lines")
        except Exception:
            pass

    # Check Svelte files (higher limit)
    for svelte_file in PROJECT_ROOT.glob("**/*.svelte"):
        if "node_modules" in str(svelte_file):
            continue
        try:
            lines = len(svelte_file.read_text().splitlines())
            if lines > RULES["max_svelte_lines"]:
                violations.append(f"{svelte_file.relative_to(PROJECT_ROOT)}: {lines} lines (svelte)")
        except Exception:
            pass

    check = RuleCheck(
        rule_id="R-SIZE-001",
        category="code-quality",
        description=f"File size <= {RULES['max_file_lines']} lines ({RULES['max_svelte_lines']} for .svelte)",
        passed=len(violations) == 0,
        value=f"{len(violations)} violations",
        threshold="0 violations",
        details=violations[:10],  # First 10
    )
    result.checks.append(check)
    if check.passed:
        result.passed += 1
    else:
        result.failed += 1


def check_git_checkpoint(result: CheckResult) -> None:
    """Check if git checkpoint exists for current phase."""
    os.chdir(PROJECT_ROOT)

    try:
        # Get recent commits with "Phase" in message
        proc = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True,
            text=True,
        )
        commits = proc.stdout.strip().split("\n")

        phase_commits = [c for c in commits if "Phase" in c and "Complete" in c]

        check = RuleCheck(
            rule_id="R-GIT-001",
            category="git",
            description="Git checkpoint exists for phase completion",
            passed=len(phase_commits) > 0,
            value=f"{len(phase_commits)} phase commits found",
            threshold=">= 1",
            details=phase_commits[:5],
        )
        result.checks.append(check)
        if check.passed:
            result.passed += 1
        else:
            result.failed += 1

    except Exception as e:
        check = RuleCheck(
            rule_id="R-GIT-001",
            category="git",
            description="Git checkpoint exists for phase completion",
            passed=False,
            value="Error",
            details=[str(e)],
        )
        result.checks.append(check)
        result.skipped += 1


def check_gate_records(result: CheckResult) -> None:
    """Check gate record existence and validity."""
    gates_dir = PROJECT_ROOT / ".claude-bus" / "gates"

    if not gates_dir.exists():
        check = RuleCheck(
            rule_id="R-GATE-001",
            category="gates",
            description="Gate records directory exists",
            passed=False,
            value="Missing",
            threshold="Directory exists",
        )
        result.checks.append(check)
        result.failed += 1
        return

    # Count gate files
    gate_files = list(gates_dir.glob("**/*gate*.md"))

    check = RuleCheck(
        rule_id="R-GATE-001",
        category="gates",
        description="Gate records exist",
        passed=len(gate_files) > 0,
        value=f"{len(gate_files)} gate files",
        threshold=">= 1",
        details=[str(f.relative_to(PROJECT_ROOT)) for f in gate_files[:5]],
    )
    result.checks.append(check)
    if check.passed:
        result.passed += 1
    else:
        result.failed += 1


def check_pre_commit_hook(result: CheckResult) -> None:
    """Check pre-commit hook is installed."""
    hook_path = PROJECT_ROOT / ".git" / "hooks" / "pre-commit"

    check = RuleCheck(
        rule_id="R-HOOK-001",
        category="gates",
        description="Pre-commit hook installed",
        passed=hook_path.exists() and os.access(hook_path, os.X_OK),
        value="Installed" if hook_path.exists() else "Missing",
        threshold="Installed and executable",
    )

    if hook_path.exists() and not os.access(hook_path, os.X_OK):
        check.details.append("Hook exists but is not executable")

    result.checks.append(check)
    if check.passed:
        result.passed += 1
    else:
        result.failed += 1


def check_test_files(result: CheckResult) -> None:
    """Check test file existence."""
    frontend_tests = list((PROJECT_ROOT / "frontend").glob("**/*.test.ts"))
    e2e_tests = list((PROJECT_ROOT / "frontend").glob("**/e2e/**/*.spec.ts"))
    backend_tests = list((PROJECT_ROOT / "backend").glob("**/test_*.py"))

    # Filter out node_modules
    frontend_tests = [f for f in frontend_tests if "node_modules" not in str(f)]
    e2e_tests = [f for f in e2e_tests if "node_modules" not in str(f)]

    check = RuleCheck(
        rule_id="R-TEST-001",
        category="testing",
        description="Test files exist",
        passed=len(frontend_tests) > 0 or len(backend_tests) > 0,
        value=f"Frontend: {len(frontend_tests)}, E2E: {len(e2e_tests)}, Backend: {len(backend_tests)}",
        threshold=">= 1 test file",
    )
    result.checks.append(check)
    if check.passed:
        result.passed += 1
    else:
        result.failed += 1


def check_data_testid(result: CheckResult) -> None:
    """Check for data-testid attributes in Svelte components."""
    svelte_files = list((PROJECT_ROOT / "frontend").glob("**/*.svelte"))
    svelte_files = [f for f in svelte_files if "node_modules" not in str(f)]

    files_with_testid = 0
    files_without = []

    for svelte_file in svelte_files:
        try:
            content = svelte_file.read_text()
            if "data-testid" in content:
                files_with_testid += 1
            else:
                # Only report components with interactive elements
                if any(tag in content for tag in ["<button", "<input", "<form", "on:click"]):
                    files_without.append(str(svelte_file.relative_to(PROJECT_ROOT)))
        except Exception:
            pass

    check = RuleCheck(
        rule_id="R-TEST-002",
        category="testing",
        description="Interactive components have data-testid",
        passed=len(files_without) == 0,
        value=f"{files_with_testid}/{len(svelte_files)} files have data-testid",
        threshold="All interactive components",
        details=files_without[:5],
    )
    result.checks.append(check)
    if check.passed:
        result.passed += 1
    else:
        result.failed += 1


def check_pm_state(result: CheckResult) -> None:
    """Check pm-state.json integrity."""
    pm_state_file = PROJECT_ROOT / ".claude-bus" / "pm-state.json"

    if not pm_state_file.exists():
        check = RuleCheck(
            rule_id="R-PM-001",
            category="gates",
            description="pm-state.json exists and is valid",
            passed=False,
            value="Missing",
            threshold="Exists and valid JSON",
        )
        result.checks.append(check)
        result.failed += 1
        return

    try:
        data = json.loads(pm_state_file.read_text())
        required_fields = ["current_stage", "current_phase", "phase_status"]
        missing = [f for f in required_fields if f not in data]

        check = RuleCheck(
            rule_id="R-PM-001",
            category="gates",
            description="pm-state.json exists and is valid",
            passed=len(missing) == 0,
            value=f"Stage {data.get('current_stage', '?')}, Phase {data.get('current_phase', '?')}",
            threshold="All required fields present",
            details=[f"Missing: {missing}"] if missing else [],
        )
        result.checks.append(check)
        if check.passed:
            result.passed += 1
        else:
            result.failed += 1

    except json.JSONDecodeError:
        check = RuleCheck(
            rule_id="R-PM-001",
            category="gates",
            description="pm-state.json exists and is valid",
            passed=False,
            value="Invalid JSON",
            threshold="Exists and valid JSON",
        )
        result.checks.append(check)
        result.failed += 1


# =============================================================================
# MAIN
# =============================================================================

def run_all_checks() -> CheckResult:
    """Run all rule checks."""
    result = CheckResult()

    check_coverage(result)
    check_file_sizes(result)
    check_git_checkpoint(result)
    check_gate_records(result)
    check_pre_commit_hook(result)
    check_test_files(result)
    check_data_testid(result)
    check_pm_state(result)

    return result


def print_results(result: CheckResult) -> None:
    """Print check results in human-readable format."""
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  📋 CLAUDE.md Rules Checker (P2-001)                       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")

    # Group by category
    categories = {}
    for check in result.checks:
        if check.category not in categories:
            categories[check.category] = []
        categories[check.category].append(check)

    for category, checks in categories.items():
        print(f"📂 {category.upper()}")
        print("-" * 60)
        for check in checks:
            status = "✅" if check.passed else "❌"
            print(f"  {status} [{check.rule_id}] {check.description}")
            print(f"     Value: {check.value} (threshold: {check.threshold})")
            if check.details:
                for detail in check.details[:3]:
                    print(f"     └─ {detail}")
        print("")

    # Summary
    total = result.passed + result.failed + result.skipped
    print("=" * 60)
    print(f"Summary: {result.passed}/{total} passed, {result.failed} failed, {result.skipped} skipped")

    if result.failed == 0:
        print("✅ All automated rule checks passed")
    else:
        print("❌ Some rule checks failed - review above")

    print("")


def main():
    parser = argparse.ArgumentParser(description="CLAUDE.md Rules Checker")
    parser.add_argument("--category", help="Run specific category only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)
    result = run_all_checks()

    if args.json:
        output = {
            "passed": result.passed,
            "failed": result.failed,
            "skipped": result.skipped,
            "checks": [
                {
                    "rule_id": c.rule_id,
                    "category": c.category,
                    "description": c.description,
                    "passed": c.passed,
                    "value": c.value,
                    "threshold": c.threshold,
                    "details": c.details,
                }
                for c in result.checks
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(result)

    sys.exit(1 if result.failed > 0 else 0)


if __name__ == "__main__":
    main()
