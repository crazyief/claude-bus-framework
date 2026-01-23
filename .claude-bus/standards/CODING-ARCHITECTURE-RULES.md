# Coding & Architecture Rules for GPT-OSS Agents

**Version**: 2.1
**Effective Date**: 2025-12-08
**Status**: MANDATORY - Non-negotiable enforcement
**Last Updated**: 2025-12-08 (v2.1 - Added L2 Audit Logging, C19 File Upload Security, Phase Gate Sequencing)

---

## Core Philosophy: Simplicity First

**The best code is the code you don't have to debug at 2am.**

Every line of code should:
- ✅ Be necessary (no over-engineering)
- ✅ Be readable (future you will thank you)
- ✅ Be testable (if you can't test it, refactor it)
- ✅ Follow contracts (o3 API, o7 State, o8 UI, o9 Validation)

See `CLAUDE.md` for full project context.

---

## Quick Pre-Flight Checklist (Read Before Writing Any Code)

### Svelte Store Syntax (Most Common Bug)
```typescript
// ❌ WRONG - "set is not a function" error
$selectedProjectId.set(123)

// ✅ CORRECT - Use store object, not $ prefix
selectedProjectId.set(123)

// ✅ CORRECT - $ prefix is ONLY for reading in templates
{$selectedProjectId}
```

### File Size Check
```bash
# Before committing, verify file size
wc -l <file>
# *.ts/*.js/*.py: MAX 400 lines
# *.svelte: MAX 500 lines
# If over limit: MUST refactor before commit
```

### Contract Compliance
```typescript
// ❌ WRONG - Inventing API endpoint
fetch('/api/projects/get-all')

// ✅ CORRECT - Match o3 OpenAPI contract
fetch('/api/projects/')  // As defined in stage{N}-api-spec.yaml
```

### Database Selection
```typescript
// ❌ WRONG - Storing graph data in SQLite
db.execute("INSERT INTO relationships...")

// ✅ CORRECT - Use the right database
// SQLite: Projects, Conversations, Messages, Users (structured)
// Neo4j: Entity relationships, Knowledge graphs
// ChromaDB: Embeddings, Vector search
```

---

## Coding Rules

### Rule C1: File Size Limits (BLOCKING)

| File Type | Limit | Action if Exceeded |
|-----------|-------|-------------------|
| `*.svelte` | 500 lines | Extract components |
| `*.ts`/`*.js` | 400 lines | Extract modules |
| `*.py` | 400 lines | Extract functions/classes |
| `*.css`/`*.scss` | 600 lines | Extract partials |

**Enforcement**: QA-Agent BLOCKS Phase 3→4 if exceeded.

---

### Rule C2: Function/Method Size

| Metric | Limit |
|--------|-------|
| Lines per function | ≤ 50 |
| Cyclomatic complexity | ≤ 10 |
| Nesting depth | ≤ 3 levels |
| Parameters | ≤ 5 (use object for more) |

```python
# ❌ WRONG - Too nested
def process():
    if condition1:
        if condition2:
            if condition3:
                if condition4:  # 4 levels deep!
                    do_something()

# ✅ CORRECT - Early returns
def process():
    if not condition1: return
    if not condition2: return
    if not condition3: return
    if not condition4: return
    do_something()
```

---

### Rule C3: Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Python functions** | snake_case | `get_project_by_id()` |
| **Python classes** | PascalCase | `ProjectService` |
| **TypeScript functions** | camelCase | `getProjectById()` |
| **TypeScript interfaces** | PascalCase + I prefix | `IProject` or `Project` |
| **Svelte components** | PascalCase | `ChatMessage.svelte` |
| **CSS classes** | kebab-case | `.chat-message-container` |
| **Constants** | UPPER_SNAKE_CASE | `MAX_FILE_SIZE` |
| **data-testid** | kebab-case | `data-testid="send-button"` |

---

### Rule C4: Import Organization

```typescript
// 1. External packages (node_modules)
import { writable } from 'svelte/store';
import { onMount } from 'svelte';

// 2. Internal absolute imports ($lib)
import { apiClient } from '$lib/services/api';
import type { Project } from '$lib/types';

// 3. Relative imports (same feature)
import ChatMessage from './ChatMessage.svelte';
import { formatTimestamp } from './utils';

// Each group separated by blank line
```

---

### Rule C5: Error Handling Patterns

**Backend (Python/FastAPI)**:
```python
# ✅ CORRECT - Structured error response (match o9 contract)
from fastapi import HTTPException

raise HTTPException(
    status_code=400,
    detail={
        "error_code": "VALIDATION_ERROR",
        "message": "Project name is required",
        "field": "name"
    }
)
```

**Frontend (TypeScript)**:
```typescript
// ✅ CORRECT - Centralized error handling
try {
    const result = await apiClient.createProject(name);
    return result;
} catch (error) {
    if (error instanceof ApiError) {
        toastStore.error(error.message);
    } else {
        toastStore.error('An unexpected error occurred');
        console.error('Unhandled error:', error);
    }
    throw error;  // Re-throw for caller to handle
}
```

---

### Rule C6: No Console in Production

```typescript
// ❌ WRONG - console.log in production code
console.log('Debug:', data);

// ✅ CORRECT - Use logger or remove
import { logger } from '$lib/utils/logger';
logger.debug('Processing data', { data });

// ✅ ALSO CORRECT - In development only
if (import.meta.env.DEV) {
    console.log('Debug:', data);
}
```

**Enforcement**: QA-Agent flags as HIGH during Phase 3.

---

### Rule C7: TypeScript Strictness

```typescript
// ❌ WRONG - Using 'any'
function process(data: any) { ... }

// ✅ CORRECT - Use proper types
function process(data: ProjectCreateRequest) { ... }

// ❌ WRONG - Non-null assertion without check
const name = project!.name;

// ✅ CORRECT - Explicit null check
if (!project) throw new Error('Project not found');
const name = project.name;
```

**Required tsconfig settings**:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

---

### Rule C8: Async/Await Patterns

```python
# ❌ WRONG - Blocking call in async function
async def get_data():
    result = requests.get(url)  # BLOCKS event loop!
    return result

# ✅ CORRECT - Use async client
async def get_data():
    async with httpx.AsyncClient() as client:
        result = await client.get(url)
    return result
```

```typescript
// ❌ WRONG - Fire and forget
async function save() {
    apiClient.saveProject(data);  // No await!
}

// ✅ CORRECT - Await and handle errors
async function save() {
    try {
        await apiClient.saveProject(data);
    } catch (error) {
        handleError(error);
    }
}
```

---

### Rule C9: Svelte Reactivity Patterns

```svelte
<!-- ❌ WRONG - Mutating store value directly -->
<script>
    $projects.push(newProject);  // Won't trigger reactivity!
</script>

<!-- ✅ CORRECT - Create new reference -->
<script>
    $projects = [...$projects, newProject];
</script>

<!-- ❌ WRONG - Complex logic in template -->
{#if $projects.filter(p => p.status === 'active').length > 0}

<!-- ✅ CORRECT - Use reactive statement -->
<script>
    $: activeProjects = $projects.filter(p => p.status === 'active');
</script>
{#if activeProjects.length > 0}
```

---

### Rule C10: API Response Schema (Match o9)

All API responses MUST follow this structure:

**Success Response**:
```json
{
    "data": { ... },
    "meta": {
        "timestamp": "2025-12-08T10:00:00Z",
        "request_id": "uuid"
    }
}
```

**Error Response**:
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human readable message",
        "details": { ... }
    },
    "meta": {
        "timestamp": "2025-12-08T10:00:00Z",
        "request_id": "uuid"
    }
}
```

---

### Rule C11: Pydantic Schema Validation (Backend)

All FastAPI request/response MUST use Pydantic models:

```python
# ❌ WRONG - Manual dict validation
@app.post("/api/projects/create")
async def create_project(data: dict):
    if "name" not in data:
        raise HTTPException(400, "Name required")
    name = data["name"]

# ✅ CORRECT - Pydantic model validation
from pydantic import BaseModel, Field

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = Field(None, pattern=r'^[a-z-]+$')

class ProjectResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode

@app.post("/api/projects/create", response_model=ProjectResponse)
async def create_project(data: ProjectCreateRequest):
    # Pydantic auto-validates, raises 422 if invalid
    return project_service.create(data)
```

**Benefits**: Auto-validation, OpenAPI docs generation, type safety.

---

### Rule C12: FastAPI Dependency Injection

Use `Depends()` for service injection, NOT manual instantiation:

```python
# ❌ WRONG - Manual instantiation in route
@app.get("/api/projects/{id}")
async def get_project(id: int):
    db = SessionLocal()  # Manual!
    service = ProjectService(db)  # Manual!
    try:
        return service.get(id)
    finally:
        db.close()

# ✅ CORRECT - FastAPI Depends
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_project_service(db: Session = Depends(get_db)):
    return ProjectService(db)

@app.get("/api/projects/{id}")
async def get_project(
    id: int,
    service: ProjectService = Depends(get_project_service)
):
    return service.get(id)
```

**Benefits**: Automatic cleanup, testability (easy to mock), reusability.

---

### Rule C13: Accessibility Requirements (WCAG 2.1 AA)

All interactive UI elements MUST be accessible:

```svelte
<!-- ❌ WRONG - No accessibility -->
<div on:click={handleClick}>
    Click me
</div>

<!-- ✅ CORRECT - Keyboard accessible with ARIA -->
<button
    on:click={handleClick}
    on:keydown={(e) => e.key === 'Enter' && handleClick()}
    aria-label="Create new project"
    data-testid="create-project-btn"
>
    Click me
</button>
```

**Accessibility Checklist**:

| Requirement | Rule | Example |
|-------------|------|---------|
| **Keyboard Navigation** | All actions reachable via Tab/Enter/Space | `tabindex="0"` |
| **ARIA Labels** | All icons/buttons have labels | `aria-label="Close"` |
| **Focus Indicators** | Visible focus states | `:focus-visible` styling |
| **Color Contrast** | 4.5:1 for normal text, 3:1 for large | Use contrast checker |
| **Screen Reader** | Meaningful content order | Semantic HTML |
| **Form Labels** | All inputs have labels | `<label for="...">` |
| **Error Messages** | Linked to inputs | `aria-describedby` |

**Icon-Only Buttons**:
```svelte
<!-- ❌ WRONG - No label for screen readers -->
<button on:click={deleteProject}>
    <TrashIcon />
</button>

