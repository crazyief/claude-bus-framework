# Gate Check Command

Run gate validation for the current phase transition.

## Usage
```
/gate-check [stage] [phase] [type]
```

## Examples
- `/gate-check 1 2 output` - Check Stage 1 Phase 2 output gate
- `/gate-check 2 3 input` - Check Stage 2 Phase 3 input gate

## Steps

1. Parse the stage, phase, and gate type from arguments
2. Run the gate workflow script:
   ```bash
   python3 .claude-bus/scripts/gate_workflow.py --stage {stage} --phase {phase} --type {type}
   ```
3. Report the results to the user
4. If BLOCKED, list the blocking issues and required fixes
5. If PASSED, confirm ready to proceed

## Gate Types
- **input** - Run before starting a phase
- **output** - Run after completing a phase
