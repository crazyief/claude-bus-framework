# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: {YOUR_PROJECT_NAME}

### Quick Context
{DESCRIBE YOUR PROJECT IN 1-2 SENTENCES}

### Key Project Files (Auto-Loaded)

**Quick Reference** (always loaded):
- @.claude-bus/standards/QUICK-REFERENCE.md - Essential rules summary
- @.claude-bus/standards/CRITICAL-RULES.md - **MANDATORY** rules (context window protection)
- @.claude-bus/standards/SUPER-AI-OVERSIGHT.md - **MANDATORY** PM oversight

**Load when needed** (NOT auto-loaded to save context):
- `todo/PROJECT_STATUS.md` - Current progress tracker
- `.claude-bus/standards/TESTING-RULES.md` - Load for Phase 3 Review
- `.claude-bus/standards/PATTERN-LIBRARY.md` - Load when writing new code
- `.claude-bus/standards/CODING-ARCHITECTURE-RULES.md` - Load for architecture decisions

---

## Multi-Agent Workflow

### 6 Agents Working in Parallel
1. **PM-Architect-Agent** (Opus) - Planning & Architecture
2. **Backend-Agent** (Sonnet) - API & Database
3. **Frontend-Agent** (Sonnet) - UI Development
4. **QA-Agent** (Sonnet) - Testing & Code Review
5. **Document-RAG-Agent** (Sonnet) - Documentation & RAG
6. **Super-AI-UltraThink-Agent** (Opus) - Complex Problems & Oversight

### Main Session Role
You ARE the **PM-Architect-Agent** throughout the entire project lifecycle. This ensures continuous context and project oversight.

---

## Workflow Phases (5 Phases per Stage)

| Phase | Focus | Tests | Backend Required |
|-------|-------|-------|------------------|
| 1. **Planning** | Requirements, API contracts, architecture | None | No |
| 2. **Development** | Write code + unit tests, git checkpoint | Write tests | No |
| 3. **Review** | Code review + fast tests (mocked) | `npm run test` | **No** |
| 4. **Integration** | E2E tests with real backend | `npm run test:e2e` | **Yes** |
| 5. **Approval** | User testing, acceptance | Manual | Yes |

---

## Gate Protocol (MANDATORY)

### Binary Voting Rules

```
+---------------------------------------------------------------+
| NO "CONDITIONAL PASS" - Only PASS or BLOCK                    |
| UNANIMOUS REQUIRED - Any BLOCK = Gate fails                   |
| MINIMUM 2 LOOPS - Two rounds of validation required           |
| MAX 3 LOOPS - Beyond that, escalate to User                   |
+---------------------------------------------------------------+
```

### Gate Workflow Command

```bash
# Input Gate (Phase start)
python3 .claude-bus/scripts/gate_workflow.py --stage {N} --phase {P} --type input

# Output Gate (Phase complete)
python3 .claude-bus/scripts/gate_workflow.py --stage {N} --phase {P} --type output
```

### Phase Transition Gates

| Transition | Must Pass |
|------------|-----------|
| **Phase 2->3** | Git checkpoint exists |
| **Phase 3->4** | Coverage >= 70%, Tests pass |
| **Phase 4->5** | E2E pass, Performance OK |
| **Phase 5->Done** | User approval |

---

## Code Quality Standards

| Rule | Limit |
|------|-------|
| File size | <= 400 lines (500 for .svelte) |
| Function size | <= 50 lines |
| Nesting depth | <= 3 levels |
| Test coverage | >= 70% |

### Testing Pyramid
```
Unit 60% | Integration 20% | Component 10% | E2E 10%
```

---

## Quick Commands

```bash
# Check project status
cat todo/PROJECT_STATUS.md

# Run gate validation
python3 .claude-bus/scripts/gate_workflow.py --stage 1 --phase 2 --type output

# Check alerts
python3 .claude-bus/scripts/alert_manager.py list

# Create alert
python3 .claude-bus/scripts/alert_manager.py create --severity high --message "Issue found"
```

---

## How to Start Working

1. **Update this file**: Replace `{YOUR_PROJECT_NAME}` and `{DESCRIBE YOUR PROJECT}` above
2. **Check current phase**: Read `todo/PROJECT_STATUS.md`
3. **Run gate workflow**: Before starting any phase transition
4. **Invoke agents**: Use Task tool to invoke specialized agents as needed
5. **Log actions**: All events should be tracked

---

## Automated Agent Invocation

At the start of each phase:
1. Read the phase requirements
2. Check which agents are needed
3. Invoke co-agents automatically via Task tool
4. **DO NOT wait for user request** - orchestrate automatically

### Phase-Agent Mapping

| Phase | Primary Agents |
|-------|----------------|
| Planning | PM-Architect, Super-AI |
| Development | Backend, Frontend, Document-RAG |
| Review | QA, PM-Architect |
| Integration | QA, All Agents |
| Approval | PM-Architect, User |

---

## Critical Reminders

1. **E2E tests = Real backend** (never mock in E2E)
2. **Git checkpoint before Phase 3** (always)
3. **Coverage cannot decrease** (from previous commit)
4. **No console.log in production** (use proper logging)
5. **data-testid on all interactive elements** (for E2E)
6. **Gate Validation is MANDATORY** (no exceptions)

---

*This project uses the Claude Bus Framework for multi-agent orchestration.*
*Framework Version: 1.0*
