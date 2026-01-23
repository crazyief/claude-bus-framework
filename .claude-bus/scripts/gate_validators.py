#!/usr/bin/env python3
"""
Gate Validation Functions - Defense in Depth Layer 3

Contains all validation functions for gate record checking.

Author: PM-Architect-Agent
Created: 2025-12-14
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from gate_config import (
    ValidationResult,
    REQUIRED_SECTIONS,
    REQUIRED_AGENTS,
    VALID_AGENT_STATUSES,
    VALID_GATE_DECISIONS,
    VALID_SIGNOFF_VALUES,
    MIN_SUMMARY_LENGTH,
    MAX_FILE_SIZE,
)


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def read_file(file_path: str) -> str:
    """Read gate record file with error handling."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Gate record not found: {file_path}")

    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE})")

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"File encoding error: {file_path} is not valid UTF-8. Error: {e}")

    if not content.strip():
        raise ValueError(f"Gate record file is empty: {file_path}")

    return content


# =============================================================================
# SECTION VALIDATORS
# =============================================================================

def check_required_sections(content: str, result: ValidationResult) -> None:
    """Check that all required sections are present."""
    for section in REQUIRED_SECTIONS:
        if section not in content:
            result.errors.append(
                f"Missing required section: '{section}'. "
                f"Copy from template: .claude-bus/templates/gate-validation-template.md"
            )
        else:
            result.info.append(f"Found section: '{section}'")