<!-- ✅ CORRECT - Accessible icon button -->
<button
    on:click={deleteProject}
    aria-label="Delete project"
    title="Delete project"
>
    <TrashIcon aria-hidden="true" />
</button>
```

**Form Accessibility**:
```svelte
<!-- ✅ CORRECT - Accessible form -->
<form on:submit|preventDefault={handleSubmit}>
    <label for="project-name">Project Name</label>
    <input
        id="project-name"
        name="name"
        type="text"
        required
        aria-required="true"
        aria-invalid={hasError}
        aria-describedby={hasError ? 'name-error' : undefined}
    />
    {#if hasError}
        <span id="name-error" role="alert">
            Name is required
        </span>
    {/if}
</form>
```

**Enforcement**: QA-Agent includes a11y checks in Phase 3 review.

> **See also**: Rule 15 (A11y Testing) in `TESTING-RULES.md` for test templates and checklist.

---

### Rule C14: Documentation Standards

**Philosophy**: Document the WHY, not the WHAT. Clean code with good naming is self-documenting for the WHAT; comments explain the WHY.

---

#### Quantity Thresholds (Floor)

| File Type | Minimum | WARN | BLOCK | Notes |
|-----------|---------|------|-------|-------|
| `*.py` | **20%** | <20% | <10% | Docstrings + inline |
| `*.ts` | **15%** | <15% | <10% | JSDoc + inline |
| `*.svelte` | **15%** | <15% | <10% | JSDoc + HTML comments |
| **RAG/Algorithm** | **30%** | <30% | <20% | Complex logic needs more explanation |

**What Counts as Documentation**:
- ✅ Docstrings (Python) / JSDoc (TypeScript)
- ✅ Inline comments explaining WHY
- ✅ Module/file header comments
- ✅ HTML comments for layout structure (Svelte)
- ❌ Commented-out code (tech debt, not docs)
- ❌ Obvious comments (`// increment counter`)

**Quick Measurement**:
```bash
# Python: (comments + docstrings) / total lines
grep -cE '^\s*#|^\s*"""' file.py

# TypeScript: (comments) / total lines
grep -cE '^\s*//|^\s*/\*|\*/' file.ts
```

---

#### Required Documentation (Quality)

| Element | Requirement | Example |
|---------|-------------|---------|
| **Module/File** | Purpose docstring at top | `"""Project service - handles CRUD operations."""` |
| **Public Functions** | JSDoc/docstring with params & returns | Google style for Python, JSDoc for TS |
| **Exported Components** | Props and events documented | `/** @prop {string} name - Project name */` |
| **Complex Logic** | Inline comment explaining WHY | `// Use binary search because list is sorted` |
| **Non-obvious Business Rules** | Explain the reasoning | `// CSRF exempt: public endpoint per security review` |
| **Svelte Reactivity** | Explain complex reactive statements | `// $: recalculate when deps change` |
| **TODO/FIXME** | Include ticket reference | `// TODO(#123): Add retry logic` |
| **Magic Numbers/Regex** | Explain the value | `// 1200 = LightRAG default chunk size` |

---

#### Forbidden Patterns

| Anti-pattern | Example | Why Bad |
|--------------|---------|---------|
| Obvious comments | `// increment counter` | Adds noise, no value |
| Commented-out code | `// old_function()` | Use git history instead |
| Outdated comments | Comment says X, code does Y | Worse than no comment |
| Redundant type comments | `// string` next to `: string` | TypeScript already documents this |
| Journal comments | `// Added by John on 2024-01-01` | Use git blame |

---

#### Enforcement

**Phase 3 QA Checks**:

| Check | Method | Severity |
|-------|--------|----------|
| Quantity threshold | Line count measurement | **BLOCK** if below BLOCK threshold |
| Public API docs | Scan for missing JSDoc/docstring | **HIGH** |
| Complex logic explanation | Review cyclomatic complexity >5 | **HIGH** |
| Forbidden patterns | Grep for anti-patterns | **MEDIUM** |
| TODO without ticket | Grep for bare TODO/FIXME | **LOW** |

**Automated Check Script**:
```bash
#!/bin/bash
# Check documentation coverage (approximate)

check_doc_coverage() {
    file=$1
    threshold=$2

    total=$(wc -l < "$file")
    comments=$(grep -cE '^\s*(#|//|/\*|\*|""")' "$file" 2>/dev/null || echo 0)

    if [ "$total" -gt 0 ]; then
        coverage=$((comments * 100 / total))
        if [ "$coverage" -lt "$threshold" ]; then
            echo "⚠️ $file: ${coverage}% < ${threshold}% minimum"
            return 1
        fi
    fi
    return 0
}

# Usage: check_doc_coverage "file.py" 20
```

---

## Architecture Rules

### Rule A1: Layered Architecture

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│   (Svelte Components, API Routes)       │
├─────────────────────────────────────────┤
│            Service Layer                │
│   (Business Logic, Orchestration)       │
├─────────────────────────────────────────┤
│          Repository Layer               │
│   (Data Access, Database Operations)    │
├─────────────────────────────────────────┤
│             Data Layer                  │
│   (SQLite, Neo4j, ChromaDB)            │
└─────────────────────────────────────────┘
```

**Rules**:
- ❌ Components CANNOT access database directly
- ❌ API routes CANNOT contain business logic
- ✅ Services orchestrate repository calls
- ✅ Repositories handle single data source

---

### Rule A2: Database Selection Matrix

| Data Type | Database | Example |
|-----------|----------|---------|
| Structured entities | **SQLite** | Projects, Conversations, Messages, Users |
| Relationships/Graphs | **Neo4j** | Entity relations, Knowledge graphs |
| Vector embeddings | **ChromaDB** | Document chunks, Semantic search |
| Binary files | **File System** | Uploaded PDFs, images |

**Enforcement**: QA-Agent reviews database usage in Phase 3.

---

### Rule A3: Contract Compliance

All implementations MUST match Phase 1 contracts:

| Contract | File | Validates |
|----------|------|-----------|
| o3 API | `stage{N}-api-spec.yaml` | Endpoints, methods, schemas |
| o7 State | `stage{N}-state-contracts.ts` | Store interfaces, naming |
| o8 UI | `stage{N}-ui-selectors.ts` | data-testid attributes |
| o9 Validation | `stage{N}-validation-rules.json` | Field constraints, errors |

```typescript
// ❌ WRONG - Endpoint not in contract
POST /api/projects/create-new

// ✅ CORRECT - Matches o3 contract
POST /api/projects/create
```

**Enforcement**: BLOCKS Phase 2→3 if contract violated.

---

### Rule A4: State Management Boundaries

```
┌─────────────────────────────────────────┐
│              Global Stores              │
│  (projects, conversations, user, theme) │
│  Location: $lib/stores/                 │
│  Scope: App-wide, persisted            │
├─────────────────────────────────────────┤
│            Feature Stores               │
│  (chatMessages, documentList)          │
│  Location: $lib/features/{name}/       │
│  Scope: Feature-specific               │
├─────────────────────────────────────────┤
│           Component State               │
│  (isLoading, formData, isOpen)         │
│  Location: Component script            │
│  Scope: Component-only                 │
└─────────────────────────────────────────┘
```

**Decision Tree**:
1. Is it shared across routes? → Global Store
2. Is it shared within a feature? → Feature Store
3. Is it only for this component? → Local State

---

### Rule A5: API Client Structure

```
$lib/services/api/
├── base.ts           # Fetch wrapper, CSRF, error handling
├── projects.ts       # Project CRUD operations
├── conversations.ts  # Conversation operations
├── chat.ts           # Chat/SSE streaming
├── documents.ts      # Document upload/management
└── index.ts          # Re-exports all modules
```

**Rules**:
- ✅ All API calls go through `base.ts` wrapper
- ✅ CSRF token handling centralized in `base.ts`
- ✅ Error transformation centralized in `base.ts`
- ❌ No direct `fetch()` calls in components

---

### Rule A6: Component Composition

```svelte
<!-- ❌ WRONG - God component -->
<ChatInterface>
    <!-- 800 lines of everything -->
</ChatInterface>

<!-- ✅ CORRECT - Composed components -->
<ChatInterface>
    <ChatHeader {project} />
    <MessageList {messages} />
    <ChatInput on:send={handleSend} />
</ChatInterface>

<!-- Each sub-component: ≤200 lines, single responsibility -->
```

---

### Rule A7: Dependency Injection

```python
# ❌ WRONG - Hardcoded dependency
class ProjectService:
    def __init__(self):
        self.db = SQLiteDatabase("./data/gpt_oss.db")

# ✅ CORRECT - Injected dependency
class ProjectService:
    def __init__(self, db: Database):
        self.db = db

# In main.py
db = get_database_from_config()
project_service = ProjectService(db)
```

**Benefits**: Testability, configurability, flexibility.

---

### Rule A8: SSE/WebSocket Patterns

```typescript
// ✅ CORRECT SSE Client Pattern
class SSEClient {
    private eventSource: EventSource | null = null;

    connect(url: string, handlers: SSEHandlers): void {
        this.eventSource = new EventSource(url);
        this.eventSource.onmessage = handlers.onMessage;
        this.eventSource.onerror = handlers.onError;
    }

    disconnect(): void {
        this.eventSource?.close();
        this.eventSource = null;
    }
}

// ✅ CORRECT - Always cleanup on component destroy
onDestroy(() => {
    sseClient.disconnect();
});
```

---

### Rule A9: Co-location Principle

```
src/lib/features/chat/
├── ChatInterface.svelte    # Main component
├── ChatMessage.svelte      # Sub-component
├── chat.store.ts           # Feature store
├── chat.service.ts         # Feature service
├── chat.types.ts           # Feature types
├── chat.test.ts            # Unit tests
└── index.ts                # Public exports
```

**Rules**:
- ✅ Tests co-located with source
- ✅ Types co-located with usage
- ✅ Services co-located with features
- ❌ No global `types/` folder with everything

---

### Rule A10: Migration Protocol

**Database Migrations**:
```bash
# ❌ WRONG - Edit existing migration
migrations/001_create_projects.sql  # Modified!

# ✅ CORRECT - Create new migration
migrations/001_create_projects.sql   # Untouched
migrations/002_add_project_icon.sql  # New migration
```

**API Changes**:
- ❌ Breaking changes without version bump
- ✅ Add new endpoint, deprecate old
- ✅ Document in CHANGELOG.md

---

## Phase Gates & Enforcement

### Document Responsibility Matrix

> **QA-Agent raised**: Which document governs which phase? This section clarifies.

| Phase Transition | Primary Document | Secondary Document | Enforcer |
|------------------|------------------|-------------------|----------|
| **Phase 1 → 2** | CLAUDE.md (contracts) | - | PM-Architect |
| **Phase 2 → 3** | **CODING-ARCHITECTURE-RULES.md** | - | QA-Agent |
| **Phase 3 → 4** | **TESTING-RULES.md** + **CODING-ARCHITECTURE-RULES.md** | - | QA-Agent |
| **Phase 4 → 5** | TESTING-RULES.md | - | QA-Agent |
| **Phase 5 → Done** | Manual approval | - | User |

**How Documents Interact**:

```
Phase 2 (Development)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2 → 3 Gate: CODING-ARCHITECTURE-RULES.md              │
│ ─────────────────────────────────────────────────────────── │
│ ✓ File size limits (C1)                                     │
│ ✓ Contract compliance (A3)                                  │
│ ✓ TypeScript strictness (C7)                                │
│ ✓ No console.log (C6)                                       │
│ ✓ Pydantic validation (C11)                                 │
│ ✓ Accessibility basics (C13)                                │
│ ✓ Security rules (S1-S8)                                    │
│ ✓ Audit logging (L2)                                        │
│ ✓ File upload security (C19)                                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Phase 3 (QA Review - Mocked Tests)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3 → 4 Gate: BOTH Documents                            │
│ ─────────────────────────────────────────────────────────── │
│ From CODING-ARCHITECTURE-RULES.md:                          │
│ ✓ Layered architecture (A1)                                 │
│ ✓ Database selection (A2)                                   │
│ ✓ API response schema (C10)                                 │
│ ✓ Error handling (C5)                                       │
│ ✓ RAG configuration (R1-R9)                                 │
│                                                             │
│ From TESTING-RULES.md:                                      │
│ ✓ Coverage ≥ 70%                                            │
│ ✓ Test pyramid compliant (60% unit, 20% integration, etc.)  │
│ ✓ Regression tests pass (Stage 2+)                          │
│ ✓ Permission check passed (no root-owned cache)             │
│ ✓ A11y E2E tests pass (WCAG scan) ← NEW                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Phase 4 (Integration Testing - Real Backend)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4 → 5 Gate: TESTING-RULES.md                          │
│ ─────────────────────────────────────────────────────────── │
│ ✓ All E2E tests passing                                     │
│ ✓ Visual regression passing                                 │
│ ✓ Performance tests passing (LCP ≤ 2.5s, etc.)              │
│ ✓ A11y E2E scan passing (axe-core)                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Phase 5 (Manual Approval)
```

**Quick Decision Guide**:

| Question | Answer |
|----------|--------|
| "Is my code structured correctly?" | Check CODING-ARCHITECTURE-RULES.md |
| "Are my tests sufficient?" | Check TESTING-RULES.md |
| "What blocks Phase 2→3?" | CODING-ARCHITECTURE-RULES.md only |
| "What blocks Phase 3→4?" | BOTH documents |
| "What blocks Phase 4→5?" | TESTING-RULES.md only |

---

### Phase 2 → Phase 3 (Code Review)

**Governing Document**: CODING-ARCHITECTURE-RULES.md

| Check | Rule | Severity |
|-------|------|----------|
| File size | C1 | CRITICAL |
| Contract compliance | A3 | CRITICAL |
| TypeScript strict | C7 | HIGH |
| No console.log | C6 | HIGH |
| Pydantic validation | C11 | HIGH |
| FastAPI Depends | C12 | MEDIUM |
| Accessibility | C13 | HIGH |
| Documentation | C14 | MEDIUM |
| Security rules | S1-S8 | CRITICAL |
| Audit logging | L2 | CRITICAL |
| File upload security | C19 | CRITICAL |
| Naming conventions | C3 | LOW |

### Phase 3 → Phase 4 (Integration)

**Governing Documents**: CODING-ARCHITECTURE-RULES.md + TESTING-RULES.md

**From CODING-ARCHITECTURE-RULES.md**:

| Check | Rule | Severity |
|-------|------|----------|
| Layered architecture | A1 | CRITICAL |
| Database selection | A2 | CRITICAL |
| API response schema | C10 | HIGH |
| Error handling | C5 | HIGH |
| RAG configuration | R1-R9 | HIGH |

**From TESTING-RULES.md**:

| Check | Rule | Severity |
|-------|------|----------|
| Coverage ≥ 70% | Rule 2 | CRITICAL |
| Test pyramid compliant | Rule 4 | HIGH |
| Regression tests pass | Rule 9 | CRITICAL |
| Permission check | Rule 11 | CRITICAL |
| **A11y E2E tests pass** | **NEW** | **HIGH** |

### Phase 4 → Phase 5 (Manual Approval)

**Governing Document**: TESTING-RULES.md

| Check | Rule | Severity |
|-------|------|----------|
| All E2E tests passing | Rule 10 | CRITICAL |
| Visual regression passing | Rule 6 | HIGH |
| Performance tests passing | Rule 5 | HIGH |
| A11y scan passing | NEW | HIGH |

---

## Enforcement Summary

| Rule | Severity | Gate | Action |
|------|----------|------|--------|
| File > 400/500 lines | CRITICAL | Phase 2→3 | BLOCK |
| Contract mismatch | CRITICAL | Phase 2→3 | BLOCK |
| Security (S1-S8) missing | CRITICAL | Phase 2→3 | BLOCK |
| Audit logging (L2) missing | CRITICAL | Phase 2→3 | BLOCK |
| File upload validation (C19) | CRITICAL | Phase 2→3 | BLOCK |
| Wrong database | CRITICAL | Phase 3→4 | BLOCK |
| Coverage < 70% | CRITICAL | Phase 3→4 | BLOCK |
| console.log in prod | HIGH | Phase 2→3 | Fix required |
| TypeScript `any` | HIGH | Phase 2→3 | Fix required |
| A11y violations | HIGH | Phase 3→4 | Fix required |
| Function > 50 lines | MEDIUM | Phase 2→3 | Refactor |
| Naming violation | LOW | Phase 2→3 | Warning |

---

## Quick Reference Commands

```bash
# Check file sizes
find frontend/src -name "*.svelte" -exec wc -l {} + | sort -n | tail -20
find frontend/src -name "*.ts" -exec wc -l {} + | sort -n | tail -20
find backend -name "*.py" -exec wc -l {} + | sort -n | tail -20

# TypeScript strict check
cd frontend && npx tsc --noEmit

# Lint check
cd frontend && npm run lint
cd backend && ruff check .

# Contract validation (manual)
# Compare implementation against .claude-bus/contracts/stage{N}-*.yaml
```

---

## RAG Pipeline Rules (LightRAG Best Practices)

> Based on [LightRAG](https://github.com/HKUDS/LightRAG) research and [RAG chunking best practices 2025](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025).

### Rule R1: Chunking Strategy

| Parameter | Recommended | Range | Notes |
|-----------|-------------|-------|-------|
| **Chunk Size** | 1200 tokens | 512-1500 | LightRAG default; larger for analytical queries |
| **Overlap** | 100 tokens | 50-200 | ~8-10% of chunk size |
| **Strategy** | Semantic | - | RecursiveCharacterTextSplitter as baseline |

```python
# ✅ CORRECT - LightRAG chunking config
from lightrag import LightRAG

rag = LightRAG(
    working_dir="./rag_data",
    chunk_token_size=1200,        # Default for LightRAG
    chunk_overlap_token_size=100,  # ~8% overlap
)

# For different query types:
# - Factoid queries (specific facts): 256-512 tokens
# - Analytical queries (complex analysis): 1024-1500 tokens
```

**Query-Type Chunking Guide**:
| Query Type | Optimal Chunk Size | Example |
|------------|-------------------|---------|
| Factoid | 256-512 tokens | "What is IEC 62443-4-2 CR 2.11?" |
| Analytical | 1024-1500 tokens | "Compare security requirements across standards" |
| Mixed | 1200 tokens (default) | General usage |

---

### Rule R2: Embedding Configuration

| Parameter | Recommended | Notes |
|-----------|-------------|-------|
| **Model** | `BAAI/bge-m3` or `text-embedding-3-large` | Multilingual support |
| **Dimension** | 384 or 768 | NEVER mix dimensions |
| **Batch Size** | ≤100 chunks | Memory management |

```python
# ✅ CORRECT - Embedding configuration
from lightrag import LightRAG
from lightrag.llm import openai_embedding

rag = LightRAG(
    working_dir="./rag_data",
    embedding_func=openai_embedding,
    embedding_dim=1536,  # text-embedding-3-large
    embedding_batch_num=32,  # Batch size
    embedding_func_max_async=16,  # Concurrency
)
```

**CRITICAL**:
- ⚠️ Embedding model MUST remain consistent after indexing
- ⚠️ Changing model requires deleting existing vector tables
- ⚠️ Never mix 384-dim and 768-dim embeddings in same collection

---

### Rule R3: Retrieval Mode Selection

LightRAG supports 6 query modes:

| Mode | Use Case | Performance |
|------|----------|-------------|
| **local** | Entity-specific queries | Fast, precise |
| **global** | Broad topic queries | Uses knowledge graph |
| **hybrid** | General queries | Balanced (recommended default) |
| **naive** | Simple keyword search | Baseline, no graph |
| **mix** | Knowledge graph + vector | Best accuracy, slower |
| **bypass** | Direct LLM (no retrieval) | When context known |

```python
# ✅ CORRECT - Query mode usage
# For specific entity lookup
result = rag.query("What is CR 2.11?", param=QueryParam(mode="local"))

# For cross-document analysis
result = rag.query("How do IEC 62443 and ETSI EN 303 645 compare?",
                   param=QueryParam(mode="global"))

# For general queries (default)
result = rag.query("Explain authentication requirements",
                   param=QueryParam(mode="hybrid"))

# With reranker (recommended for production)
result = rag.query(query, param=QueryParam(mode="mix"))
```

---

### Rule R4: Token Budget Management

| Parameter | Default | Max | Purpose |
|-----------|---------|-----|---------|
| `max_total_tokens` | 30,000 | - | Total context budget |
| `max_entity_tokens` | 6,000 | - | Entity descriptions |
| `max_relation_tokens` | 8,000 | - | Relationship data |

```python
# ✅ CORRECT - Token budget configuration
rag = LightRAG(
    working_dir="./rag_data",
    llm_model_max_token_size=32768,  # LLM context window
    llm_model_max_async=4,           # Concurrent LLM calls
)
```

**LLM Requirements for LightRAG**:
- Minimum: 32B parameters, 32K context
- Recommended: 64B+ parameters, 64K context
- Use stronger model for query than indexing

---

### Rule R5: Graph Storage Selection

| Storage | Use Case | Performance |
|---------|----------|-------------|
| **NetworkXStorage** | Development, small datasets | Simple, in-memory |
| **Neo4JStorage** | Production, large graphs | Best performance |
| **PGGraphStorage** | PostgreSQL ecosystem | Good alternative |

```python
# ✅ CORRECT - Production graph storage
from lightrag.kg.neo4j_impl import Neo4JStorage

rag = LightRAG(
    working_dir="./rag_data",
    graph_storage=Neo4JStorage,
    kg_neo4j_url="bolt://localhost:7687",
    kg_neo4j_user="neo4j",
    kg_neo4j_password="password123",
)
```

---

### Rule R6: Vector Storage Selection

| Storage | Use Case | Notes |
|---------|----------|-------|
| **ChromaVectorDBStorage** | Default, good performance | Our current choice |
| **MilvusVectorDBStorage** | Large scale (billions) | Enterprise |
| **FaissVectorDBStorage** | Local, fast | No persistence |
| **PGVectorStorage** | PostgreSQL unified | All-in-one |

```python
# ✅ CORRECT - ChromaDB configuration (our setup)
from lightrag.storage import ChromaVectorDBStorage

rag = LightRAG(
    working_dir="./rag_data",
    vector_storage=ChromaVectorDBStorage,
    vector_db_storage_cls_kwargs={
        "host": "localhost",
        "port": 8001,
    },
)
```

---

### Rule R7: Reranking Configuration

Enable reranking for improved retrieval accuracy:

```python
# ✅ CORRECT - Reranker configuration
rag = LightRAG(
    working_dir="./rag_data",
    reranker_model="BAAI/bge-reranker-v2-m3",
    reranker_enabled=True,
)

# Query with reranking (mix mode recommended)
result = rag.query(
    "What security controls are required?",
    param=QueryParam(mode="mix")
)
```

**Reranking Guidelines**:
- ✅ Enable for production (improves accuracy 10-20%)
- ⚠️ Adds latency (~200-500ms per query)
- ✅ Use `mix` mode when reranker is enabled

---

### Rule R8: Document Processing Quality

| Document Type | Processing | Quality Check |
|---------------|------------|---------------|
| **PDF (clean)** | Direct extraction | Verify text accuracy |
| **PDF (scanned)** | OCR required | ≥95% accuracy for clean scans |
| **Word/Excel** | Library extraction | Check formatting |
| **Images** | OCR | Review output |

```python
# ✅ CORRECT - Document processing with quality check
async def process_document(file_path: str) -> ProcessingResult:
    # Extract text
    text = await extract_text(file_path)

    # Quality checks
    if len(text.strip()) < 100:
        raise ProcessingError("Insufficient text extracted")

    # Check for OCR garbage (common patterns)
    garbage_ratio = count_garbage_chars(text) / len(text)
    if garbage_ratio > 0.1:  # >10% garbage
        raise ProcessingError("OCR quality too low")

    return ProcessingResult(text=text, quality_score=1.0 - garbage_ratio)
```

---

### Rule R9: Retrieval Thresholds

| Parameter | Recommended | Purpose |
|-----------|-------------|---------|
| **top_k** | 10-20 | Number of chunks to retrieve |
| **similarity_threshold** | 0.7 | Minimum similarity score |
| **max_context_chunks** | 5-10 | Chunks sent to LLM |

```python
# ✅ CORRECT - Retrieval configuration
result = rag.query(
    query_text,
    param=QueryParam(
        mode="hybrid",
        top_k=15,  # Retrieve 15 candidates
        # Reranker will select best 5-10 for context
    )
)
```

**"I Cannot Answer" Protocol**:
```python
# ✅ CORRECT - Insufficient data handling
if not result.chunks or all(c.score < 0.7 for c in result.chunks):
    return {
        "answer": "I cannot answer this question because the data is insufficient.",
        "confidence": 0.0,
        "reason": "No relevant documents found above similarity threshold"
    }
```

---

### RAG Phase Gates

| Phase | Check | Severity |
|-------|-------|----------|
| Phase 2→3 | Chunking config matches R1 | HIGH |
| Phase 2→3 | Embedding dimension consistent (R2) | CRITICAL |
| Phase 3→4 | Retrieval mode appropriate (R3) | MEDIUM |
| Phase 3→4 | Quality checks implemented (R8) | HIGH |

---

## Security Rules

> **CRITICAL**: Security rules are non-negotiable. Violations block deployment.

### Rule S1: Secrets Management (CRITICAL)

**Never expose secrets in code, logs, or version control.**

```python
# ✅ CORRECT - Use Pydantic BaseSettings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    neo4j_password: str
    openai_api_key: str
    database_url: str

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# ✅ CORRECT - Access via settings object
api_key = settings.openai_api_key
```

```typescript
// ✅ CORRECT - Vite environment variables
const apiUrl = import.meta.env.VITE_API_URL;

// ❌ WRONG - Hardcoded secrets
const API_KEY = "sk-abc123...";  // NEVER!
```

**Requirements**:
- ✅ `.env` files MUST be in `.gitignore`
- ✅ Use `VITE_` prefix for frontend env vars (Vite requirement)
- ✅ Use Pydantic BaseSettings for backend config
- ❌ NEVER commit API keys, passwords, tokens
- ❌ NEVER log secrets (see S8)

**Enforcement**: Pre-commit hook scans for secrets patterns. BLOCKS commit.

---

### Rule S2: Input Validation (CRITICAL)

**Sanitize all user input to prevent XSS and injection attacks.**

**Backend (Pydantic)**:
```python
from pydantic import BaseModel, Field, field_validator
import re

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        # Strip whitespace, limit length
        v = v.strip()[:100]
        # Remove potential script tags
        v = re.sub(r'<[^>]*>', '', v)
        if not v:
            raise ValueError('Name cannot be empty')
        return v
```

**Frontend (DOMPurify for HTML)**:
```typescript
import DOMPurify from 'dompurify';

// ✅ CORRECT - Sanitize before rendering HTML
const safeHtml = DOMPurify.sanitize(userContent);

// ❌ WRONG - Direct HTML rendering
{@html userContent}  // XSS vulnerability!

// ✅ CORRECT - Sanitized HTML rendering
{@html DOMPurify.sanitize(userContent)}
```

**Database (SQLAlchemy ORM)**:
```python
# ✅ CORRECT - ORM prevents SQL injection
project = session.query(Project).filter(Project.id == project_id).first()

# ❌ WRONG - Raw SQL with string interpolation
session.execute(f"SELECT * FROM projects WHERE id = {project_id}")  # SQL INJECTION!

# ✅ CORRECT - Parameterized query if raw SQL needed
session.execute(text("SELECT * FROM projects WHERE id = :id"), {"id": project_id})
```

**Enforcement**: QA reviews all user input handling. BLOCKS Phase 3→4 if vulnerable.

---

### Rule S3: Rate Limiting (HIGH)

**Prevent API abuse through request throttling.**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Standard CRUD endpoints
@app.get("/api/projects/")
@limiter.limit("100/minute")
async def get_projects(request: Request):
    ...

# Resource-intensive LLM endpoints
@app.post("/api/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request):
    ...

# File upload endpoints
@app.post("/api/documents/upload")
@limiter.limit("20/minute")
async def upload_document(request: Request):
    ...
```

**Rate Limits**:
| Endpoint Type | Limit | Reason |
|---------------|-------|--------|
| CRUD (GET/POST/PUT/DELETE) | 100/min | Normal usage |
| LLM/Chat endpoints | 10/min | GPU resource intensive |
| File upload | 20/min | Storage/processing intensive |
| Auth endpoints | 5/min | Brute force prevention |

---

### Rule S4: Security Headers (HIGH)

**Configure HTTP headers to prevent common attacks.**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Specific origins only!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws://localhost:* http://localhost:*"
    )
    return response
