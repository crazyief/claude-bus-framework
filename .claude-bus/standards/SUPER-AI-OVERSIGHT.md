# Super-AI Independent Oversight Protocol

**Version**: 1.0 | **Created**: 2025-12-14 | **Author**: PM-Architect-Agent

---

## Problem Statement

PM-Architect-Agent has a fundamental conflict of interest:
- PM enforces Gate Protocol rules
- PM also executes Gate Protocol
- PM can potentially skip/fabricate gates without external verification

**This is the "fox guarding the henhouse" problem.**

---

## Solution: Super-AI as Independent Auditor

Super-AI-UltraThink-Agent is designated as the **Independent Oversight Authority** with the following powers:

### 1. Mandatory Audit Triggers

Super-AI MUST be automatically invoked for audit in these situations:

| Trigger | Audit Scope |
|---------|-------------|
| **Phase Transition** | Verify gate records exist and are valid |
| **Stage Completion** | Full audit of all gates in that stage |
| **User Request** | Ad-hoc audit on demand |
| **Anomaly Detection** | Investigate suspicious patterns |

### 2. Super-AI Audit Powers

Super-AI has READ access to:
- All gate records (`.claude-bus/gates/`)
- PM state file (`pm-state.json`)
- Event log (`.claude-bus/events.jsonl`)
- Git history (via `git log`, `git diff`)
- All handoff documents

Super-AI MUST verify:
1. Gate records exist for claimed phase completions
2. Gate records pass validation (`validate_gate.py`)
3. pm-state.json matches gate records (no drift)
4. All 6 agents were actually invoked (check events.jsonl)
5. Sign-offs are present from appropriate agents

### 3. Audit Report Format

Super-AI generates audit report in `.claude-bus/audits/`:

```markdown
# Oversight Audit Report

**Audit ID**: AUDIT-2025-12-14-001
**Auditor**: Super-AI-UltraThink-Agent
**Scope**: Stage 5 Phase 2 → Phase 3 Transition

## Verification Results

| Check | Status | Evidence |
|-------|--------|----------|
| Gate record exists | ✅ PASS | phase2-output-gate.md |
| Gate validation passes | ✅ PASS | Exit code 0 |
| pm-state.json consistent | ✅ PASS | phase_status: "completed" |
| 6 agents invoked | ⚠️ WARN | Only 5 agents found in events.jsonl |
| Sign-offs complete | ✅ PASS | All 6 sign-offs present |

## Findings

- ⚠️ WARNING: frontend-debug-agent invocation not found in events.jsonl
  - Recommendation: Verify agent was invoked via other means

## Audit Decision

**APPROVED** with minor finding

---
*Audit timestamp: 2025-12-14T03:00:00Z*
*This audit is independent of PM-Architect-Agent*
```

### 4. Escalation Protocol

If Super-AI finds violations:

| Severity | Action |
|----------|--------|
| **CRITICAL** | Block transition, notify user immediately |
| **HIGH** | Block transition, require PM explanation |
| **MEDIUM** | Allow transition with warning, log for review |
| **LOW** | Log only, no action required |

### 5. Integration with Gate Protocol

Modify Gate Validation workflow:

```
Standard Flow:
[PM triggers Gate] → [6 agents respond] → [PM records result] → [Proceed]

With Super-AI Oversight:
[PM triggers Gate] → [6 agents respond] → [PM records result]
                                                    ↓
                                         [Super-AI Audit]
                                                    ↓
                                         [Proceed if APPROVED]
```

### 5.1 BLOCK Resolution Protocol (2025-12-14 新增)

**當有 BLOCK 時，Super-AI 的角色取決於誰是 blocker：**

```
Reviewer Selection Matrix:
┌─────────────────────────────────┬──────────────────────────────────┐
│ Blocker                         │ Reviewer                         │
├─────────────────────────────────┼──────────────────────────────────┤
│ 其他 Agent (非 Super-AI)        │ Super-AI-UltraThink-Agent        │
│ Super-AI-UltraThink-Agent       │ QA-Agent + User 確認 (避免自審)  │
│ PM-Architect-Agent              │ Super-AI + User 確認             │
│ Super-AI + 其他 Agents          │ Super-AI 審其他; QA 審 Super-AI  │
└─────────────────────────────────┴──────────────────────────────────┘
```

**Super-AI 作為 Reviewer 的職責：**

1. 驗證 Clarification Discussion 真的發生
2. 確認 Blocker 改票是自願的、非被迫的
3. 評估改票理由是否合理
4. 決定：APPROVE (改票有效) 或 REJECT (維持原 BLOCK)

**Super-AI 作為 Blocker 時：**

- 由 QA-Agent 擔任 Reviewer（避免利益衝突）
- 必須額外取得 User 確認
- 這確保 "fox guarding the henhouse" 問題不會發生

### 6. Implementation

Add to pm-state.json:
```json
{
  "oversight": {
    "last_audit": "2025-12-14T03:00:00Z",
    "audit_id": "AUDIT-2025-12-14-001",
    "status": "APPROVED"
  }
}
```

### 7. Audit Frequency

| Phase Transition | Mandatory Audit |
|------------------|-----------------|
| Phase 1 → 2 | No (low risk) |
| Phase 2 → 3 | **YES** (code checkpoint) |
| Phase 3 → 4 | **YES** (QA approval) |
| Phase 4 → 5 | **YES** (E2E complete) |
| Phase 5 → Done | **YES** (stage complete) |

---

## Why This Works

1. **Separation of Concerns**: PM executes, Super-AI verifies
2. **Independent Authority**: Super-AI has no stake in PM's decisions
3. **Audit Trail**: All audits are logged and timestamped
4. **Escalation Path**: Violations are surfaced to user
5. **Automation**: Audits are triggered automatically, not manually

---

## Enforcement

This oversight protocol is MANDATORY for all phase transitions marked "YES" above.

PM-Architect-Agent MUST:
1. Invoke Super-AI after completing gate record
2. Wait for audit result before proceeding
3. Address any findings before transition

Failure to invoke Super-AI audit is itself a violation that will be detected in subsequent audits.

---

*This protocol addresses Vulnerability V-001 (Self-policing architecture)*
