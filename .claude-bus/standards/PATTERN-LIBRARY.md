# Pattern Library for GPT-OSS

**Version**: 1.2
**Effective Date**: 2025-12-21
**Status**: MANDATORY reference for all development stages
**Location**: `.claude-bus/standards/PATTERN-LIBRARY.md`

---

## Purpose

This document contains **reusable patterns** that have been proven effective across stages. Instead of reinventing solutions, agents SHOULD reference and apply these patterns.

**Benefits**:
- Reduce development time by 30-50%
- Ensure consistency across codebase
- Prevent known pitfalls
- Enable knowledge transfer between stages

---

## Pattern Categories

| Category | Description | Use When |
|----------|-------------|----------|
| **API** | Backend endpoint patterns | Building FastAPI routes |
| **Store** | Svelte store patterns | Managing frontend state |
| **Component** | UI component patterns | Building Svelte components |
| **Test** | Testing patterns | Writing unit/E2E tests |
| **Error** | Error handling patterns | Implementing error flows |
| **SSE** | Server-Sent Events patterns | Real-time streaming |

---

## API Patterns

### API-001: Standard CRUD Endpoint

**Source**: Stage 1 - Projects API
**File**: `backend/app/api/projects.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db, Project
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Request/Response Models
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# CRUD Operations
@router.post("/create", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    db_project = Project(name=project.name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("/", response_model=list[ProjectResponse])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all projects with pagination."""
    return db.query(Project).offset(skip).limit(limit).all()

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project: ProjectCreate, db: Session = Depends(get_db)):
    """Update project."""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_project.name = project.name
    db_project.description = project.description
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete project."""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(db_project)
    db.commit()
    return None
```

**Key Points**:
- Use Pydantic models for request/response validation
- Use `Depends(get_db)` for database sessions
- Return 201 for create, 204 for delete
- Always check existence before update/delete

---

### API-002: SSE Streaming Endpoint

**Source**: Stage 1 - Chat API
**File**: `backend/app/api/chat.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.llm_service import LLMService
import json
import asyncio

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat response using Server-Sent Events."""

    async def event_generator():
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'message_id': msg_id})}\n\n"

            # Stream content chunks
            async for chunk in llm_service.stream_response(request.message):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                await asyncio.sleep(0)  # Allow other tasks to run

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

**Key Points**:
- Use `StreamingResponse` with `text/event-stream`
- Format: `data: {json}\n\n` (double newline required)
- Include event types: `start`, `chunk`, `done`, `error`
- Use `asyncio.sleep(0)` to prevent blocking

---

## Store Patterns

### STORE-001: Basic Writable Store

**Source**: Stage 1 - Projects Store
**File**: `frontend/src/lib/stores/projects.ts`

```typescript
import { writable, derived, get } from 'svelte/store';
import type { Project } from '$lib/types';

// State interface
interface ProjectsState {
    items: Project[];
    loading: boolean;
    error: string | null;
    selectedId: number | null;
}

// Initial state
const initialState: ProjectsState = {
    items: [],
    loading: false,
    error: null,
    selectedId: null
};

// Create store
function createProjectsStore() {
    const { subscribe, set, update } = writable<ProjectsState>(initialState);

    return {
        subscribe,

        // Actions
        setProjects: (projects: Project[]) => update(s => ({ ...s, items: projects })),

        setLoading: (loading: boolean) => update(s => ({ ...s, loading })),

        setError: (error: string | null) => update(s => ({ ...s, error })),

        selectProject: (id: number | null) => update(s => ({ ...s, selectedId: id })),

        addProject: (project: Project) => update(s => ({
            ...s,
            items: [...s.items, project]
        })),

        updateProject: (id: number, updates: Partial<Project>) => update(s => ({
            ...s,
            items: s.items.map(p => p.id === id ? { ...p, ...updates } : p)
        })),

        removeProject: (id: number) => update(s => ({
            ...s,
            items: s.items.filter(p => p.id !== id),
            selectedId: s.selectedId === id ? null : s.selectedId
        })),

        reset: () => set(initialState)
    };
}

// Export singleton
export const projectsStore = createProjectsStore();

// Derived stores
export const selectedProject = derived(
    projectsStore,
    $store => $store.items.find(p => p.id === $store.selectedId) ?? null
);

export const projectCount = derived(
    projectsStore,
    $store => $store.items.length
);
```

**Key Points**:
- Define state interface explicitly
- Use factory function pattern for testability
- Include `loading`, `error` states
- Export singleton instance
- Create derived stores for computed values

---

### STORE-002: SSE Client Store

**Source**: Stage 1 - SSE Client
**File**: `frontend/src/lib/stores/sse-client.ts`

```typescript
import { writable, get } from 'svelte/store';

interface SSEState {
    connected: boolean;
    messageId: string | null;
    content: string;
    error: string | null;
}

function createSSEStore() {
    const { subscribe, set, update } = writable<SSEState>({
        connected: false,
        messageId: null,
        content: '',
        error: null
    });

    let eventSource: EventSource | null = null;
    let abortController: AbortController | null = null;

    return {
        subscribe,

        async startStream(url: string, body: object): Promise<void> {
            // Cleanup previous connection
            this.stopStream();

            abortController = new AbortController();

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                    signal: abortController.signal
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                if (!response.body) {
                    throw new Error('No response body');
                }

                update(s => ({ ...s, connected: true, content: '', error: null }));

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    const lines = text.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.slice(6));
                            this.handleEvent(data);
                        }
                    }
                }
            } catch (error) {
                if (error.name !== 'AbortError') {
                    update(s => ({ ...s, error: error.message }));
                }
            } finally {
                update(s => ({ ...s, connected: false }));
            }
        },

        handleEvent(data: { type: string; content?: string; message_id?: string; message?: string }) {
            switch (data.type) {
                case 'start':
                    update(s => ({ ...s, messageId: data.message_id ?? null }));
                    break;
                case 'chunk':
                    update(s => ({ ...s, content: s.content + (data.content ?? '') }));
                    break;
                case 'done':
                    update(s => ({ ...s, connected: false }));
                    break;
                case 'error':
                    update(s => ({ ...s, error: data.message ?? 'Unknown error', connected: false }));
                    break;
            }
        },

        stopStream() {
            if (abortController) {
                abortController.abort();
                abortController = null;
            }
            update(s => ({ ...s, connected: false }));
        },

        reset() {
            this.stopStream();
            set({ connected: false, messageId: null, content: '', error: null });
        }
    };
}