```

**Required Headers**:
| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| X-XSS-Protection | 1; mode=block | XSS filter |
| Content-Security-Policy | (see above) | Script/resource control |
| Referrer-Policy | strict-origin-when-cross-origin | Limit referrer info |

---

### Rule S5: CSRF Protection (HIGH)

**Protect state-changing requests from cross-site attacks.**

```python
# Backend - CSRF Token Generation
import secrets
from fastapi import Cookie, HTTPException

def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

@app.get("/api/csrf-token")
async def get_csrf_token(response: Response):
    token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # Frontend needs to read it
        samesite="strict",
        secure=True  # HTTPS only in production
    )
    return {"csrf_token": token}

# Validate on state-changing requests
async def verify_csrf(
    x_csrf_token: str = Header(...),
    csrf_token: str = Cookie(...)
):
    if not secrets.compare_digest(x_csrf_token, csrf_token):
        raise HTTPException(403, "CSRF token mismatch")
```

```typescript
// Frontend - Include CSRF token in requests
async function apiRequest(url: string, options: RequestInit = {}) {
    const csrfToken = getCookie('csrf_token');

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',  // Send cookies
    });
}
```

**Requirements**:
- ✅ CSRF token required for all POST/PUT/DELETE requests
- ✅ Use double-submit cookie pattern
- ✅ SameSite=Strict on cookies
- ❌ GET requests should NEVER modify state

---

### Rule S6: Authentication Patterns (CRITICAL)

**Secure user identity verification.**

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

# Set tokens in secure cookies
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,      # JS cannot access
    secure=True,        # HTTPS only
    samesite="strict",  # CSRF protection
    max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
)
```

