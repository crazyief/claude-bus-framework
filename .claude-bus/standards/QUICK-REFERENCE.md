# Quick Reference - GPT-OSS Standards

**Version**: 1.6 | **Last Updated**: 2025-12-21

> This is a condensed summary. For detailed rules, load the full documentation when needed.

---

## ⚠️ 每次 Session 開始必做 (MANDATORY)

**PM-Architect 在每次新 session 必須：**

1. **讀取目前狀態**：`cat todo/PROJECT_STATUS.md | head -50`
2. **確認目前 Phase**：檢查 "Current Position" 區塊
3. **Phase 轉換前執行**：
   ```bash
   python3 .claude-bus/scripts/gate_workflow.py --stage {N} --phase {P} --type {input|output}
   ```

**不執行 gate_workflow.py 就開始工作 = 違反流程**

---

## 🚨 Gate Voting Rules (2025-12-14 Updated)

```
┌─────────────────────────────────────────────────────────────────┐
│ ❌ NO "CONDITIONAL PASS" - 只有 PASS 或 BLOCK                   │
│ ✅ UNANIMOUS REQUIRED - 任一 BLOCK = Gate 失敗                  │
│ ✅ MINIMUM 2 LOOPS - 強制兩輪驗證                               │
│ ✅ MAX 3 LOOPS - 超過則 escalate to User                        │
│ ✅ BLOCK = 必須附理由 + 修復建議                                │
│ ❌ PM 不可單方面 override BLOCK (G-008)                         │
│ ✅ 只有 blocker 本人可改票 + 需獨立 review (G-009, G-010)       │
└─────────────────────────────────────────────────────────────────┘
```

**流程**:
```
Loop N → 6 agents vote → Any BLOCK?
         ↓ All PASS        ↓ YES
Loop N+1              PM discusses with blocker
         ↓                  ↓
GATE PASSED ✅     Blocker maintains? → Fix or Escalate
                   Blocker changes? → Review → Loop N+1
```

**BLOCK Resolution (G-008 ~ G-015)**:
1. PM 與 blocker 討論 (Clarification Discussion)
2. Blocker 自己決定是否改票
3. 改票需獨立 review (Super-AI 或 QA-Agent)
4. Reviewer Selection: 若 Super-AI 是 blocker → QA-Agent + User 確認

**投票格式**: `✅ PASS` 或 `❌ BLOCK (reason: xxx, fix: yyy)`

**記錄位置**: `.claude-bus/gates/stage{N}/phase{P}-{input|output}-votes.json`

---

## Gate Protocol Terminology (Memorize These)

| 術語 | 定義 |
|------|------|
| **Input Gate** | Phase 開始前的關卡 |
| **Output Gate** | Phase 結束時的關卡 |
| **Gate Validation** | 6 agents 投票 Meeting |
| **PASS** | Agent 同意通過 (無條件) |
| **BLOCK** | Agent 不同意，必須附理由 |

**每個 Gate 需要 2 輪全員 PASS 才能通過**

```
Phase N:
  [Input Gate: 2 loops] → Work → [Output Gate: 2 loops] → Next Phase
      6 agents vote                  6 agents vote

每 Stage 最少會議次數：20 次（5 Phases × 2 Gates × 2 Loops）
紀錄存放：.claude-bus/gates/stage{N}/
```

---

## Phase Gates (Memorize These)

| Transition | Must Pass |
|------------|-----------|
| **Phase 2→3** | Git checkpoint exists |
| **Phase 3→4** | Coverage ≥70%, Tests pass, Pyramid OK, A11y pass |
| **Phase 4→5** | E2E pass, Performance OK (LCP ≤2.5s), Bundle ≤60KB |
| **Phase 5→Done** | User approval, Final git checkpoint |

---

## Testing Quick Rules

```
Pyramid: Unit 60% | Integration 20% | Component 10% | E2E 10%
Coverage: ALL stages ≥70%
E2E: MUST use REAL backend (no MSW mocks)
Selectors: Use data-testid from Phase 1 contracts (o8)
```

**Commands**:
```bash
npm run test              # Phase 3 (mocked)
npm run test:e2e          # Phase 4 (real backend required)
npm run test:a11y         # Accessibility
```

---

## Code Quality Quick Rules

| Rule | Limit |
|------|-------|
| File size | ≤400 lines (≤500 for .svelte) |
| Function size | ≤50 lines |
| Nesting depth | ≤3 levels |
| Comments | 15-20% (30% for RAG/algorithms) |

---

## Key Commands

```bash
# Services
docker-compose up -d          # Start all
docker-compose logs -f backend # View logs

# Tasks
ls .claude-bus/tasks/*.json   # Check tasks
tail -20 .claude-bus/events.jsonl # Recent activity

# Phase 4 prerequisite check
find frontend/node_modules/.vite -user root 2>/dev/null | head -1
```

---

## Agent Responsibilities