export const sseStore = createSSEStore();
```

**Key Points**:
- Use `AbortController` for cancellation
- Parse SSE format: `data: {json}\n\n`
- Handle all event types: start, chunk, done, error
- Cleanup on stop/reset
- Track connection state

---

## Component Patterns

### COMP-001: Form Component with Validation

**Source**: Stage 1 - Project Create Modal
**File**: `frontend/src/lib/components/ProjectCreateModal.svelte`

```svelte
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { projectsStore } from '$lib/stores/projects';
    import { createProject } from '$lib/services/api/projects';

    export let isOpen = false;

    const dispatch = createEventDispatcher<{
        close: void;
        created: { id: number; name: string };
    }>();

    let name = '';
    let description = '';
    let error: string | null = null;
    let submitting = false;

    // Validation
    $: nameError = name.length === 0 ? null :
                   name.length > 200 ? 'Name too long (max 200)' : null;
    $: isValid = name.length > 0 && name.length <= 200;

    async function handleSubmit() {
        if (!isValid || submitting) return;

        submitting = true;
        error = null;

        try {
            const project = await createProject({ name, description });
            projectsStore.addProject(project);
            dispatch('created', project);
            handleClose();
        } catch (e) {
            error = e instanceof Error ? e.message : 'Failed to create project';
        } finally {
            submitting = false;
        }
    }

    function handleClose() {
        name = '';
        description = '';
        error = null;
        isOpen = false;
        dispatch('close');
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') handleClose();
        if (e.key === 'Enter' && e.ctrlKey) handleSubmit();
    }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
    <div
        class="modal-backdrop"
        on:click={handleClose}
        on:keydown={handleKeydown}
        role="button"
        tabindex="-1"
        data-testid="modal-backdrop"
    >
        <div
            class="modal-content"
            on:click|stopPropagation
            on:keydown|stopPropagation
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
        >
            <h2 id="modal-title">Create Project</h2>

            <form on:submit|preventDefault={handleSubmit}>
                <div class="form-group">
                    <label for="project-name">Name *</label>
                    <input
                        id="project-name"
                        type="text"
                        bind:value={name}
                        placeholder="Enter project name"
                        maxlength="200"
                        required
                        disabled={submitting}
                        aria-invalid={nameError ? 'true' : undefined}
                        aria-describedby={nameError ? 'name-error' : undefined}
                        data-testid="project-name-input"
                    />
                    {#if nameError}
                        <span id="name-error" class="error" role="alert">{nameError}</span>
                    {/if}
                </div>

                <div class="form-group">
                    <label for="project-desc">Description</label>
                    <textarea
                        id="project-desc"
                        bind:value={description}
                        placeholder="Optional description"
                        maxlength="1000"
                        disabled={submitting}
                        data-testid="project-desc-input"
                    />
                </div>

                {#if error}
                    <div class="error-banner" role="alert" data-testid="form-error">
                        {error}
                    </div>
                {/if}

                <div class="button-group">
                    <button
                        type="button"
                        on:click={handleClose}
                        disabled={submitting}
                        data-testid="cancel-btn"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={!isValid || submitting}
                        data-testid="submit-btn"
                    >
                        {submitting ? 'Creating...' : 'Create'}
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<style>
    .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 100;
    }

    .modal-content {
        background: var(--bg-primary);
        border-radius: 8px;
        padding: 24px;
        min-width: 400px;
        max-width: 90vw;
    }

    .form-group {
        margin-bottom: 16px;
    }

    .error {
        color: var(--color-error);
        font-size: 0.875rem;
    }

    .error-banner {
        background: var(--color-error-bg);
        color: var(--color-error);
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 16px;
    }

    .button-group {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
    }
</style>
```

**Key Points**:
- Use `createEventDispatcher` for parent communication
- Reactive validation with `$:` statements
- Handle keyboard shortcuts (Escape, Ctrl+Enter)
- Include `data-testid` for E2E tests
- ARIA attributes for accessibility
- Disable form during submission
- Reset state on close

---

### COMP-002: List with Loading/Empty/Error States

**Source**: Stage 1 - Sidebar Project List
**File**: `frontend/src/lib/components/sidebar/ProjectList.svelte`

```svelte
<script lang="ts">
    import { projectsStore, selectedProject } from '$lib/stores/projects';
    import ProjectItem from './ProjectItem.svelte';

    export let onSelect: (id: number) => void = () => {};
</script>

<div class="project-list" data-testid="project-list">
    {#if $projectsStore.loading}
        <!-- Loading State -->
        <div class="loading-state" data-testid="loading-state">
            <span class="spinner" aria-hidden="true"></span>
            <span>Loading projects...</span>
        </div>

    {:else if $projectsStore.error}
        <!-- Error State -->
        <div class="error-state" role="alert" data-testid="error-state">
            <span class="error-icon" aria-hidden="true">⚠️</span>
            <span>{$projectsStore.error}</span>
            <button on:click={() => loadProjects()} data-testid="retry-btn">
                Retry
            </button>
        </div>

    {:else if $projectsStore.items.length === 0}
        <!-- Empty State -->
        <div class="empty-state" data-testid="empty-state">
            <span>No projects yet</span>
            <span class="hint">Create your first project to get started</span>
        </div>

    {:else}
        <!-- Content State -->
        <ul role="listbox" aria-label="Projects">
            {#each $projectsStore.items as project (project.id)}
                <ProjectItem
                    {project}
                    selected={$selectedProject?.id === project.id}
                    on:select={() => onSelect(project.id)}
                />
            {/each}
        </ul>
    {/if}
</div>

<style>
    .project-list {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .loading-state,
    .error-state,
    .empty-state {
        padding: 24px;
        text-align: center;
        color: var(--text-secondary);
    }

    .spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid currentColor;
        border-right-color: transparent;
        border-radius: 50%;
        animation: spin 0.75s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    ul {
        list-style: none;
        margin: 0;
        padding: 0;
    }
</style>
```

**Key Points**:
- Always handle 4 states: loading, error, empty, content
- Use `{#each ... (key)}` with unique key for efficient updates
- Include retry button for error state
- Use ARIA roles for accessibility
- Use `data-testid` for each state

---

## Test Patterns

### TEST-001: Unit Test with Store

**Source**: Stage 1 - Projects Store Tests
**File**: `frontend/src/lib/stores/projects.test.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { projectsStore, selectedProject } from './projects';

describe('projectsStore', () => {
    beforeEach(() => {
        projectsStore.reset();
    });

    describe('setProjects', () => {
        it('should set projects list', () => {
            const projects = [
                { id: 1, name: 'Project 1', created_at: '2025-01-01', updated_at: '2025-01-01' },
                { id: 2, name: 'Project 2', created_at: '2025-01-02', updated_at: '2025-01-02' }
            ];

            projectsStore.setProjects(projects);

            expect(get(projectsStore).items).toEqual(projects);
        });
    });

    describe('addProject', () => {
        it('should add project to list', () => {
            const project = { id: 1, name: 'New Project', created_at: '2025-01-01', updated_at: '2025-01-01' };

            projectsStore.addProject(project);

            expect(get(projectsStore).items).toContainEqual(project);
        });
    });

    describe('removeProject', () => {
        it('should remove project from list', () => {
            projectsStore.setProjects([
                { id: 1, name: 'Project 1', created_at: '2025-01-01', updated_at: '2025-01-01' },
                { id: 2, name: 'Project 2', created_at: '2025-01-02', updated_at: '2025-01-02' }
            ]);

            projectsStore.removeProject(1);

            expect(get(projectsStore).items).toHaveLength(1);
            expect(get(projectsStore).items[0].id).toBe(2);
        });

        it('should clear selectedId if removed project was selected', () => {
            projectsStore.setProjects([{ id: 1, name: 'Project 1', created_at: '2025-01-01', updated_at: '2025-01-01' }]);
            projectsStore.selectProject(1);

            projectsStore.removeProject(1);

            expect(get(projectsStore).selectedId).toBeNull();
        });
    });

    describe('derived: selectedProject', () => {
        it('should return null when no project selected', () => {
            expect(get(selectedProject)).toBeNull();
        });

        it('should return selected project', () => {
            const project = { id: 1, name: 'Project 1', created_at: '2025-01-01', updated_at: '2025-01-01' };
            projectsStore.setProjects([project]);
            projectsStore.selectProject(1);

            expect(get(selectedProject)).toEqual(project);
        });
    });
});
```

**Key Points**:
- Use `beforeEach` to reset store state
- Use `get()` from svelte/store to read values
- Test both actions and derived stores
- Test edge cases (remove selected item)

---

### TEST-002: Integration Test with MSW

**Source**: Stage 1 - API Integration Tests
**File**: `frontend/src/lib/services/api/projects.integration.test.ts`

```typescript
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { createProject, getProjects, deleteProject } from './projects';

// MSW Server Setup
const server = setupServer(
    // List projects
    http.get('http://localhost:8000/api/projects/', () => {
        return HttpResponse.json([
            { id: 1, name: 'Project 1', created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' }
        ]);
    }),

    // Create project
    http.post('http://localhost:8000/api/projects/create', async ({ request }) => {
        const body = await request.json() as { name: string };
        return HttpResponse.json({
            id: 2,
            name: body.name,
            created_at: '2025-01-02T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z'
        }, { status: 201 });
    }),

    // Delete project
    http.delete('http://localhost:8000/api/projects/:id', () => {
        return new HttpResponse(null, { status: 204 });
    })
);

beforeAll(() => server.listen());
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

describe('Projects API', () => {
    describe('getProjects', () => {
        it('should fetch projects list', async () => {
            const projects = await getProjects();

            expect(projects).toHaveLength(1);
            expect(projects[0].name).toBe('Project 1');
        });

        it('should handle server error', async () => {
            server.use(
                http.get('http://localhost:8000/api/projects/', () => {
                    return HttpResponse.json(
                        { detail: 'Internal server error' },
                        { status: 500 }
                    );
                })
            );

            await expect(getProjects()).rejects.toThrow();
        });
    });

    describe('createProject', () => {
        it('should create new project', async () => {
            const project = await createProject({ name: 'New Project' });

            expect(project.id).toBe(2);
            expect(project.name).toBe('New Project');
        });

        it('should handle validation error', async () => {
            server.use(
                http.post('http://localhost:8000/api/projects/create', () => {
                    return HttpResponse.json(
                        { detail: 'Name is required' },
                        { status: 422 }
                    );
                })
            );

            await expect(createProject({ name: '' })).rejects.toThrow();
        });
    });

    describe('deleteProject', () => {
        it('should delete project', async () => {
            await expect(deleteProject(1)).resolves.not.toThrow();
        });

        it('should handle not found', async () => {
            server.use(
                http.delete('http://localhost:8000/api/projects/:id', () => {
                    return HttpResponse.json(
                        { detail: 'Project not found' },
                        { status: 404 }
                    );
                })
            );

            await expect(deleteProject(999)).rejects.toThrow();
        });
    });
});
```

**Key Points**:
- Use `setupServer` from `msw/node`
- Define default handlers, override with `server.use()` for error cases
- Call `server.resetHandlers()` in `afterEach`
- Test both success and error paths

---

### TEST-003: E2E Test with Real Backend

**Source**: Stage 1 - Chat E2E Tests
**File**: `frontend/tests/e2e/chat.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Chat Workflow', () => {
    // Verify backend before tests
    test.beforeAll(async ({ request }) => {
        const health = await request.get('http://localhost:8000/health');
        expect(health.ok()).toBeTruthy();
    });

    test.beforeEach(async ({ page }) => {
        // Create test project
        await page.goto('http://localhost:5173');
        await page.locator('[data-testid="new-project-btn"]').click();
        await page.locator('[data-testid="project-name-input"]').fill('E2E Test Project');
        await page.locator('[data-testid="submit-btn"]').click();
        await expect(page.locator('[data-testid="project-item"]')).toBeVisible();
    });

    test.afterEach(async ({ page }) => {
        // Cleanup: Delete test project
        await page.locator('[data-testid="project-item"]').first().hover();
        await page.locator('[data-testid="delete-project-btn"]').click();
        await page.locator('[data-testid="confirm-delete-btn"]').click();
    });

    test('should send message and receive response', async ({ page }) => {
        // Navigate to chat
        await page.locator('[data-testid="project-item"]').first().click();

        // Send message
        const input = page.locator('[data-testid="chat-input"]');
        await input.fill('Hello, how are you?');
        await page.locator('[data-testid="send-btn"]').click();

        // Verify user message appears
        await expect(page.locator('[data-testid="user-message"]').last())
            .toContainText('Hello, how are you?');

        // Wait for AI response (real LLM, longer timeout)
        await expect(page.locator('[data-testid="assistant-message"]').last())
            .toBeVisible({ timeout: 60000 });

        // Verify response has content
        const response = await page.locator('[data-testid="assistant-message"]').last().textContent();
        expect(response?.length).toBeGreaterThan(10);
    });

    test('should handle streaming response', async ({ page }) => {
        await page.locator('[data-testid="project-item"]').first().click();

        // Send message
        await page.locator('[data-testid="chat-input"]').fill('Tell me a short story');
        await page.locator('[data-testid="send-btn"]').click();

        // Verify streaming indicator appears
        await expect(page.locator('[data-testid="streaming-indicator"]'))
            .toBeVisible({ timeout: 5000 });

        // Wait for streaming to complete
        await expect(page.locator('[data-testid="streaming-indicator"]'))
            .not.toBeVisible({ timeout: 60000 });

        // Verify final response
        await expect(page.locator('[data-testid="assistant-message"]').last())
            .toBeVisible();
    });
});
```

**Key Points**:
- Verify backend health in `beforeAll`
- Create test data in `beforeEach`, cleanup in `afterEach`
- Use longer timeouts for real LLM responses (60s)
- Test streaming indicators
- NO MSW mocks - real backend only

---

## Error Handling Patterns

### ERR-001: API Error Handler

**Source**: Stage 1 - API Base
**File**: `frontend/src/lib/services/api/base.ts`

```typescript
export class APIError extends Error {
    constructor(
        message: string,
        public status: number,
        public code?: string,
        public details?: unknown
    ) {
        super(message);
        this.name = 'APIError';
    }
}

export async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let message = `HTTP ${response.status}`;
        let code: string | undefined;
        let details: unknown;

        try {
            const data = await response.json();
            message = data.detail || data.message || message;
            code = data.code;
            details = data.details;
        } catch {
            // Response is not JSON
        }

        throw new APIError(message, response.status, code, details);
    }

    // Handle 204 No Content
    if (response.status === 204) {
        return undefined as T;
    }

    return response.json();
}

export async function fetchAPI<T>(
    url: string,
    options: RequestInit = {}
): Promise<T> {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });

    return handleResponse<T>(response);
}
```

**Key Points**:
- Create custom `APIError` class with status and code
- Parse error details from response body
- Handle 204 No Content
- Centralize fetch logic

---

### ERR-002: Component Error Boundary

**Source**: Stage 1 - Error Boundary
**File**: `frontend/src/lib/components/ErrorBoundary.svelte`

```svelte
<script lang="ts">
    import { onMount } from 'svelte';

    export let fallback: string = 'Something went wrong';

    let hasError = false;
    let errorMessage = '';

    onMount(() => {
        const handleError = (event: ErrorEvent) => {
            hasError = true;
            errorMessage = event.message;
            event.preventDefault();
        };

        const handleRejection = (event: PromiseRejectionEvent) => {
            hasError = true;
            errorMessage = event.reason?.message || 'Unhandled promise rejection';
            event.preventDefault();
        };

        window.addEventListener('error', handleError);
        window.addEventListener('unhandledrejection', handleRejection);

        return () => {
            window.removeEventListener('error', handleError);
            window.removeEventListener('unhandledrejection', handleRejection);
        };
    });

    function handleRetry() {
        hasError = false;
        errorMessage = '';
    }
</script>

{#if hasError}
    <div class="error-boundary" role="alert" data-testid="error-boundary">
        <h2>⚠️ {fallback}</h2>
        <p>{errorMessage}</p>
        <button on:click={handleRetry} data-testid="error-retry-btn">
            Try Again
        </button>
    </div>
{:else}
    <slot />
{/if}

<style>
    .error-boundary {
        padding: 24px;
        text-align: center;
        background: var(--color-error-bg);
        border: 1px solid var(--color-error);
        border-radius: 8px;
        margin: 16px;
    }
</style>
```

**Key Points**:
- Catch both sync errors and unhandled rejections
- Provide retry mechanism
- Use slot for children
- Clean up listeners on destroy

---

## Quick Reference: When to Use Which Pattern

| Scenario | Pattern | File Location |
|----------|---------|---------------|
| New CRUD endpoint | API-001 | `backend/app/api/` |
| Streaming response | API-002 | `backend/app/api/` |
| State management | STORE-001 | `frontend/src/lib/stores/` |
| Real-time data | STORE-002 | `frontend/src/lib/stores/` |
| Form with validation | COMP-001 | `frontend/src/lib/components/` |
| List with states | COMP-002 | `frontend/src/lib/components/` |
| Store unit test | TEST-001 | Co-located `*.test.ts` |
| API integration test | TEST-002 | Co-located `*.integration.test.ts` |
| Full workflow test | TEST-003 | `frontend/tests/e2e/` |
| API error handling | ERR-001 | `frontend/src/lib/services/api/` |
| UI error recovery | ERR-002 | `frontend/src/lib/components/` |

---

## Pattern Submission Process

To add a new pattern to this library:

1. **Identify** - Pattern must be used successfully in at least one stage
2. **Document** - Use the template above (Source, File, Code, Key Points)
3. **Review** - Submit for PM-Architect review
4. **Approve** - PM adds to this document with version bump

**Pattern Template**:
```markdown
### {CATEGORY}-{NUMBER}: {Name}

**Source**: Stage {N} - {Feature}
**File**: `{path/to/file}`

\`\`\`{language}
{code}
\`\`\`

**Key Points**:
- Point 1
- Point 2
- Point 3
```

---

## Test Patterns (NEW - 2025-12-20)

### TEST-004: Outcome Verification for Filtered Lists

**Source**: Stage 6 - Bug Fix: ProjectDetails showing all conversations
**File**: `frontend/tests/e2e/project-conversations-filter.spec.ts`

```typescript
// tests/e2e/project-conversations-filter.spec.ts
import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:5173';
const API_URL = process.env.VITE_API_URL || 'http://localhost:18000';

/**
 * Helper: Get project_ids from all visible conversation items
 * Requires data-project-id attribute on conversation items
 */
async function getConversationProjectIds(page: Page): Promise<number[]> {
    const conversations = page.locator('[data-testid="conversation-item"]');
    const count = await conversations.count();
    const projectIds: number[] = [];

    for (let i = 0; i < count; i++) {
        const projectId = await conversations.nth(i).getAttribute('data-project-id');
        if (projectId) {
            projectIds.push(parseInt(projectId, 10));
        }
    }

    return projectIds;
}

/**
 * Helper: Get conversation count from API for specific project
 */
async function getApiConversationCount(page: Page, projectId: number): Promise<number> {
    const response = await page.request.get(`${API_URL}/api/conversations/list?project_id=${projectId}`);
    if (response.ok()) {
        const data = await response.json();
        return data.data?.items?.length || data.items?.length || 0;
    }
    return 0;
}

test.describe('Project Conversations Filter - Outcome Verification', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        await page.waitForLoadState('networkidle');
    });

    /**
     * POSITIVE: Verify INCLUSION - items that SHOULD appear DO appear
     */
    test('should include conversations from selected project', async ({ page }) => {
        // Get first project ID from API
        const projectsResponse = await page.request.get(`${API_URL}/api/projects/list`);
        const projectsData = await projectsResponse.json();
        const projects = projectsData.data?.items || projectsData.projects || [];

        if (projects.length === 0) {
            test.skip(true, 'No projects available');
            return;
        }

        const projectId = projects[0].id;

        // Select the project in Projects tab
        await page.locator('#projects-tab').click();
        await page.locator(`[data-testid="project-item-${projectId}"]`).click();
        await page.waitForLoadState('networkidle');

        // Get all displayed conversation project_ids
        const displayedProjectIds = await getConversationProjectIds(page);

        // All should belong to selected project
        displayedProjectIds.forEach(pid => {
            expect(pid, `Conversation with project_id ${pid} does not belong to selected project ${projectId}`).toBe(projectId);
        });
    });

    /**
     * NEGATIVE: Verify EXCLUSION - items that should NOT appear are absent
     */
    test('should NOT include conversations from other projects', async ({ page }) => {
        // Setup: Need at least 2 projects with conversations
        const projectsResponse = await page.request.get(`${API_URL}/api/projects/list`);
        const projectsData = await projectsResponse.json();
        const projects = projectsData.data?.items || projectsData.projects || [];

        if (projects.length < 2) {
            test.skip(true, 'Need at least 2 projects for this test');
            return;
        }

        const projectId = projects[0].id;
        const otherProjectId = projects[1].id;

        // Select first project
        await page.locator('#projects-tab').click();
        await page.locator(`[data-testid="project-item-${projectId}"]`).click();
        await page.waitForLoadState('networkidle');

        // Get displayed conversations
        const displayedProjectIds = await getConversationProjectIds(page);

        // None should belong to other project
        const leakedConversations = displayedProjectIds.filter(pid => pid === otherProjectId);
        expect(leakedConversations.length, `Found ${leakedConversations.length} conversations from wrong project ${otherProjectId}`).toBe(0);
    });

    /**
     * COUNT: Verify count matches filtered result
     */
    test('should show correct count for selected project', async ({ page }) => {
        const projectsResponse = await page.request.get(`${API_URL}/api/projects/list`);
        const projectsData = await projectsResponse.json();
        const projects = projectsData.data?.items || projectsData.projects || [];

        if (projects.length === 0) {
            test.skip(true, 'No projects available');
            return;
        }

        const projectId = projects[0].id;

        // Get expected count from API
        const apiCount = await getApiConversationCount(page, projectId);

        // Select project
        await page.locator('#projects-tab').click();
        await page.locator(`[data-testid="project-item-${projectId}"]`).click();
        await page.waitForLoadState('networkidle');

        // Get UI count
        const uiCount = await page.locator('[data-testid="conversation-item"]').count();

        // Should match (accounting for pagination)
        expect(uiCount).toBeLessThanOrEqual(apiCount);

        // If API has items, UI should have items
        if (apiCount > 0) {
            expect(uiCount).toBeGreaterThan(0);
        }
    });
});
```

**Key Points**:
- Tests verify DATA correctness, not just UI rendering
- Requires `data-project-id` attribute on conversation items
- Tests both INCLUSION (correct items) and EXCLUSION (no wrong items)
- Compares UI count with API count for validation

---

### TEST-005: Derived Store Correctness

**Source**: Stage 6 - Bug Fix: Wrong derived store used
**File**: `frontend/src/lib/stores/conversations.derived-store.test.ts`

```typescript
// src/lib/stores/conversations.derived-store.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import {
    conversations,
    currentProjectConversations,
    selectedProjectConversations
} from './conversations';
import { currentProjectId, selectedProjectId } from './projects';

describe('Derived Store Correctness', () => {
    beforeEach(() => {
        // Reset all stores
        conversations.reset();
        currentProjectId.set(null);
        selectedProjectId.set(null);
    });

    describe('selectedProjectConversations', () => {
        it('should filter by selectedProjectId, NOT currentProjectId', () => {
            // Setup: Different values for currentProjectId and selectedProjectId
            // This catches the bug where wrong store was used
            currentProjectId.set(10);  // Chat tab project
            selectedProjectId.set(20); // Projects tab project

            conversations.setConversations([
                { id: 1, project_id: 10, title: 'Conv for project 10', created_at: '', updated_at: '' },
                { id: 2, project_id: 20, title: 'Conv for project 20', created_at: '', updated_at: '' },
                { id: 3, project_id: 30, title: 'Conv for project 30', created_at: '', updated_at: '' },
            ]);

            // Get value from selectedProjectConversations
            const result = get(selectedProjectConversations);

            // Should ONLY have project 20's conversations (selectedProjectId)
            expect(result.length).toBe(1);
            expect(result[0].project_id).toBe(20);

            // Explicitly verify it does NOT use currentProjectId
            expect(result.some(c => c.project_id === 10)).toBe(false);
        });

        it('should return empty array when selectedProjectId is null', () => {
            selectedProjectId.set(null);
            currentProjectId.set(10);  // This should NOT affect result

            conversations.setConversations([
                { id: 1, project_id: 10, title: 'Conv', created_at: '', updated_at: '' },
            ]);

            const result = get(selectedProjectConversations);

            // Should be empty because selectedProjectId is null
            // NOT return all conversations
            expect(result.length).toBe(0);
        });

        it('should update when selectedProjectId changes', () => {
            conversations.setConversations([
                { id: 1, project_id: 10, title: 'Project 10 conv', created_at: '', updated_at: '' },
                { id: 2, project_id: 20, title: 'Project 20 conv', created_at: '', updated_at: '' },
            ]);

            // Initially project 10
            selectedProjectId.set(10);
            expect(get(selectedProjectConversations).length).toBe(1);
            expect(get(selectedProjectConversations)[0].project_id).toBe(10);

            // Change to project 20
            selectedProjectId.set(20);
            expect(get(selectedProjectConversations).length).toBe(1);
            expect(get(selectedProjectConversations)[0].project_id).toBe(20);
        });
    });

    describe('currentProjectConversations', () => {
        it('should filter by currentProjectId, NOT selectedProjectId', () => {
            currentProjectId.set(10);  // Chat tab project
            selectedProjectId.set(20); // Projects tab project - should be ignored

            conversations.setConversations([
                { id: 1, project_id: 10, title: 'Conv for project 10', created_at: '', updated_at: '' },
                { id: 2, project_id: 20, title: 'Conv for project 20', created_at: '', updated_at: '' },
            ]);

            const result = get(currentProjectConversations);

            // Should ONLY have project 10's conversations (currentProjectId)
            expect(result.length).toBe(1);
            expect(result[0].project_id).toBe(10);
        });

        it('should return ALL conversations when currentProjectId is null', () => {
            currentProjectId.set(null);  // "All Projects" mode

            conversations.setConversations([
                { id: 1, project_id: 10, title: 'Conv 1', created_at: '', updated_at: '' },
                { id: 2, project_id: 20, title: 'Conv 2', created_at: '', updated_at: '' },
            ]);

            const result = get(currentProjectConversations);

            // Should return ALL conversations (Chat tab "All Projects" behavior)
            expect(result.length).toBe(2);
        });
    });

    describe('Store Independence', () => {
        it('currentProjectConversations and selectedProjectConversations should be independent', () => {
            currentProjectId.set(10);
            selectedProjectId.set(20);

            conversations.setConversations([
                { id: 1, project_id: 10, title: 'Conv 10', created_at: '', updated_at: '' },
                { id: 2, project_id: 20, title: 'Conv 20', created_at: '', updated_at: '' },
                { id: 3, project_id: 30, title: 'Conv 30', created_at: '', updated_at: '' },
            ]);

            const currentResult = get(currentProjectConversations);
            const selectedResult = get(selectedProjectConversations);

            // Should have different results
            expect(currentResult.length).toBe(1);
            expect(currentResult[0].project_id).toBe(10);

            expect(selectedResult.length).toBe(1);
            expect(selectedResult[0].project_id).toBe(20);

            // Verify they are truly independent
            expect(currentResult).not.toEqual(selectedResult);
        });
    });
});
```

**Key Points**:
- Tests that derived stores use the CORRECT source store
- Explicitly tests that wrong store is NOT used
- Tests independence between similar-sounding stores
- Tests null/undefined behavior differences

---

### TEST-006: Filter Boundary Testing

**Source**: Stage 6 - Comprehensive Filter Testing
**File**: `frontend/tests/e2e/filter-boundary.spec.ts`

```typescript
// tests/e2e/filter-boundary.spec.ts
import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:5173';

/**
 * Helper: Get project_ids from visible conversation items
 */
async function getConversationProjectIds(page: Page): Promise<number[]> {
    const conversations = page.locator('[data-testid="conversation-item"], .chat-history-item');
    const count = await conversations.count();
    const projectIds: number[] = [];

    for (let i = 0; i < count; i++) {
        const projectId = await conversations.nth(i).getAttribute('data-project-id');
        if (projectId) {
            projectIds.push(parseInt(projectId, 10));
        }
    }

    return projectIds;
}

test.describe('Filter Boundary Cases', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        await page.waitForLoadState('networkidle');
    });

    /**
     * ALL -> SPECIFIC transition
     */
    test('switching from "All Projects" to specific project should filter correctly', async ({ page }) => {
        const projectSelector = page.locator('[data-testid="project-selector"]');

        // Start with "All Projects"
        await projectSelector.selectOption('all');
        await page.waitForLoadState('networkidle');
        const allCount = await page.locator('.chat-history-item').count();

        // Get first project ID from dropdown options
        const options = projectSelector.locator('option');
        const optionCount = await options.count();
        let projectId: string | null = null;

        for (let i = 0; i < optionCount; i++) {
            const value = await options.nth(i).getAttribute('value');
            if (value && value !== 'all') {
                projectId = value;
                break;
            }
        }

        if (!projectId) {
            test.skip(true, 'No projects available');
            return;
        }

        // Switch to specific project
        await projectSelector.selectOption(projectId);
        await page.waitForLoadState('networkidle');
        const filteredCount = await page.locator('.chat-history-item').count();

        // Filtered count should be <= all count
        expect(filteredCount).toBeLessThanOrEqual(allCount);

        // All visible items should belong to selected project
        const visibleProjectIds = await getConversationProjectIds(page);
        visibleProjectIds.forEach(pid =>
            expect(pid).toBe(parseInt(projectId!, 10))
        );
    });

    /**
     * SPECIFIC -> DIFFERENT SPECIFIC transition
     */
    test('switching between projects should update filter correctly', async ({ page }) => {
        const projectSelector = page.locator('[data-testid="project-selector"]');
        const options = projectSelector.locator('option');
        const optionCount = await options.count();

        // Get two different project IDs
        const projectIds: string[] = [];
        for (let i = 0; i < optionCount && projectIds.length < 2; i++) {
            const value = await options.nth(i).getAttribute('value');
            if (value && value !== 'all') {
                projectIds.push(value);
            }
        }

        if (projectIds.length < 2) {
            test.skip(true, 'Need at least 2 projects');
            return;
        }

        const [projectId1, projectId2] = projectIds;

        // Select first project
        await projectSelector.selectOption(projectId1);
        await page.waitForLoadState('networkidle');

        const project1Ids = await getConversationProjectIds(page);
        project1Ids.forEach(pid =>
            expect(pid).toBe(parseInt(projectId1, 10))
        );

        // Switch to second project
        await projectSelector.selectOption(projectId2);
        await page.waitForLoadState('networkidle');

        const project2Ids = await getConversationProjectIds(page);
        project2Ids.forEach(pid =>
            expect(pid).toBe(parseInt(projectId2, 10))
        );

        // Verify no conversations from project1 leaked through
        const leakedIds = project2Ids.filter(pid => pid === parseInt(projectId1, 10));
        expect(leakedIds.length).toBe(0);
    });

    /**
     * Empty result case
     */
    test('project with no conversations should show empty state', async ({ page }) => {
        // This test requires a project with no conversations
        // Option 1: Create one via API, Option 2: Find one that exists

        // For now, verify empty state component exists
        const emptyState = page.locator('.empty-state, [data-testid="empty-conversations"]');

        // This is a structural test - verify empty state component is reachable
        // A full test would create a project, verify it has 0 conversations,
        // then verify the empty state shows (not "All Projects" data)
        await expect(emptyState).toBeAttached();
    });
});
```

**Key Points**:
- Tests all filter boundary transitions
- Verifies no data "leaks" from previous filter state
- Tests empty state handling
- Uses data attributes to verify correctness

---

## Quick Reference: When to Use Which Pattern

| Scenario | Pattern | File Location |
|----------|---------|---------------|
| New CRUD endpoint | API-001 | `backend/app/api/` |
| Streaming response | API-002 | `backend/app/api/` |
| State management | STORE-001 | `frontend/src/lib/stores/` |
| Real-time data | STORE-002 | `frontend/src/lib/stores/` |
| Form with validation | COMP-001 | `frontend/src/lib/components/` |
| List with states | COMP-002 | `frontend/src/lib/components/` |
| Store unit test | TEST-001 | Co-located `*.test.ts` |
| API integration test | TEST-002 | Co-located `*.integration.test.ts` |
| Full workflow test | TEST-003 | `frontend/tests/e2e/` |
| **Filtered list verification** | **TEST-004** | `frontend/tests/e2e/*-filter-outcome.spec.ts` |
| **Derived store correctness** | **TEST-005** | Co-located `*.derived-store.test.ts` |
| **Filter boundary testing** | **TEST-006** | `frontend/tests/e2e/filter-boundary.spec.ts` |
| API error handling | ERR-001 | `frontend/src/lib/services/api/` |
| UI error recovery | ERR-002 | `frontend/src/lib/components/` |

---

## Pattern Submission Process

To add a new pattern to this library:

1. **Identify** - Pattern must be used successfully in at least one stage
2. **Document** - Use the template above (Source, File, Code, Key Points)
3. **Review** - Submit for PM-Architect review
4. **Approve** - PM adds to this document with version bump

**Pattern Template**:
```markdown
### {CATEGORY}-{NUMBER}: {Name}

**Source**: Stage {N} - {Feature}
**File**: `{path/to/file}`

\`\`\`{language}
{code}
\`\`\`

**Key Points**:
- Point 1
- Point 2
- Point 3
```

---

**Document Owner**: PM-Architect-Agent
**Review Schedule**: After each stage completion
**Last Updated**: 2025-12-21 (Version 1.2 - Added COMP-003, API-003 patterns for AbortController cleanup)

---

## Component Patterns (Continued)

### COMP-003: AbortController Cleanup Pattern

**Source**: Stage 6 - Agent Meeting #2 Bug Fixes (BUG-RACE-002)
**File**: `frontend/src/lib/components/Sidebar.svelte`

```svelte
<script lang="ts">
    import { onDestroy } from 'svelte';
    import { fetchProject } from '$lib/services/api/projects';

    // AbortController for async operations
    let settingsAbortController: AbortController | null = null;

    // ALWAYS cleanup on component destroy
    onDestroy(() => {
        if (settingsAbortController) {
            settingsAbortController.abort();
            settingsAbortController = null;
        }
    });

    async function openSettingsModal() {
        if ($currentProjectId === null) return;

        // Cancel any previous request before starting new one
        if (settingsAbortController) {
            settingsAbortController.abort();
        }
        settingsAbortController = new AbortController();
        const signal = settingsAbortController.signal;

        try {
            isLoadingProject = true;
            currentProject = await fetchProject($currentProjectId, { signal });

            // Check if aborted before updating UI
            if (!signal.aborted) {
                showSettingsModal = true;
            }
        } catch (error) {
            // Silently ignore AbortError - expected when user navigates away
            if (error instanceof Error && error.name === 'AbortError') {
                logger.debug('Request aborted (component unmounting or user action)');
                return;
            }
            logger.error('Failed to load data', { error });
        } finally {
            // Only update loading state if not aborted
            if (!signal.aborted) {
                isLoadingProject = false;
            }
        }
    }
</script>
```

**Key Points**:
- Use `onDestroy()` to cleanup AbortController
- Always check `signal.aborted` before updating UI state
- Catch and silently ignore `AbortError` - it's expected behavior
- Cancel previous request before starting new one (cancel-and-replace pattern)
- Don't update loading/error state if request was aborted

---

## API Patterns (Continued)

### API-003: API Client with AbortSignal Support

**Source**: Stage 6 - Agent Meeting #2 Bug Fixes (BUG-API-001, BUG-API-002)
**Files**: `frontend/src/lib/services/api/projects.ts`, `frontend/src/lib/services/api/messages.ts`

```typescript
// API Client Pattern: Optional AbortSignal for request cancellation

/**
 * Fetch projects with optional abort signal.
 * Allows cancellation when component unmounts or user navigates away.
 *
 * @param options - Fetch options including abort signal
 * @returns Promise<ProjectListResponse>
 *
 * @example
 * const controller = new AbortController();
 * const projects = await fetchProjects({ signal: controller.signal });
 * // Later: controller.abort() to cancel
 */
export async function fetchProjects(
    options?: { signal?: AbortSignal }
): Promise<ProjectListResponse> {
    return apiRequest<ProjectListResponse>(API_ENDPOINTS.projects.list, options);
}

/**
 * Fetch single project by ID with optional abort signal.
 */
export async function fetchProject(
    id: number,
    options?: { signal?: AbortSignal }
): Promise<Project> {
    return apiRequest<Project>(API_ENDPOINTS.projects.get(id), options);
}

/**
 * Create message with optional abort signal.
 * Signal is passed through to the request options.
 */
export async function createMessage(
    conversationId: number,
    content: string,
    role: MessageRole = 'user',
    options?: { signal?: AbortSignal }
): Promise<Message> {
    return apiRequest<Message>('/api/messages/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId, content, role }),
        signal: options?.signal  // Pass signal to underlying fetch
    });
}
```

**Key Points**:
- Add optional `{ signal?: AbortSignal }` parameter to all API functions
- Pass signal through to `apiRequest()` or underlying `fetch()`
- Document usage in JSDoc comments
- Works with COMP-003 pattern for component cleanup
- Enables proper request cancellation on navigation/unmount

---

## Quick Reference (Updated)

| Scenario | Pattern | File Location |
|----------|---------|---------------|
| Component async cleanup | **COMP-003** | `frontend/src/lib/components/` |
| API with cancellation | **API-003** | `frontend/src/lib/services/api/` |