**Token Requirements**:
| Token Type | Expiry | Storage | HttpOnly |
|------------|--------|---------|----------|
| Access Token | 15 minutes | Cookie | Yes |
| Refresh Token | 7 days | Cookie | Yes |
| CSRF Token | Session | Cookie | No (JS needs access) |

---

### Rule S7: Authorization Patterns (CRITICAL)

**Enforce resource access control - validate ownership on EVERY request.**

```python
from fastapi import Depends, HTTPException

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Validate token and return user
    ...

async def verify_project_ownership(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Project:
    """Verify user owns the project - use for ALL project endpoints."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(404, "Project not found")

    if project.user_id != current_user.id:
        raise HTTPException(403, "Access denied")  # Don't reveal existence

    return project

# ✅ CORRECT - Always verify ownership
@app.get("/api/projects/{project_id}")
async def get_project(
    project: Project = Depends(verify_project_ownership)
):
    return project

# ❌ WRONG - No ownership check (anyone can access any project!)
@app.get("/api/projects/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.id == project_id).first()
```

**Authorization Rules**:
- ✅ ALWAYS verify ownership at API level (not just UI)
- ✅ Use dependency injection for consistent auth checks
- ✅ Return 403 Forbidden (not 404) to avoid info leakage
- ❌ NEVER trust client-side authorization only

