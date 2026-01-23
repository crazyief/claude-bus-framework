# New Stage Command

Initialize a new development stage with proper structure.

## Usage
```
/new-stage [number] "[description]"
```

## Examples
- `/new-stage 1 "Foundation - Core API and Database"`
- `/new-stage 2 "User Authentication and Sessions"`

## Steps

1. Create stage directory structure:
   ```
   .claude-bus/planning/stages/stage{N}/
   .claude-bus/gates/stage{N}/
   ```

2. Initialize phase checklists for all 5 phases

3. Update `todo/PROJECT_STATUS.md` with:
   - New stage entry
   - Current position: Stage N Phase 1

4. Create initial requirements document template

5. Notify user that stage is ready to begin

## Phase Structure Created
- Phase 1: Planning
- Phase 2: Development
- Phase 3: Review
- Phase 4: Integration
- Phase 5: Approval
