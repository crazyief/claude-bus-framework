# Team Meeting Command

Invoke all 6 agents for a gate validation meeting.

## Usage
```
/team-meeting [topic]
```

## Examples
- `/team-meeting "Phase 2 Output Gate Review"`
- `/team-meeting "Architecture Decision: Database Choice"`

## Steps

1. **Prepare Meeting Context**
   - Read current PROJECT_STATUS.md
   - Identify the topic/gate being discussed
   - Gather relevant files and changes

2. **Invoke All 6 Agents in Parallel**
   Use Task tool to invoke:
   - PM-Architect-Agent
   - Backend-Agent
   - Frontend-Agent
   - QA-Agent
   - Document-RAG-Agent
   - Super-AI-UltraThink-Agent

3. **Collect Votes**
   Each agent provides:
   - Vote: PASS or BLOCK
   - If BLOCK: reason and fix suggestion

4. **Tally Results**
   - All PASS = Gate passes
   - Any BLOCK = Gate blocked, list issues

5. **Record Meeting**
   Save results to `.claude-bus/gates/stage{N}/`

## Meeting Protocol
- Binary voting only (PASS/BLOCK)
- Minimum 2 loops required
- All agents must participate