---

### Rule S8: Sensitive Data Handling (HIGH)

**Protect PII and credentials in logs and storage.**

```python
import logging
import re

class SensitiveDataFilter(logging.Filter):
    """Filter sensitive data from logs."""

    PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\'>\s]+', 'password: [REDACTED]'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\'>\s]+', 'token: [REDACTED]'),
        (r'api_key["\']?\s*[:=]\s*["\']?[^"\'>\s]+', 'api_key: [REDACTED]'),
        (r'Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', 'Bearer [REDACTED]'),
    ]

    def filter(self, record):
        msg = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        record.msg = msg
        record.args = ()
        return True

# Apply filter to all loggers
logging.getLogger().addFilter(SensitiveDataFilter())
```

**What to NEVER log**:
| Data Type | Example | Action |
|-----------|---------|--------|
| Passwords | `password: abc123` | REDACT |
| API Keys | `sk-abc123...` | REDACT |
| JWT Tokens | `eyJ...` | REDACT |
| Full documents | PDF content | Truncate or omit |
| PII | Email, phone, SSN | Mask (`j***@email.com`) |

**Storage Requirements**:
- ✅ Hash passwords with bcrypt (never store plaintext)
- ✅ Encrypt sensitive fields at rest if required
- ❌ NEVER store credit card numbers (use payment provider)

---

### Security Phase Gates

| Rule | Severity | Gate | Enforcement |
|------|----------|------|-------------|
| S1 Secrets | CRITICAL | Pre-commit | Block commit if secrets detected |
| S2 Input Validation | CRITICAL | Phase 3→4 | Code review mandatory |
| S3 Rate Limiting | HIGH | Phase 3→4 | Verify middleware configured |
| S4 Security Headers | HIGH | Phase 4 | Automated header scan |
| S5 CSRF | HIGH | Phase 3→4 | Verify token flow |
| S6 Authentication | CRITICAL | Phase 3→4 | Security review |
| S7 Authorization | CRITICAL | Phase 3→4 | Verify ownership checks |
| S8 Sensitive Data | HIGH | Phase 3→4 | Log audit |

---

## Backend Infrastructure Rules

### Rule T1: Transaction Management (HIGH)

**Use context managers for database sessions - always rollback on exceptions.**

```python
from contextlib import contextmanager
from sqlalchemy.orm import Session

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ✅ CORRECT - Using context manager
def create_project(name: str) -> Project:
    with get_db_session() as db:
        project = Project(name=name)
        db.add(project)
        # Auto-commit on success, auto-rollback on exception
        return project

# ✅ CORRECT - FastAPI dependency (auto-cleanup)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/projects/create")
async def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**data.dict())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

# ❌ WRONG - No cleanup, session leak
def bad_create_project(name: str):
    db = SessionLocal()
    project = Project(name=name)
    db.add(project)
    db.commit()
    # Session never closed! Connection leak!
    return project
```

**Transaction Rules**:
- ✅ Always use context managers or FastAPI Depends
- ✅ Commit on success, rollback on exception
- ✅ Close session in `finally` block
- ❌ NEVER leave sessions open

---

### Rule L1: Logging Standards (MEDIUM)

**Use structured JSON logging with sensitive data masking.**

```python
import logging
import json
from datetime import datetime
from typing import Any

class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logging
def setup_logging(level: str = "INFO"):
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Add sensitive data filter (see S8)
    root_logger.addFilter(SensitiveDataFilter())

# Usage
logger = logging.getLogger(__name__)

# ✅ CORRECT - Structured logging with context
logger.info("Project created", extra={
    "event": "project_created",
    "project_id": project.id,
    "user_id": current_user.id,
})

# ❌ WRONG - Unstructured, hard to parse
logger.info(f"User {user_id} created project {project_id}")
```

**Log Levels**:
| Level | Use Case | Example |
|-------|----------|---------|
| DEBUG | Development only | Variable values, flow tracing |
| INFO | Normal operations | User actions, API calls |
| WARNING | Recoverable issues | Retry attempts, deprecation |
| ERROR | Failures | Exception caught, operation failed |
| CRITICAL | System failure | Database down, OOM |

---

### Rule L2: Audit Logging for Compliance (CRITICAL)

> **IEC 62443-4-2 CR 2.8, CR 6.1**: Systems must maintain audit logs of security-relevant events with timestamps, user identity, and action details.

**All security-relevant actions MUST be audit logged to a tamper-evident store.**

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditEventType(str, Enum):
    """Audit event categories per IEC 62443."""
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_PASSWORD_CHANGE = "auth.password.change"

    # Authorization events
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"

    # Data events
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Document events
    DOC_UPLOAD = "document.upload"
    DOC_DELETE = "document.delete"
    DOC_ACCESS = "document.access"

    # System events
    SYS_CONFIG_CHANGE = "system.config.change"
    SYS_BACKUP = "system.backup"
    SYS_RESTORE = "system.restore"

