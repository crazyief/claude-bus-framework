#!/usr/bin/env python3
"""
Gate Validation Configuration - Defense in Depth Layer 3

Contains all configuration constants for gate validation.
Can be extended to load from YAML config file in future.

Author: PM-Architect-Agent
Created: 2025-12-14
"""

from dataclasses import dataclass, field
from typing import List


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

MIN_SUMMARY_LENGTH = 50  # Minimum characters for agent summaries
MAX_FILE_SIZE = 1_000_000  # 1 MB max file size

# Required agents for gate validation (G-001)
REQUIRED_AGENTS = [
    "Backend-Agent",
    "Frontend-Agent",
    "QA-Agent",
    "Document-RAG-Agent",
    "Super-AI-UltraThink-Agent",
    "frontend-debug-agent",
]

# Required sections in gate record (Layer 2 template)
REQUIRED_SECTIONS = [
    "Section 1: Agent Invocation Evidence",
    "Section 2: Agent Responses",
    "Section 3: Consolidated Checklist",
    "Section 4: Unresolved Issues",
    "Section 5: Sign-offs",
    "Section 6: Gate Decision",
    "Section 7: Validation",
]

# Valid status values
VALID_AGENT_STATUSES = ["OK", "CONCERN", "QUESTION", "STANDBY"]
VALID_GATE_DECISIONS = ["PASS", "FAIL", "CONDITIONAL"]
VALID_SIGNOFF_VALUES = ["APPROVED", "REJECTED", "CONDITIONAL", "N/A"]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ValidationResult:
    """Result of gate validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "valid": self.valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }
