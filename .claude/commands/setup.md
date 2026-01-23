# Setup Command

Interactive project setup for new Claude Bus projects.

## Usage
```
/setup
```

## Steps

1. **Gather Project Information**
   Ask user for:
   - Project name
   - Brief description (1-2 sentences)
   - Tech stack (e.g., FastAPI + Svelte, Django + React)
   - Project type (web app, API, CLI, library)

2. **Update CLAUDE.md**
   - Replace `{YOUR_PROJECT_NAME}` with actual name
   - Replace `{DESCRIBE YOUR PROJECT}` with description
   - Add tech stack specific guidance if needed

3. **Initialize PROJECT_STATUS.md**
   Create with:
   ```markdown
   # Project Status: {name}

   ## Current Position
   Stage: 1 | Phase: 1 (Planning)

   ## Progress
   - [ ] Stage 1: {first feature}

   ## Recent Updates
   - {date}: Project initialized
   ```

4. **Create Initial Gate Structure**
   - Create `.claude-bus/gates/stage1/` directory
   - Initialize empty events.jsonl

5. **Confirm Setup Complete**
   - Show summary of created files
   - Suggest next step: "Start planning Phase 1"

## Output
```
=== Project Setup Complete ===
Project: {name}
Type: {type}
Stack: {stack}

Files created:
- CLAUDE.md (updated)
- todo/PROJECT_STATUS.md
- .claude-bus/gates/stage1/

Next: Run /new-stage 1 "Your first feature"
```