class AuditLog(Base):
    """Audit log table - append-only, no updates/deletes allowed."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=True)  # Null for system events
    user_email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    resource_type = Column(String(50), nullable=True)  # e.g., "project", "document"
    resource_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # "success", "failure", "denied"
    details = Column(JSON, nullable=True)  # Additional context
    request_id = Column(String(36), nullable=True)  # For request tracing


class AuditLogger:
    """Audit logger service - write-only operations."""

    def __init__(self, db_session_factory):
        self._session_factory = db_session_factory

    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        status: str,
        user_id: int | None = None,
        user_email: str | None = None,
        ip_address: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        request_id: str | None = None,
    ) -> None:
        """Write audit log entry. NEVER fails silently."""
        async with self._session_factory() as session:
            entry = AuditLog(
                event_type=event_type.value,
                user_id=user_id,
                user_email=user_email,
                ip_address=ip_address,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                action=action,
                status=status,
                details=details,
                request_id=request_id,
            )
            session.add(entry)
            await session.commit()


# ✅ CORRECT - Audit login attempt
async def login(credentials: LoginRequest, request: Request, audit: AuditLogger):
    try:
        user = await authenticate(credentials)
        await audit.log(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            action="User login",
            status="success",
            user_id=user.id,
            user_email=user.email,
            ip_address=request.client.host,
            details={"method": "password"},
        )
        return create_tokens(user)
    except AuthenticationError as e:
        await audit.log(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            action="User login failed",
            status="failure",
            user_email=credentials.email,
            ip_address=request.client.host,
            details={"reason": str(e)},
        )
        raise


# ✅ CORRECT - Audit data access
@app.get("/api/projects/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger),
):
    project = await project_service.get(project_id)

    await audit.log(
        event_type=AuditEventType.DATA_READ,
        action="Project viewed",
        status="success",
        user_id=current_user.id,
        resource_type="project",
        resource_id=project_id,
    )

    return project


# ✅ CORRECT - Audit authorization denial
async def verify_project_ownership(project_id: int, user: User, audit: AuditLogger):
    project = await get_project(project_id)

    if project.user_id != user.id:
        await audit.log(
            event_type=AuditEventType.AUTHZ_ACCESS_DENIED,
            action="Unauthorized project access attempt",
            status="denied",
            user_id=user.id,
            resource_type="project",
            resource_id=project_id,
            details={"owner_id": project.user_id},
        )
        raise HTTPException(403, "Access denied")

    return project
```

**Audit Requirements (IEC 62443 Compliance)**:

| Requirement | Implementation | Notes |
|-------------|----------------|-------|
| **Tamper-evident** | Append-only table, no UPDATE/DELETE | Use DB triggers to enforce |
| **Timestamped** | UTC timestamp on every entry | Auto-set by DB |
| **User identity** | user_id + user_email | Both for traceability |
| **Action details** | event_type + action + details JSON | Flexible context |
| **Retention** | Minimum 90 days, recommended 1 year | Configure per policy |
| **Access control** | Only admins can READ, nobody can MODIFY | Separate audit DB role |

**Events That MUST Be Audited**:

| Category | Events |
|----------|--------|
| **Authentication** | Login success/failure, logout, password change, token refresh |
| **Authorization** | Access granted, access denied |
| **Data Operations** | Create, read (sensitive), update, delete, export |
| **Documents** | Upload, delete, access |
| **System** | Config changes, backup, restore |

**Audit Sampling Policy** (for high-volume events):

> **Backend-Agent raised**: DOC_READ events could create massive log tables. Use sampling for read events.

| Event Type | Sampling Strategy | Rationale |
|------------|-------------------|-----------|
| **AUTH_*** | 100% (no sampling) | Security-critical, must log all |
| **AUTHZ_ACCESS_DENIED** | 100% | Security-critical |
| **DATA_CREATE/UPDATE/DELETE** | 100% | Modification events, must log all |
| **DATA_READ** | First per session | Reduces log bloat by 90%+ |
| **DOC_UPLOAD/DELETE** | 100% | Modification events |
| **DOC_ACCESS** | First per document per session | Reduces log bloat |
| **SYS_*** | 100% | Critical system events |

**Implementation**:
```python
from functools import lru_cache
from datetime import datetime, timedelta

class AuditLogger:
    def __init__(self, db_session_factory):
        self._session_factory = db_session_factory
        self._read_cache: dict[str, datetime] = {}  # session_id:resource -> last_logged

    def _should_log_read(self, session_id: str, resource_type: str, resource_id: str) -> bool:
        """Only log first read per resource per session (reduces log volume 90%+)."""
        cache_key = f"{session_id}:{resource_type}:{resource_id}"
        now = datetime.utcnow()

        if cache_key in self._read_cache:
            # Already logged this session - skip
            return False

        self._read_cache[cache_key] = now
        return True

    async def log(
        self,
        event_type: AuditEventType,
        session_id: str | None = None,
        **kwargs
    ) -> None:
        # Apply sampling for read events
        if event_type in (AuditEventType.DATA_READ, AuditEventType.DOC_ACCESS):
            if session_id and not self._should_log_read(
                session_id,
                kwargs.get('resource_type', ''),
                kwargs.get('resource_id', '')
            ):
                return  # Skip - already logged this session

        # Log all other events (no sampling)
        await self._write_log(event_type, **kwargs)
```

**Database Trigger (Prevent Tampering)**:
```sql
-- Prevent UPDATE on audit_logs
CREATE TRIGGER prevent_audit_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audit logs cannot be modified';
END;

-- Prevent DELETE on audit_logs
CREATE TRIGGER prevent_audit_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audit logs cannot be deleted';
END;
```

**Enforcement**: Phase 3→4 BLOCKED if security-relevant endpoints lack audit logging.

---

## Additional Frontend Rules

### Rule C15: Bundle Optimization (HIGH)

**Lazy load heavy components to reduce initial bundle size.**

```typescript
// ✅ CORRECT - Lazy load heavy libraries
<script lang="ts">
    import { onMount } from 'svelte';

    let MarkdownRenderer: any;
    let GraphViewer: any;

    onMount(async () => {
        // Load only when component mounts
        const [markdownModule, graphModule] = await Promise.all([
            import('$lib/components/MarkdownRenderer.svelte'),
            import('$lib/components/GraphViewer.svelte'),
        ]);
        MarkdownRenderer = markdownModule.default;
        GraphViewer = graphModule.default;
    });
</script>

{#if MarkdownRenderer}
    <svelte:component this={MarkdownRenderer} {content} />
{:else}
    <div class="loading">Loading...</div>
{/if}

// ❌ WRONG - Static imports bloat initial bundle
<script>
    import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
    import GraphViewer from '$lib/components/GraphViewer.svelte';
    import { marked } from 'marked';  // 30KB+
    import * as d3 from 'd3';         // 100KB+
    import Prism from 'prismjs';      // 20KB+
</script>
```

**Bundle Budget**:
| Bundle | Limit | Action if Exceeded |
|--------|-------|-------------------|
| Initial JS | 60 KB (gzip) | Lazy load components |
| Initial CSS | 15 KB (gzip) | Purge unused Tailwind |
| Per-route chunk | 30 KB (gzip) | Split further |

**Heavy Libraries to Lazy Load**:
- `marked` / `markdown-it` (Markdown rendering)
- `prismjs` / `shiki` (Syntax highlighting)
- `d3` (Data visualization)
- `chart.js` (Charts)
- `pdfjs-dist` (PDF viewing)

---

### Rule C16: SvelteKit Patterns (MEDIUM)

**Use SvelteKit conventions for data loading and routing.**

```typescript
// +page.server.ts - Server-side data loading
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, locals }) => {
    const project = await getProject(params.id);
    return {
        project,
        // Data is typed and available in +page.svelte
    };
};

// +page.svelte - Access loaded data
<script lang="ts">
    import type { PageData } from './$types';
    import { page } from '$app/stores';

    export let data: PageData;  // From load function

    // ✅ CORRECT - Access route params reactively
    $: projectId = $page.params.id;

    // ✅ CORRECT - Access loaded data
    $: project = data.project;
</script>

// ❌ WRONG - Fetch in onMount (causes loading flash)
<script>
    import { onMount } from 'svelte';
    let project;

    onMount(async () => {
        project = await fetch(`/api/projects/${id}`).then(r => r.json());
    });
</script>
```

**SvelteKit Conventions**:
| File | Purpose | When to Use |
|------|---------|-------------|
| `+page.svelte` | Page component | Always |
| `+page.ts` | Client-side load | Public data, no secrets |
| `+page.server.ts` | Server-side load | Auth required, secrets |
| `+layout.svelte` | Shared layout | Wrap child pages |
| `+error.svelte` | Error page | Custom error UI |

---

### Rule C17: Store Cleanup (MEDIUM)

**Properly manage store subscriptions to prevent memory leaks.**

```svelte
<!-- ✅ CORRECT - Auto-subscription with $ (auto-cleanup) -->
<script>
    import { messages } from '$lib/stores/chat';
</script>

{#each $messages as message}
    <ChatMessage {message} />
{/each}

<!-- ✅ CORRECT - Manual subscription with cleanup -->
<script>
    import { onDestroy } from 'svelte';
    import { messages } from '$lib/stores/chat';

    let messageList = [];

    const unsubscribe = messages.subscribe(value => {
        messageList = value;
    });

    onDestroy(() => {
        unsubscribe();  // MUST cleanup!
    });
</script>

<!-- ❌ WRONG - Manual subscription without cleanup (MEMORY LEAK!) -->
<script>
    import { messages } from '$lib/stores/chat';

    let messageList = [];
    messages.subscribe(value => {
        messageList = value;
    });
    // No cleanup - subscription lives forever!
</script>
```

**Store Rules**:
- ✅ Prefer `$store` auto-subscription (auto-cleanup)
- ✅ If manual `.subscribe()`, MUST call unsubscribe in `onDestroy`
- ✅ Use `derived` for computed values
- ❌ NEVER subscribe without cleanup

---

### Rule C18: TailwindCSS Patterns (LOW)

**Use utility-first approach - avoid @apply in components.**

```svelte
<!-- ✅ CORRECT - Utility classes directly -->
<button class="
    px-4 py-2
    bg-blue-500 hover:bg-blue-600
    text-white font-medium
    rounded-lg
    transition-colors
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
">
    Save Project
</button>

<!-- ✅ CORRECT - Extract to component for reuse -->
<!-- Button.svelte -->
<script>
    export let variant: 'primary' | 'secondary' = 'primary';

    const variants = {
        primary: 'bg-blue-500 hover:bg-blue-600 text-white',
        secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    };
</script>

<button class="px-4 py-2 rounded-lg transition-colors {variants[variant]}">
    <slot />
</button>

<!-- ❌ WRONG - @apply defeats Tailwind's purpose -->
<style>
    .btn-primary {
        @apply px-4 py-2 bg-blue-500 text-white rounded-lg;
    }
</style>
<button class="btn-primary">Save</button>

<!-- ❌ WRONG - Inline styles when Tailwind has utilities -->
<button style="padding: 1rem; background: blue;">Save</button>
```

**When @apply IS acceptable**:
- Base styles in `app.css` (typography, resets)
- Third-party component overrides
- Complex animations

---

### Rule C19: File Upload Security (CRITICAL)

**Validate all uploaded files to prevent malicious content injection.**

```python
import magic
import hashlib
from pathlib import Path
from fastapi import UploadFile, HTTPException
from pydantic import BaseModel

# Allowed file types with MIME validation
ALLOWED_TYPES = {
    # Documents
    "application/pdf": {"ext": [".pdf"], "max_size": 100 * 1024 * 1024},  # 100MB
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "ext": [".docx"], "max_size": 50 * 1024 * 1024  # 50MB
    },
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
        "ext": [".xlsx"], "max_size": 50 * 1024 * 1024  # 50MB
    },
    "text/plain": {"ext": [".txt", ".md"], "max_size": 20 * 1024 * 1024},  # 20MB
    "text/markdown": {"ext": [".md"], "max_size": 20 * 1024 * 1024},  # 20MB

    # Images (for OCR)
    "image/png": {"ext": [".png"], "max_size": 20 * 1024 * 1024},  # 20MB
    "image/jpeg": {"ext": [".jpg", ".jpeg"], "max_size": 20 * 1024 * 1024},  # 20MB
}

# Dangerous patterns to reject
DANGEROUS_PATTERNS = [
    b"<%",           # ASP/JSP tags
    b"<?php",        # PHP tags
    b"<script",      # JavaScript
    b"javascript:",  # JS protocol
    b"vbscript:",    # VBScript protocol
    b"data:text/html",  # Data URI HTML
]


class FileValidationResult(BaseModel):
    is_valid: bool
    mime_type: str | None
    file_hash: str | None
    error: str | None


async def validate_upload(file: UploadFile) -> FileValidationResult:
    """
    Comprehensive file upload validation.

    Checks:
    1. File extension whitelist
    2. MIME type detection (magic bytes, not just Content-Type header)
    3. Extension-MIME consistency
    4. File size limits
    5. Dangerous content patterns
    6. Generate file hash for deduplication
    """

    # 1. Check extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    allowed_extensions = set()
    for config in ALLOWED_TYPES.values():
        allowed_extensions.update(config["ext"])

    if ext not in allowed_extensions:
        return FileValidationResult(
            is_valid=False,
            mime_type=None,
            file_hash=None,
            error=f"File extension '{ext}' not allowed. Allowed: {sorted(allowed_extensions)}"
        )

    # 2. Read file content (with size limit check)
    content = await file.read()
    await file.seek(0)  # Reset for later use

    # 3. Detect actual MIME type using magic bytes
    detected_mime = magic.from_buffer(content, mime=True)

    if detected_mime not in ALLOWED_TYPES:
        return FileValidationResult(
            is_valid=False,
            mime_type=detected_mime,
            file_hash=None,
            error=f"File type '{detected_mime}' not allowed"
        )

    # 4. Verify extension matches detected MIME
    type_config = ALLOWED_TYPES[detected_mime]
    if ext not in type_config["ext"]:
        return FileValidationResult(
            is_valid=False,
            mime_type=detected_mime,
            file_hash=None,
            error=f"Extension '{ext}' doesn't match detected type '{detected_mime}'"
        )

    # 5. Check file size
    if len(content) > type_config["max_size"]:
        max_mb = type_config["max_size"] / (1024 * 1024)
        return FileValidationResult(
            is_valid=False,
            mime_type=detected_mime,
            file_hash=None,
            error=f"File too large. Maximum size for {detected_mime}: {max_mb}MB"
        )

    # 6. Scan for dangerous patterns (first 8KB)
    header = content[:8192].lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in header:
            return FileValidationResult(
                is_valid=False,
                mime_type=detected_mime,
                file_hash=None,
                error="File contains potentially dangerous content"
            )

    # 7. Generate hash for deduplication and integrity
    file_hash = hashlib.sha256(content).hexdigest()

    return FileValidationResult(
        is_valid=True,
        mime_type=detected_mime,
        file_hash=file_hash,
        error=None
    )


# ✅ CORRECT - Validate before processing
@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile,
    project_id: int,
    current_user: User = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger),
):
    # Validate file
    validation = await validate_upload(file)

    if not validation.is_valid:
        await audit.log(
            event_type=AuditEventType.DOC_UPLOAD,
            action="Document upload rejected",
            status="failure",
            user_id=current_user.id,
            resource_type="document",
            details={"error": validation.error, "filename": file.filename},
        )
        raise HTTPException(400, validation.error)

    # Safe to process
    document = await document_service.create(
        project_id=project_id,
        filename=sanitize_filename(file.filename),
        mime_type=validation.mime_type,
        file_hash=validation.file_hash,
        content=await file.read(),
    )

    await audit.log(
        event_type=AuditEventType.DOC_UPLOAD,
        action="Document uploaded",
        status="success",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document.id,
        details={"mime_type": validation.mime_type, "hash": validation.file_hash},
    )

    return document


def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filename."""
    import re
    # Keep only alphanumeric, dash, underscore, dot
    sanitized = re.sub(r'[^\w\-.]', '_', filename)
    # Prevent directory traversal
    sanitized = sanitized.replace('..', '_')
    # Limit length
    return sanitized[:255]