| Agent | Primary Focus |
|-------|---------------|
| PM-Architect | Planning, coordination, phase gates |
| Backend | FastAPI, SQLAlchemy, LLM service |
| Frontend | Svelte, stores, components |
| QA | Testing, code review, coverage |
| Document-RAG | Chunking, embedding, retrieval |
| Super-AI | Architecture review, complex problems |

---

## When to Load Full Docs

| Situation | Load This |
|-----------|-----------|
| Starting Phase 3 Review | `TESTING-RULES.md` |
| Writing new component | `PATTERN-LIBRARY.md` |
| During Phase 2 development | `CONTINUOUS-QUALITY.md` |
| Architecture decisions | `CODING-ARCHITECTURE-RULES.md` |
| Debugging test issues | `TESTING-STANDARDS.md` |

**Location**: `.claude-bus/standards/` and `docs/`

---

## Defense in Depth Scripts

| Script | When to Use |
|--------|-------------|
| `validate_gate.py` | Auto-run by pre-commit hook on gate records |
| `user_signoff.py` | **MANDATORY** for Output Gate Phase 2+ |
| `secure_events.py` | Log events with HMAC signatures |
| `agent_signature.py` | Sign agent responses |
| `super_ai_audit.py` | Independent audit (Phase transitions) |
| `monitor_runner.py` | Execute auto-monitoring rules (tech debt, service health) |
| `vote_watcher.py` | Real-time BLOCK vote monitoring (防止 PM override) |

**User Sign-off Command** (Output Gate Phase 2+):
```bash
python3 .claude-bus/scripts/user_signoff.py request --stage N --phase P --type output
# User must verify with token to proceed!
```

---

## Complete Scripts Inventory

### 核心工作流腳本

| Script | 用途 | 位置 |
|--------|------|------|
| `gate_workflow.py` | **統一入口 v2.0** - 整合所有 gate 驗證 | `.claude-bus/scripts/` |
| `gate_checklists.py` | Phase gate checklist 定義 | `.claude-bus/gates/checklists/` |

### 公用程式腳本

| Script | 用途 |
|--------|------|
| `session_resume.py` | 新 session context 重建 |
| `check_rules.py` | CLAUDE.md 規則合規檢查 |
| `check_hooks.py` | Pre-commit hooks 驗證 |
| `verify_coordination.py` | Multi-agent 協調驗證 |
| `create_handoff.py` | Session handoff 產生器 |
| `validate_handoff.py` | Handoff 檔案驗證 |
| `alert_manager.py` | Alert 建立/列出/解決 |

### 內部模組（由其他腳本 import）

| Module | 被誰使用 | 用途 |
|--------|----------|------|
| `gate_validators.py` | `validate_gate.py` | Gate 驗證邏輯 |
| `gate_config.py` | `validate_gate.py` | Gate 設定常數 |
| `gate_output.py` | `validate_gate.py` | Gate 輸出格式化 |

### 狀態追蹤檔案

| File | 用途 | 位置 |
|------|------|------|
| `events.jsonl` | 所有 agent 活動日誌 | `.claude-bus/` |
| `events-secure.jsonl` | HMAC 簽章的安全日誌 | `.claude-bus/` |
| `pm-state.json` | PM phase/stage 狀態追蹤 | `.claude-bus/` |

### Memory Service（位於 backend）

```bash
# 透過 docker exec 執行
docker exec gpt-oss-backend python scripts/memory_cli.py <command>
```

---

## Memory Service CLI (Bug 經驗查詢 + 記錄)

**遇到問題時先查詢！解決後必須記錄！**

```bash
# 搜尋 bug 解法 (FIRST: 先查有沒有人解過)
docker exec gpt-oss-backend python scripts/memory_cli.py search "YOUR_ERROR"
docker exec gpt-oss-backend python scripts/memory_cli.py search "test failure" --type solution

# 記錄 bug/root cause (MANDATORY: 解決後必須存)
docker exec gpt-oss-backend python scripts/memory_cli.py store \
  --agent YOUR_AGENT_ID \
  --type solution \
  --stage CURRENT_STAGE \
  --title "Short bug description" \
  --content "Problem: X. Root Cause: Y. Solution: Z." \
  --tags "tag1,tag2" \
  --files "path/to/file.py"

# 其他指令
docker exec gpt-oss-backend python scripts/memory_cli.py health
docker exec gpt-oss-backend python scripts/memory_cli.py list
```

**Types**: `solution` (bug fix), `lesson` (learned), `pattern` (reusable), `decision` (architecture)

---

## Critical Reminders

1. **E2E tests = Real backend** (never mock in E2E)
2. **Git checkpoint before Phase 3** (always)
3. **Coverage cannot decrease** (from previous commit)
4. **No console.log in production** (use proper logging)
5. **data-testid on all interactive elements** (for E2E)
6. **User Sign-off for Output Gate Phase 2+** (MANDATORY - breaks self-policing)
7. **遇到 bug 先查 Memory Service** (docker exec ... memory_cli.py search)
