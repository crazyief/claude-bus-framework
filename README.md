# Claude Bus Framework

A multi-agent orchestration framework for Claude Code CLI. Provides structured workflow, quality gates, and team coordination for software projects.

## Quick Start

### Option 1: GitHub Template (Recommended)

```bash
# Create new project from template
gh repo create my-project --template yourname/claude-bus-framework --private
cd my-project

# Start Claude Code
claude

# Run setup
/setup
```

### Option 2: Clone Directly

```bash
# Clone the framework
git clone https://github.com/yourname/claude-bus-framework my-project
cd my-project
rm -rf .git && git init

# Start Claude Code
claude

# Run setup
/setup
```

## What You Get

When you run `claude` in a project with this framework, you automatically have:

### 6 Specialized Agents
| Agent | Focus |
|-------|-------|
| PM-Architect | Planning, coordination, phase gates |
| Backend | API, database, services |
| Frontend | UI, components, stores |
| QA | Testing, code review, coverage |
| Document-RAG | Documentation, RAG pipelines |
| Super-AI | Complex problems, architecture review |

### 5-Phase Workflow
1. **Planning** - Requirements, contracts, architecture
2. **Development** - Write code + unit tests
3. **Review** - Code review + mocked tests
4. **Integration** - E2E tests with real backend
5. **Approval** - User testing, acceptance

### Quality Gates
- Binary voting (PASS/BLOCK only)
- Minimum 2 validation loops
- Unanimous agreement required
- Automatic escalation on blocks

### Slash Commands
| Command | Description |
|---------|-------------|
| `/setup` | Interactive project configuration |
| `/status` | Show current progress and alerts |
| `/gate-check` | Run gate validation |
| `/new-stage` | Initialize a new development stage |
| `/team-meeting` | Invoke all 6 agents for review |

## Directory Structure

```
your-project/
├── CLAUDE.md                    # Auto-loaded instructions
├── .claude/
│   ├── agents/                  # 6 agent definitions
│   │   ├── PM-Architect-Agent.md
│   │   ├── Backend-Agent.md
│   │   ├── Frontend-Agent.md
│   │   ├── QA-Agent.md
│   │   ├── Document-RAG-Agent.md
│   │   └── Super-AI-UltraThink-Agent.md
│   └── commands/                # Slash commands
│       ├── setup.md
│       ├── status.md
│       ├── gate-check.md
│       ├── new-stage.md
│       └── team-meeting.md
├── .claude-bus/
│   ├── standards/               # Coding standards & rules
│   ├── scripts/                 # Automation scripts
│   ├── gates/                   # Gate records
│   ├── planning/                # Requirements & architecture
│   └── contracts/               # API contracts
└── todo/
    └── PROJECT_STATUS.md        # Progress tracker
```

## Workflow Example

```bash
# 1. Start Claude Code
claude

# 2. Configure project
/setup
> Project name: My Awesome App
> Description: A task management application
> Tech stack: FastAPI + Svelte

# 3. Start first stage
/new-stage 1 "User Authentication"

# 4. Work through phases
# Claude (as PM-Architect) will:
# - Create requirements
# - Invoke development agents
# - Run gate validations
# - Coordinate testing

# 5. Check progress anytime
/status

# 6. Run gate checks
/gate-check 1 2 output
```

## Quality Standards

| Rule | Requirement |
|------|-------------|
| Test Coverage | >= 70% |
| File Size | <= 400 lines |
| Function Size | <= 50 lines |
| Nesting Depth | <= 3 levels |

### Test Pyramid
- Unit Tests: 60%
- Integration Tests: 20%
- Component Tests: 10%
- E2E Tests: 10%

## Gate Protocol

Every phase transition requires gate validation:

```
Phase N Output Gate:
  Loop 1: 6 agents vote (PASS/BLOCK)
  Loop 2: Re-validation (required)
  Result: All PASS = Continue, Any BLOCK = Fix first
```

### Gate Commands

```bash
# Check before starting Phase 3
python3 .claude-bus/scripts/gate_workflow.py --stage 1 --phase 3 --type input

# Check after completing Phase 2
python3 .claude-bus/scripts/gate_workflow.py --stage 1 --phase 2 --type output
```

## Customization

### Adding Custom Agents

Create new agent in `.claude/agents/MyAgent.md`:

```markdown
# My Custom Agent

## Role
Describe what this agent does.

## Responsibilities
- Task 1
- Task 2

## Tools
- Tool access list
```

### Adding Custom Commands

Create new command in `.claude/commands/my-command.md`:

```markdown
# My Command

## Usage
/my-command [args]

## Steps
1. What the command does
2. Step by step
```

## Requirements

- Claude Code CLI (`claude` command)
- Python 3.8+ (for gate scripts)
- Git

## License

MIT

---

*Built with Claude Bus Framework v1.0*