```

**File Upload Security Checklist**:

| Check | Method | Severity |
|-------|--------|----------|
| **Extension whitelist** | Check against allowed list | CRITICAL |
| **MIME type validation** | Use `python-magic` (libmagic) | CRITICAL |
| **Extension-MIME match** | Verify consistency | HIGH |
| **File size limit** | Per-type maximum | HIGH |
| **Dangerous content scan** | Check for script tags, etc. | HIGH |
| **Filename sanitization** | Remove special chars, path traversal | HIGH |
| **Hash generation** | SHA-256 for deduplication | MEDIUM |

**Size Limits by Type**:

| File Type | Max Size | Rationale |
|-----------|----------|-----------|
| PDF | 100 MB | Large technical documents |
| Word/Excel | 50 MB | Standard office docs |
| Text/Markdown | 20 MB | Plain text files |
| Images | 20 MB | For OCR processing |

**Dependencies**:
```bash
pip install python-magic  # Requires libmagic system library
# Ubuntu/Debian: apt-get install libmagic1
# macOS: brew install libmagic
```

**Enforcement**: Phase 3→4 BLOCKED if file upload endpoints lack validation.

---

### Rule C20: Timer/Interval Cleanup Pattern (HIGH)

**Always cleanup timers and intervals, even when errors occur. Use finally blocks.**

```svelte
<!-- ✅ CORRECT - Cleanup in finally block (handles error cases) -->
<script lang="ts">
    import { onDestroy } from 'svelte';

    let pollingInterval: ReturnType<typeof setInterval> | null = null;

    async function startPolling() {
        try {
            pollingInterval = setInterval(async () => {
                await checkStatus();
            }, 1000);
        } catch (error) {
            console.error('Polling error:', error);
        } finally {
            // Always cleanup, even if error occurs
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        }
    }

    onDestroy(() => {
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
    });
</script>

<!-- ❌ WRONG - Interval not cleared on error (MEMORY LEAK!) -->
<script lang="ts">
    let interval: ReturnType<typeof setInterval>;

    async function startPolling() {
        interval = setInterval(async () => {
            try {
                await checkStatus();
            } catch (error) {
                // Error thrown but interval keeps running!
                console.error(error);
            }
        }, 1000);
    }
</script>
```

**Timer Cleanup Rules**:
- ✅ Store timer/interval handles in component-level variables
- ✅ Clear timers in `finally` blocks for error resilience
- ✅ Always clear in `onDestroy`
- ✅ Set handle to `null` after clearing (prevents double-clear)
- ❌ NEVER leave intervals running on component unmount

**Bug Reference**: BUG-INTERVAL-003 (DocumentUploader interval leak)

---

### Rule C21: Event Listener Cleanup Pattern (HIGH)

**Track event listeners with a Map and remove them on component destroy.**

```svelte
<!-- ✅ CORRECT - Track handlers with Map for proper cleanup -->
<script lang="ts">
    import { onDestroy, afterUpdate } from 'svelte';

    // Map to track element -> handler relationships
    const clickHandlers = new Map<HTMLElement, () => void>();

    afterUpdate(() => {
        const elements = document.querySelectorAll('.copyable');
        elements.forEach((el) => {
            if (!(el instanceof HTMLElement)) return;
            if (clickHandlers.has(el)) return; // Skip if already attached

            const handler = () => navigator.clipboard.writeText(el.textContent || '');
            el.addEventListener('click', handler);
            clickHandlers.set(el, handler);
        });
    });

    onDestroy(() => {
        // Remove all tracked handlers
        clickHandlers.forEach((handler, element) => {
            element.removeEventListener('click', handler);
        });
        clickHandlers.clear();
    });
</script>

<!-- ❌ WRONG - Anonymous handlers cannot be removed (MEMORY LEAK!) -->
<script lang="ts">
    import { afterUpdate } from 'svelte';

    afterUpdate(() => {
        document.querySelectorAll('.copyable').forEach((el) => {
            // Anonymous function - cannot be removed later!
            el.addEventListener('click', () => {
                navigator.clipboard.writeText(el.textContent || '');
            });
        });
    });
    // No cleanup possible - handlers leak!
</script>
```

**Event Listener Rules**:
- ✅ Use a `Map<Element, Handler>` to track listeners
- ✅ Store named handler references, not anonymous functions
- ✅ Check for duplicates before adding (`Map.has()`)
- ✅ Remove all listeners in `onDestroy`
- ❌ NEVER use anonymous handlers if cleanup is needed

**Bug Reference**: BUG-CLICK-001 (MessageContent click handlers)

---

### Rule C22: Reactive Statement Guard Pattern (HIGH)

**Prevent infinite loops in reactive statements with guard variables.**

```svelte
<!-- ✅ CORRECT - Guard variable prevents infinite re-execution -->
<script lang="ts">
    import { currentProjectId, projects } from '$lib/stores/projects';

    // Guard variable to track last loaded state
    let lastLoadedProjectId: number | null = null;

    // Reactive: Only load when project ID actually changes
    $: if ($currentProjectId !== null && $currentProjectId !== lastLoadedProjectId) {
        lastLoadedProjectId = $currentProjectId;  // Update guard BEFORE async
        loadProjectData($currentProjectId);
    }

    async function loadProjectData(projectId: number) {
        const data = await fetchProject(projectId);
        // Process data...
    }
</script>

<!-- ❌ WRONG - No guard, causes infinite loop -->
<script lang="ts">
    import { currentProjectId, projects } from '$lib/stores/projects';

    // DANGER: This runs infinitely!
    // 1. Reactive triggers on $currentProjectId change
    // 2. loadProjectData may update a store
    // 3. Store update triggers Svelte reactivity
    // 4. Reactive re-evaluates and runs again!
    $: if ($currentProjectId) {
        loadProjectData($currentProjectId);
    }
</script>

<!-- ✅ CORRECT - Capture values to prevent stale closures -->
<script lang="ts">
    $: if ($currentProjectId && $currentProjectId !== lastLoadedProjectId) {
        const projectIdToLoad = $currentProjectId;  // Capture value
        lastLoadedProjectId = projectIdToLoad;
        loadProjectData(projectIdToLoad);  // Use captured value
    }
</script>
```

**Reactive Guard Rules**:
- ✅ Use guard variable to track "last loaded" state
- ✅ Update guard BEFORE calling async function
- ✅ Capture reactive values before async operations
- ✅ Compare against guard in reactive condition
- ❌ NEVER call async functions in reactive without guards

**Bug Reference**: BUG-LOOP-001 (ProjectSelector infinite loop)

---

### Rule C23: Component State Reset on Destroy (MEDIUM)

**Reset component-level tracking variables in onDestroy to prevent stale state.**

```svelte
<!-- ✅ CORRECT - Reset tracking variables on destroy -->
<script lang="ts">
    import { onDestroy } from 'svelte';

    let lastLoadedProjectId: number | null = null;
    let isInitialized = false;
    let pendingRequests = new Set<string>();

    onDestroy(() => {
        // Reset all tracking state
        lastLoadedProjectId = null;
        isInitialized = false;
        pendingRequests.clear();
    });
</script>

<!-- ❌ WRONG - State persists if component is reused -->
<script lang="ts">
    let lastLoadedProjectId: number | null = null;
    // If component is remounted, lastLoadedProjectId may have stale value!
</script>
```

**State Reset Rules**:
- ✅ Reset `lastLoaded*` variables in `onDestroy`
- ✅ Clear Sets/Maps used for tracking
- ✅ Reset boolean flags (isInitialized, isLoading, etc.)
- ❌ NEVER assume component state is fresh on remount

**Bug Reference**: BUG-RESET-004 (DocumentsTab lastLoadedProjectId)

---

### Rule C24: Race Condition Prevention Pattern (CRITICAL)

**Capture context values before async operations to prevent race conditions.**

```svelte
<!-- ✅ CORRECT - Capture IDs before async to prevent races -->
<script lang="ts">
    import { currentProjectId } from '$lib/stores/projects';
    import { onDestroy } from 'svelte';

    let isCancelled = false;

    async function uploadDocument(file: File) {
        // CAPTURE current project ID before async operation
        const projectIdAtStart = $currentProjectId;

        if (!projectIdAtStart) {
            console.error('No project selected');
            return;
        }

        try {
            await uploadFile(file, projectIdAtStart);  // Use captured value

            // Check if context changed during upload
            if (isCancelled || $currentProjectId !== projectIdAtStart) {
                console.log('Context changed, discarding result');
                return;
            }

            // Safe to update UI - context is still valid
            refreshDocumentList();
        } catch (error) {
            console.error('Upload failed:', error);
        }
    }

    onDestroy(() => {
        isCancelled = true;  // Signal any in-flight requests to abort
    });
</script>

<!-- ❌ WRONG - Using reactive store during async (RACE CONDITION!) -->
<script lang="ts">
    import { currentProjectId } from '$lib/stores/projects';

    async function uploadDocument(file: File) {
        // DANGER: $currentProjectId may change during upload!
        await uploadFile(file, $currentProjectId);  // Wrong project!

        // By now, user may have switched projects
        // This refresh updates the WRONG project's document list!
        refreshDocumentList();
    }
</script>
```

**Race Condition Prevention Rules**:
- ✅ Capture store values BEFORE any `await`
- ✅ Use `isCancelled` flag checked in `onDestroy`
- ✅ Verify context hasn't changed after async completes
- ✅ Discard results if context changed during operation
- ❌ NEVER use `$store` values after `await` without re-checking

**Bug Reference**: BUG-UPLOAD-001 (Document upload race condition)

---

### Rule C25: Use get() for One-time Store Reads (MEDIUM)

**Use Svelte's `get()` for one-time reads instead of subscribe/unsubscribe.**

```typescript
// ✅ CORRECT - Use get() for one-time read
import { get } from 'svelte/store';
import { messages } from '$lib/stores/messages';