def check_metadata(content: str, result: ValidationResult) -> None:
    """Check gate metadata fields."""
    # Check Stage
    if not re.search(r"\*\*Stage\*\*:\s*\d+", content):
        result.errors.append("Missing or invalid Stage number. Add: **Stage**: N")

    # Check Phase
    if not re.search(r"\*\*Phase\*\*:\s*\d+", content):
        result.errors.append("Missing or invalid Phase number. Add: **Phase**: N")

    # Check Gate Type
    if not re.search(r"\*\*Gate Type\*\*:\s*(Input|Output)", content):
        result.errors.append("Missing or invalid Gate Type. Add: **Gate Type**: Input or Output")

    # Check Date
    date_match = re.search(r"\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
    if not date_match:
        result.errors.append("Missing or invalid Date. Add: **Date**: YYYY-MM-DD")
    else:
        try:
            parsed_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            if parsed_date > datetime.now().replace(year=datetime.now().year + 1):
                result.warnings.append(f"Date {date_match.group(1)} is more than 1 year in future")
        except ValueError:
            result.errors.append(f"Invalid date format: {date_match.group(1)}")

    # Check Status - Support PASS/PASSED/PASS (with tech debt)
    if not re.search(r"\*\*Status\*\*:\s*(PENDING|PASS(?:ED)?(?:\s*\([^)]+\))?|FAIL(?:ED)?)", content, re.IGNORECASE):
        result.errors.append("Missing or invalid Status. Add: **Status**: PENDING, PASS, or FAIL")


def check_agent_invocation(content: str, result: ValidationResult) -> None:
    """Check Section 1: Agent Invocation Evidence."""
    section_match = re.search(
        r"## Section 1: Agent Invocation Evidence.*?(?=## Section 2:|$)",
        content, re.DOTALL
    )
    if not section_match:
        result.errors.append("Cannot parse Section 1: Agent Invocation Evidence")
        return

    section = section_match.group(0)

    # Check timestamp
    timestamp_match = re.search(
        r"\*\*Invocation Timestamp\*\*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", section
    )
    if not timestamp_match:
        result.errors.append("Missing Invocation Timestamp. Add: **Invocation Timestamp**: ISO 8601")
    else:
        try:
            datetime.fromisoformat(timestamp_match.group(1).replace("Z", "+00:00"))
        except ValueError:
            result.errors.append(f"Invalid timestamp format: {timestamp_match.group(1)}")

    # Check agents
    agents_invoked = 0
    for agent in REQUIRED_AGENTS:
        agent_pattern = rf"\|\s*{re.escape(agent)}\s*\|\s*(YES|NO)\s*\|"
        match = re.search(agent_pattern, section)
        if match:
            if match.group(1) == "YES":
                agents_invoked += 1
        else:
            result.errors.append(f"Agent '{agent}' not listed in invocation table")

    # G-001: ALL 6 agents required
    if agents_invoked < 6:
        result.errors.append(f"BLOCKING: Only {agents_invoked}/6 agents invoked. G-001 requires ALL 6.")

    # Check verification checkboxes
    unchecked = section.count("[ ]")
    if unchecked > 0:
        result.errors.append(f"Unchecked verification items in Section 1 ({unchecked} items)")


def check_agent_responses(content: str, result: ValidationResult) -> List[str]:
    """Check Section 2: Agent Responses. Returns agents with concerns."""
    section_match = re.search(
        r"## Section 2: Agent Responses.*?(?=## Section 3:|$)",
        content, re.DOTALL
    )
    if not section_match:
        result.errors.append("Cannot parse Section 2: Agent Responses")
        return []

    section = section_match.group(0)
    agents_with_concerns = []

    for agent in REQUIRED_AGENTS:
        agent_pattern = rf"### {re.escape(agent)} Response.*?(?=###|## Section 3:|$)"
        agent_match = re.search(agent_pattern, section, re.DOTALL)

        if not agent_match:
            result.errors.append(f"Missing response section for '{agent}'")
            continue

        agent_section = agent_match.group(0)

        # Check Status
        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", agent_section)
        if not status_match:
            result.errors.append(f"Missing Status for '{agent}'")
        elif status_match.group(1) not in VALID_AGENT_STATUSES:
            result.errors.append(f"Invalid Status '{status_match.group(1)}' for '{agent}'")
        elif status_match.group(1) in ["CONCERN", "QUESTION"]:
            agents_with_concerns.append(agent)

        # Check Summary length
        summary_match = re.search(
            r"\*\*Summary\*\*.*?:\s*\n(.+?)(?=\*\*Checklist|\n\n|$)",
            agent_section, re.DOTALL
        )
        if summary_match:
            summary = summary_match.group(1).strip()
            if "[REQUIRED" in summary:
                result.errors.append(f"'{agent}' summary contains unfilled placeholder")
            elif len(summary) < MIN_SUMMARY_LENGTH:
                result.warnings.append(f"'{agent}' summary too short ({len(summary)} chars)")
        else:
            result.errors.append(f"Missing Summary for '{agent}'")

    return agents_with_concerns


def check_consolidated_checklist(content: str, result: ValidationResult) -> None:
    """Check Section 3: Consolidated Checklist."""
    section_match = re.search(
        r"## Section 3: Consolidated Checklist.*?(?=## Section 4:|$)",
        content, re.DOTALL
    )
    if not section_match:
        result.errors.append("Cannot parse Section 3: Consolidated Checklist")
        return

    section = section_match.group(0)
    table_rows = re.findall(r"\|\s*\d+\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|", section)

    if not table_rows:
        result.warnings.append("No checklist items found in Section 3")
    else:
        result.info.append(f"Found {len(table_rows)} checklist items")
        for i, row in enumerate(table_rows, 1):
            if "[REQUIRED]" in row:
                result.errors.append(f"Checklist item #{i} contains unfilled placeholder")
            has_valid_source = any(agent in row for agent in REQUIRED_AGENTS)
            if not has_valid_source and "PM-Architect" not in row:
                result.warnings.append(f"Checklist item #{i} may be missing source agent")

    if not re.search(r"\*\*Total Items\*\*:\s*\d+", section):
        result.errors.append("Missing Total Items count")


def check_unresolved_issues(content: str, result: ValidationResult) -> None:
    """Check Section 4: Unresolved Issues."""
    section_match = re.search(
        r"## Section 4: Unresolved Issues.*?(?=## Section 5:|$)",
        content, re.DOTALL
    )
    if not section_match:
        result.errors.append("Cannot parse Section 4: Unresolved Issues")
        return

    section = section_match.group(0)
    has_concerns = re.search(r'\*\*Status\*\*:\s*(CONCERN|QUESTION)', content)
    issue_rows = re.findall(r'\|\s*\d+\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|', section)
    has_issues = len(issue_rows) > 0 or "None" in section

    if has_concerns and not has_issues:
        result.errors.append("Agents raised CONCERN/QUESTION but Section 4 has no issues listed")


def check_signoffs(content: str, result: ValidationResult) -> None:
    """Check Section 5: Sign-offs."""
    section_match = re.search(
        r"## Section 5: Sign-offs.*?(?=## Section 6:|$)",
        content, re.DOTALL
    )
    if not section_match:
        result.errors.append("Cannot parse Section 5: Sign-offs")
        return

    section = section_match.group(0)

    # PM-Architect sign-off required
    pm_match = re.search(
        r"\|\s*PM-Architect-Agent\s*\|\s*(APPROVED|REJECTED|CONDITIONAL)\s*\|", section
    )
    if not pm_match:
        result.errors.append("PM-Architect-Agent sign-off missing or invalid")

    # Check other agents
    for agent in REQUIRED_AGENTS:
        agent_pattern = rf"\|\s*{re.escape(agent)}\s*\|\s*(APPROVED|REJECTED|CONDITIONAL|N/A)\s*\|"
        if not re.search(agent_pattern, section):
            result.errors.append(f"'{agent}' sign-off missing or invalid")


def check_gate_decision(content: str, result: ValidationResult) -> None:
    """Check Section 6: Gate Decision with cross-validation."""
    section_match = re.search(
        r"## Section 6: Gate Decision.*?(?=## Section 7:|$)",
        content, re.DOTALL
    )
    if not section_match:
        result.errors.append("Cannot parse Section 6: Gate Decision")
        return

    section = section_match.group(0)
    decision_match = re.search(r"\*\*Decision\*\*:\s*(\w+)", section)

    if not decision_match:
        result.errors.append("Missing Gate Decision. Add: **Decision**: PASS, FAIL, or CONDITIONAL")
    elif decision_match.group(1) not in VALID_GATE_DECISIONS:
        result.errors.append(f"Invalid Decision '{decision_match.group(1)}'")
    else:
        decision = decision_match.group(1)
        # Cross-validate: PASS should not have REJECTED PM sign-off
        pm_rejected = re.search(r'\|\s*PM-Architect-Agent\s*\|\s*REJECTED\s*\|', content)
        if decision == "PASS" and pm_rejected:
            result.errors.append("INCONSISTENCY: Decision is PASS but PM-Architect signed REJECTED")
        if decision == "FAIL" and "Blocking Issues" not in section:
            result.warnings.append("Decision is FAIL but no Blocking Issues documented")
        if decision == "CONDITIONAL" and "Conditions" not in section:
            result.warnings.append("Decision is CONDITIONAL but no Conditions documented")


def check_validation_section(content: str, result: ValidationResult) -> None:
    """Check Section 7: Validation."""
    section_match = re.search(
        r"## Section 7: Validation.*?(?=## Document History|$)",
        content, re.DOTALL
    )
    if not section_match:
        result.errors.append("Cannot parse Section 7: Validation")
        return

    section = section_match.group(0)

    if not re.search(r"\*\*Validation Result\*\*:\s*(VALID|INVALID)", section):
        result.warnings.append("Validation Result not yet filled")

    if not re.search(r"\*\*Validation Timestamp\*\*:\s*\d{4}-\d{2}-\d{2}T", section):
        result.warnings.append("Validation Timestamp not yet filled")


def check_unfilled_placeholders(content: str, result: ValidationResult) -> None:
    """Check for unfilled template placeholders."""
    placeholders = re.findall(r"\[REQUIRED[^\]]*\]", content)
    if placeholders:
        result.errors.append(f"Found {len(placeholders)} unfilled [REQUIRED] placeholders")
        for p in list(set(placeholders))[:5]:
            result.info.append(f"  Placeholder: {p}")


# =============================================================================
# P1-003: ANTI-FABRICATION CHECKS
# =============================================================================

def check_timestamp_consistency(content: str, file_path: str, result: ValidationResult) -> None:
    """
    P1-003: Check for timestamp fabrication indicators.

    Validates:
    1. Gate date is not in the future
    2. Invocation timestamp is not in the future
    3. Validation timestamp is not before invocation
    4. File modification time roughly matches document timestamps
    """
    now = datetime.now()

    # Check gate date
    date_match = re.search(r"\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
    if date_match:
        try:
            gate_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            if gate_date.date() > now.date():
                result.errors.append(
                    f"FABRICATION INDICATOR: Gate date {date_match.group(1)} is in the future"
                )
        except ValueError:
            pass

    # Check invocation timestamp
    invoc_match = re.search(
        r"\*\*Invocation Timestamp\*\*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", content
    )
    if invoc_match:
        try:
            invoc_time = datetime.fromisoformat(invoc_match.group(1).replace("Z", ""))
            if invoc_time > now:
                result.errors.append(
                    f"FABRICATION INDICATOR: Invocation timestamp is in the future"
                )
        except ValueError:
            pass

    # Check validation timestamp
    valid_match = re.search(
        r"\*\*Validation Timestamp\*\*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", content
    )
    if valid_match and invoc_match:
        try:
            valid_time = datetime.fromisoformat(valid_match.group(1).replace("Z", ""))
            invoc_time = datetime.fromisoformat(invoc_match.group(1).replace("Z", ""))
            if valid_time < invoc_time:
                result.errors.append(
                    "FABRICATION INDICATOR: Validation timestamp is before invocation timestamp"
                )
        except ValueError:
            pass

    # Check file modification time vs document date
    path = Path(file_path)
    if path.exists():
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if date_match:
            try:
                gate_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                # If file was modified more than 7 days before the claimed date, suspicious
                if mtime.date() < gate_date.date():
                    days_diff = (gate_date.date() - mtime.date()).days
                    if days_diff > 7:
                        result.warnings.append(
                            f"SUSPICIOUS: File mtime is {days_diff} days before claimed gate date"
                        )
            except ValueError:
                pass


def check_content_integrity(content: str, result: ValidationResult) -> None:
    """
    P1-003: Check for content fabrication indicators.

    Validates:
    1. Agent responses are not copy-paste duplicates
    2. Checklist items have variety (not all identical)
    3. Signatures are from correct agents (not wrong names)
    """
    # Check for duplicate agent responses (sign of copy-paste fabrication)
    summaries = re.findall(r"\*\*Summary\*\*.*?:\s*\n(.+?)(?=\*\*Checklist|\n\n|$)", content, re.DOTALL)
    if summaries:
        unique_summaries = set(s.strip()[:100] for s in summaries)  # First 100 chars
        if len(unique_summaries) < len(summaries) / 2 and len(summaries) > 2:
            result.warnings.append(
                f"FABRICATION INDICATOR: Multiple agent responses appear identical ({len(summaries) - len(unique_summaries)} duplicates)"
            )

    # Check for suspicious patterns in checklist
    checklist_items = re.findall(r"\|\s*\d+\s*\|([^|]+)\|", content)
    if checklist_items:
        unique_items = set(item.strip()[:50] for item in checklist_items)
        if len(unique_items) < len(checklist_items) / 3 and len(checklist_items) > 5:
            result.warnings.append(
                "FABRICATION INDICATOR: Checklist items show low variety (possible copy-paste)"
            )

    # Check agent name consistency in sign-offs
    signoff_agents = re.findall(r"\|\s*([^|]+Agent[^|]*)\s*\|\s*(?:APPROVED|REJECTED|CONDITIONAL|N/A)\s*\|", content)
    for agent in signoff_agents:
        agent_clean = agent.strip()
        # Check for typos or fabricated agent names
        known_agents = REQUIRED_AGENTS + ["PM-Architect-Agent"]
        if agent_clean not in known_agents:
            # Allow partial matches for formatting variations
            found_match = any(known in agent_clean or agent_clean in known for known in known_agents)
            if not found_match:
                result.errors.append(
                    f"FABRICATION INDICATOR: Unknown agent '{agent_clean}' in sign-off"
                )


def check_sequential_consistency(content: str, result: ValidationResult) -> None:
    """
    P1-003: Check that gate follows logical sequence.

    Validates:
    1. Output gates should reference completed input gates
    2. Phase N output should come after Phase N input
    """
    gate_type_match = re.search(r"\*\*Gate Type\*\*:\s*(Input|Output)", content)
    phase_match = re.search(r"\*\*Phase\*\*:\s*(\d+)", content)
    stage_match = re.search(r"\*\*Stage\*\*:\s*(\d+)", content)

    if gate_type_match and phase_match and stage_match:
        gate_type = gate_type_match.group(1)
        phase = int(phase_match.group(1))
        stage = int(stage_match.group(1))

        if gate_type == "Output":
            # Check if corresponding input gate is referenced or exists
            input_ref = re.search(rf"phase{phase}-input-gate", content, re.IGNORECASE)
            input_gate_path = Path(f".claude-bus/gates/stage{stage}/phase{phase}-input-gate.md")

            if not input_ref and not input_gate_path.exists():
                result.warnings.append(
                    f"SEQUENCE WARNING: Phase {phase} Output gate has no corresponding Input gate"
                )


# =============================================================================
# P2-005: GIT CHECKPOINT VERIFICATION
# =============================================================================

def check_git_checkpoint(content: str, result: ValidationResult) -> None:
    """
    P2-005: Verify git checkpoint is referenced in Phase 2+ Output gates.

    Validates:
    1. Phase 2 Output gates should reference a git commit hash
    2. The commit hash should be valid format (7-40 hex chars)
    """
    import subprocess

    gate_type_match = re.search(r"\*\*Gate Type\*\*:\s*(Input|Output)", content)
    phase_match = re.search(r"\*\*Phase\*\*:\s*(\d+)", content)

    if not gate_type_match or not phase_match:
        return

    gate_type = gate_type_match.group(1)
    phase = int(phase_match.group(1))

    # Only check Phase 2+ Output gates
    if gate_type != "Output" or phase < 2:
        return

    # Look for git commit hash reference
    # Common patterns: "Commit:", "Git Checkpoint:", "Hash:", or raw commit hashes
    commit_patterns = [
        r"\*\*Git Checkpoint\*\*:\s*([a-f0-9]{7,40})",
        r"\*\*Commit\*\*:\s*([a-f0-9]{7,40})",
        r"commit[:\s]+([a-f0-9]{7,40})",
        r"\b([a-f0-9]{7,40})\s+Stage",  # "abc1234 Stage 5 Phase 2 Complete"
    ]

    commit_hash = None
    for pattern in commit_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            commit_hash = match.group(1)
            break

    if not commit_hash:
        result.warnings.append(
            f"P2-005: Phase {phase} Output gate should reference git checkpoint commit hash"
        )
        return

    # Validate the commit hash format
    if not re.match(r"^[a-f0-9]{7,40}$", commit_hash):
        result.warnings.append(
            f"P2-005: Invalid commit hash format: {commit_hash}"
        )
        return

    # Optionally verify commit exists (may fail in CI without full git history)
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-t", commit_hash],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode != 0:
            result.warnings.append(
                f"P2-005: Commit hash {commit_hash[:7]} not found in git history"
            )
        else:
            result.info.append(f"P2-005: Git checkpoint verified: {commit_hash[:7]}")
    except Exception:
        # Git not available or timeout - just note the hash exists in document
        result.info.append(f"P2-005: Git checkpoint referenced: {commit_hash[:7]}")