function getCurrentMessageCount(): number {
    return get(messages).items.length;
}

// ❌ WRONG - Subscribe/unsubscribe pattern is fragile and can leak
import { messages } from '$lib/stores/messages';

function getCurrentMessageCount(): number {
    let count = 0;
    const unsubscribe = messages.subscribe(value => {
        count = value.items.length;
    });
    unsubscribe();  // Easy to forget! Memory leak if error before this
    return count;
}
```

```svelte
<!-- ✅ CORRECT - get() in event handlers or async callbacks -->
<script lang="ts">
    import { get } from 'svelte/store';
    import { messages } from '$lib/stores/messages';

    async function handleComplete() {
        // One-time read of current state
        const currentCount = get(messages).items.length;
        await updateConversation({ message_count: currentCount });
    }
</script>

<!-- Note: For template reactivity, still use $messages -->
<p>Total: {$messages.items.length}</p>
```

**get() vs $ Rules**:
| Use Case | Solution |
|----------|----------|
| Template binding | `$store` (auto-subscription) |
| One-time read in handler | `get(store)` |
| One-time read after async | `get(store)` |
| Computed/derived values | `$:` reactive statement |

**Bug Reference**: BUG-MEM-001 (SSE client memory leak)

---

### Rule C26: Debounce Timer Cleanup (MEDIUM)

**Clear debounce timers when the action is cancelled or component destroyed.**

```svelte
<!-- ✅ CORRECT - Clear debounce timer on clear action -->
<script lang="ts">
    import { onDestroy } from 'svelte';

    let searchQuery = '';
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    function handleInput(value: string) {
        searchQuery = value;

        // Clear any pending debounce
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }

        // Set new debounce
        debounceTimer = setTimeout(() => {
            performSearch(value);
        }, 300);
    }

    function handleClear() {
        searchQuery = '';

        // IMPORTANT: Clear debounce to prevent stale search
        if (debounceTimer) {
            clearTimeout(debounceTimer);
            debounceTimer = null;
        }

        // Immediately show unfiltered results
        performSearch('');
    }

    onDestroy(() => {
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
    });
</script>

<!-- ❌ WRONG - Debounce not cleared on clear action -->
<script lang="ts">
    function handleClear() {
        searchQuery = '';
        // BUG: Old debounce timer still pending!
        // User clears search, then 300ms later old search runs!
        performSearch('');
    }
</script>
```

**Debounce Rules**:
- ✅ Clear timer when user explicitly clears input
- ✅ Clear timer in `onDestroy`
- ✅ Set timer to `null` after clearing
- ❌ NEVER let stale debounced actions execute after clear

**Bug Reference**: BUG-SEARCH-004 (SearchInput debounce leak)

---

### Rule C27: Never Silently Swallow Errors (MEDIUM)

**Always log errors, even when catching them for graceful degradation.**

```typescript
// ✅ CORRECT - Log error before continuing
async function loadProjectStats(projectId: number): Promise<ProjectStats | null> {
    try {
        return await fetchStats(projectId);
    } catch (error) {
        // Log the error for debugging
        logger.warn('Failed to load project stats', { projectId, error });
        // Return null for graceful degradation
        return null;
    }
}

// ❌ WRONG - Error silently swallowed
async function loadProjectStats(projectId: number): Promise<ProjectStats | null> {
    try {
        return await fetchStats(projectId);
    } catch {
        return null;  // Error lost! Impossible to debug
    }
}

// ✅ CORRECT - Optional result with error logging
const [projectData, statsData] = await Promise.all([
    fetchProject(projectId),
    getProjectStats(projectId).catch((err) => {
        logger.warn('Failed to load project stats', { projectId, error: err });
        return null;  // Graceful degradation with logging
    })
]);
```

**Error Handling Rules**:
- ✅ Always log caught errors (at least `logger.warn`)
- ✅ Include context (IDs, operation name) in log
- ✅ Return sensible defaults for graceful degradation
- ❌ NEVER use empty `catch {}` blocks
- ❌ NEVER swallow errors without logging

**Bug Reference**: BUG-ERR-005 (SettingsTab silent error)

---

## Enforcement Tools

### Automated Quality Checks

Add these to your CI/CD pipeline and `package.json` scripts:

```json
{
  "scripts": {
    "lint": "eslint . --ext .ts,.svelte",
    "lint:fix": "eslint . --ext .ts,.svelte --fix",
    "check:complexity": "npx eslint --rule 'complexity: [error, 10]' src/",
    "check:a11y": "npx playwright test tests/a11y/",
    "check:security": "npm audit --audit-level=moderate",
    "check:bundle": "npx vite-bundle-analyzer",
    "check:all": "npm run lint && npm run check:complexity && npm run check:security"
  }
}
```

### Complexity Checker

```bash
# TypeScript/JavaScript
npm install -D eslint-plugin-complexity

# .eslintrc.js
module.exports = {
  rules: {
    'complexity': ['error', { max: 10 }],
  }
};

# Python
pip install radon

# Check complexity (block if average > B grade)
radon cc backend/ -a -nc --total-average
```

### Accessibility E2E Testing

```typescript
// tests/a11y/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility', () => {
    test('Home page has no a11y violations', async ({ page }) => {
        await page.goto('/');
        await injectAxe(page);
        await checkA11y(page, undefined, {
            detailedReport: true,
            detailedReportOptions: { html: true },
        });
    });

    test('Chat interface has no a11y violations', async ({ page }) => {
        await page.goto('/project/1');
        await injectAxe(page);
        await checkA11y(page);
    });
});
```

```bash
# Install
npm install -D @axe-core/playwright
```

### Security Scanning

```bash
# Frontend - npm audit
npm audit --audit-level=moderate
# Fails if moderate+ vulnerabilities found

# Backend - bandit (Python security linter)
pip install bandit
bandit -r backend/ -ll  # -ll = only medium+ severity

# Secrets detection - gitleaks
# Install: https://github.com/gitleaks/gitleaks
gitleaks detect --source . --verbose
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  - repo: local
    hooks:
      - id: npm-audit
        name: npm audit
        entry: npm audit --audit-level=moderate
        language: system
        pass_filenames: false
```

---

## 📋 Phase Gate Quick Reference Card (1-Page Summary)

> **Print this page and keep at your desk!**

### Phase 2 → Phase 3 (Code Review) - BLOCKERS

| # | Check | Command/Method | Severity |
|---|-------|----------------|----------|
| 1 | File size ≤ 400/500 lines | `wc -l <file>` | 🔴 BLOCK |
| 2 | Contract compliance (o3, o7, o8, o9) | Manual review | 🔴 BLOCK |
| 3 | Security rules (S1-S8) implemented | Code review | 🔴 BLOCK |
| 4 | Audit logging (L2) on security endpoints | Code review | 🔴 BLOCK |
| 5 | File upload validation (C19) | Code review | 🔴 BLOCK |
| 6 | TypeScript strict mode | `npx tsc --noEmit` | 🟡 FIX |
| 7 | No console.log in production | `grep -r "console.log" src/` | 🟡 FIX |
| 8 | Pydantic validation (C11) | Code review | 🟡 FIX |
| 9 | Accessibility basics (C13) | Manual + lint | 🟡 FIX |
| 10 | Documentation ≥ 15-20% (C14) | Script check | 🟢 WARN |

### Phase 3 → Phase 4 (Integration) - BLOCKERS

| # | Check | Command/Method | Severity |
|---|-------|----------------|----------|
| 1 | Coverage ≥ 70% | `npm run test:coverage` | 🔴 BLOCK |
| 2 | Test pyramid compliant (60/20/10/10) | Test count analysis | 🔴 BLOCK |
| 3 | Regression tests pass (Stage 2+) | `npm run test` | 🔴 BLOCK |
| 4 | Permission check (no root cache) | `find node_modules/.vite -user root` | 🔴 BLOCK |
| 5 | A11y tests pass | `npm run test:a11y` | 🟡 FIX |
| 6 | Layered architecture (A1) | Code review | 🟡 FIX |
| 7 | Database selection correct (A2) | Code review | 🟡 FIX |
| 8 | RAG configuration (R1-R9) | Config review | 🟡 FIX |
| 9 | E2E uses real backend (no MSW) | Test file review | 🔴 BLOCK |
| 10 | Bundle size ≤ 60KB gzipped | `npm run check:bundle` | 🟢 WARN |

### Phase 4 → Phase 5 (Manual Approval) - BLOCKERS

| # | Check | Command/Method | Severity |
|---|-------|----------------|----------|
| 1 | All E2E tests passing | `npm run test:e2e` | 🔴 BLOCK |
| 2 | Visual regression passing | `npm run test:visual` | 🟡 FIX |
| 3 | Performance (LCP ≤ 2.5s, FCP ≤ 1.8s) | `npm run test:performance` | 🟡 FIX |
| 4 | Full a11y scan (axe-core) | `npm run test:a11y` | 🟡 FIX |
| 5 | No critical security issues | `npm audit` | 🔴 BLOCK |

### Quick Commands Cheat Sheet

```bash
# Phase 2→3 Checks
wc -l frontend/src/**/*.svelte | sort -n | tail -10  # File sizes
npx tsc --noEmit                                      # TypeScript
grep -rn "console.log" frontend/src/                  # Console logs
npm run lint                                          # Linting

# Phase 3→4 Checks
npm run test:coverage                                 # Coverage
npm run test:a11y                                     # Accessibility
find frontend/node_modules/.vite -user root 2>/dev/null  # Permissions
npm run check:bundle                                  # Bundle size

# Phase 4→5 Checks
npm run test:e2e                                      # E2E tests
npm run test:visual                                   # Visual regression
npm run test:performance                              # Performance
npm audit --audit-level=moderate                      # Security
```

### Legend

| Icon | Meaning | Action |
|------|---------|--------|
| 🔴 BLOCK | Cannot proceed | Must fix before transition |
| 🟡 FIX | High priority | Must fix, can proceed with approval |
| 🟢 WARN | Low priority | Should fix, won't block |

---

## See Also

- **Testing Rules**: `.claude-bus/standards/TESTING-RULES.md`
- **Testing Standards**: `docs/TESTING-STANDARDS.md`
- **Stage Definitions**: `todo/STAGE_DEFINITIONS.md`
- **Contracts**: `.claude-bus/contracts/`

---

**Document Owner**: PM-Architect-Agent
**Last Updated**: 2025-12-20 (Version 2.3 - Added Svelte lifecycle patterns C20-C27 based on Agent Meeting bug discoveries)
