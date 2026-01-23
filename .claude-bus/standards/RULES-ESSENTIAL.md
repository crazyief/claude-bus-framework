# Rules Essential - Quick Reference

**Version**: 1.0 | **Effective Date**: 2025-12-21
**Source**: Condensed from CODING-ARCHITECTURE-RULES.md v2.3 (28K tokens → ~8K tokens)

> For detailed code examples, see full version: `CODING-ARCHITECTURE-RULES.md`

---

## Quick Pre-Flight Checklist

```typescript
// Most Common Bug - Svelte Store Syntax
$selectedProjectId.set(123)     // ❌ WRONG - "set is not a function"
selectedProjectId.set(123)      // ✅ CORRECT - Use store object, not $ prefix

// Contract Compliance
fetch('/api/projects/get-all')  // ❌ WRONG - Inventing endpoint
fetch('/api/projects/')         // ✅ CORRECT - Match o3 contract

// Database Selection
// SQLite: Projects, Conversations, Messages, Users
// Neo4j: Entity relationships, Knowledge graphs
// ChromaDB: Embeddings, Vector search
```

---

## Coding Rules Summary

| Rule | Name | Limit/Requirement | Severity |
|------|------|-------------------|----------|
| **C1** | File Size Limits | `*.svelte` ≤500, `*.ts/*.py` ≤400 lines | BLOCKING |
| **C2** | Function Size | ≤50 lines, nesting ≤3, complexity ≤10 | HIGH |
| **C3** | Naming Conventions | snake_case (Python), camelCase (TS), PascalCase (components) | LOW |
| **C4** | Import Organization | External → Internal → Relative, blank lines between | LOW |
| **C5** | Error Handling | Structured response, match o9 contract | HIGH |
| **C6** | No Console in Prod | Use logger or `import.meta.env.DEV` check | HIGH |
| **C7** | TypeScript Strictness | No `any`, strict mode enabled | HIGH |
| **C8** | Async/Await Patterns | No blocking calls, always await, handle errors | HIGH |
| **C9** | Svelte Reactivity | `$store = [...$store, item]` not `$store.push()` | HIGH |
| **C10** | API Response Schema | `{data, meta}` or `{error, meta}` format | HIGH |
| **C11** | Pydantic Validation | All FastAPI request/response use Pydantic models | HIGH |
| **C12** | FastAPI Depends | Use `Depends()` for injection, not manual instantiation | MEDIUM |
| **C13** | Accessibility | Keyboard nav, ARIA labels, 4.5:1 contrast | HIGH |
| **C14** | Documentation | `*.py` ≥20%, `*.ts` ≥15%, RAG ≥30% comments | MEDIUM |
| **C15** | Bundle Optimization | Initial JS ≤60KB gzip, lazy load heavy libs | HIGH |
| **C16** | SvelteKit Patterns | Use `+page.server.ts` for data loading | MEDIUM |
| **C17** | Store Cleanup | Manual `.subscribe()` MUST call unsubscribe in `onDestroy` | MEDIUM |
| **C18** | TailwindCSS | Utility-first, avoid `@apply` in components | LOW |
| **C19** | File Upload Security | MIME validation, size limits, dangerous pattern scan | CRITICAL |
| **C20-C27** | Svelte Lifecycle | Timer/interval cleanup, event listener cleanup, fetch abort | HIGH |

---

## Architecture Rules Summary

| Rule | Name | Requirement |
|------|------|-------------|
| **A1** | Layered Architecture | Presentation → Service → Repository → Data |
| **A2** | Database Selection | SQLite (structured), Neo4j (graphs), ChromaDB (vectors) |
| **A3** | Contract Compliance | Match Phase 1 contracts (o3 API, o7 State, o8 UI, o9 Validation) |
| **A4** | State Management | Global stores → Feature stores → Component state |
| **A5** | API Client Structure | All calls through `base.ts` wrapper, centralized CSRF |
| **A6** | Component Composition | ≤200 lines per sub-component, single responsibility |
| **A7** | Dependency Injection | Inject dependencies, don't hardcode |
| **A8** | SSE/WebSocket | Always cleanup in `onDestroy` |
| **A9** | Co-location | Tests, types, services co-located with features |
| **A10** | Migration Protocol | Create new migrations, never edit existing |

---

## Security Rules Summary (S1-S8)

| Rule | Name | Severity | Key Points |
|------|------|----------|------------|
| **S1** | Secrets Management | CRITICAL | `.env` in `.gitignore`, Pydantic BaseSettings, never commit secrets |
| **S2** | Input Validation | CRITICAL | Pydantic validators, DOMPurify for HTML, SQLAlchemy ORM |
| **S3** | Rate Limiting | HIGH | CRUD 100/min, LLM 10/min, Upload 20/min, Auth 5/min |
| **S4** | Security Headers | HIGH | X-Content-Type-Options, X-Frame-Options, CSP |
| **S5** | CSRF Protection | HIGH | Double-submit cookie, SameSite=Strict |
| **S6** | Authentication | CRITICAL | JWT, httponly cookies, 15min access / 7day refresh |
| **S7** | Authorization | CRITICAL | Verify ownership on EVERY request, not just UI |
| **S8** | Sensitive Data | HIGH | Never log passwords/tokens, mask PII, hash with bcrypt |

---

## RAG Rules Summary (R1-R9)

| Rule | Name | Recommended |
|------|------|-------------|
| **R1** | Chunking | 1200 tokens, 100 overlap, semantic strategy |
| **R2** | Embedding | `BAAI/bge-m3` or `text-embedding-3-large`, consistent dimension |
| **R3** | Retrieval Mode | `hybrid` (default), `mix` with reranker |
| **R4** | Token Budget | 30K total, 6K entity, 8K relation |
| **R5** | Graph Storage | Neo4JStorage for production |
| **R6** | Vector Storage | ChromaVectorDBStorage |
| **R7** | Reranking | `BAAI/bge-reranker-v2-m3`, adds 10-20% accuracy |
| **R8** | Doc Processing | ≥95% OCR accuracy, quality checks before indexing |
| **R9** | Retrieval Thresholds | top_k=15, similarity≥0.7, "I cannot answer" if insufficient |

---

## Backend Infrastructure Rules

| Rule | Name | Key Points |
|------|------|------------|
| **T1** | Transaction Management | Context managers, auto-rollback on exception |
| **L1** | Logging Standards | Structured JSON, log levels, mask sensitive data |
| **L2** | Audit Logging | IEC 62443 compliance, append-only, tamper-evident |

---

## Phase Gate Checklist

### Phase 2 → 3 (CODING-ARCHITECTURE-RULES.md)

| Check | Rule | Severity |
|-------|------|----------|
| File size limits | C1 | CRITICAL |
| Contract compliance | A3 | CRITICAL |
| Security rules | S1-S8 | CRITICAL |
| Audit logging | L2 | CRITICAL |
| File upload security | C19 | CRITICAL |
| TypeScript strict | C7 | HIGH |
| No console.log | C6 | HIGH |
| Pydantic validation | C11 | HIGH |
| Accessibility | C13 | HIGH |

### Phase 3 → 4 (CODING + TESTING-RULES)

| Check | Source | Severity |
|-------|--------|----------|
| Layered architecture | A1 | CRITICAL |
| Database selection | A2 | CRITICAL |
| Coverage ≥70% | TESTING-RULES | CRITICAL |
| Test pyramid compliant | TESTING-RULES | HIGH |
| Regression tests pass | TESTING-RULES | CRITICAL |
| A11y E2E tests pass | TESTING-RULES | HIGH |

### Phase 4 → 5 (TESTING-RULES)

| Check | Severity |
|-------|----------|
| All E2E tests passing | CRITICAL |
| Performance (LCP ≤2.5s, FCP ≤1.8s, CLS ≤0.1) | HIGH |
| Bundle size ≤60KB gzip | HIGH |
| A11y scan passing | HIGH |

---

## Common Mistakes Quick List

### Svelte Mistakes

```typescript
// ❌ $store.set() - Use store.set()
// ❌ $store.push() - Use $store = [...$store, item]
// ❌ Manual subscribe without cleanup
// ❌ Missing onDestroy for intervals/SSE
// ❌ Direct fetch in component - Use API client
```

### Backend Mistakes

```python
# ❌ dict instead of Pydantic model
# ❌ Manual db session without cleanup
# ❌ No ownership check in endpoints
# ❌ Missing audit logging
# ❌ Hardcoded secrets
```

### Security Mistakes

```
❌ Trusting Content-Type header (use magic bytes)
❌ Authorization in UI only (check backend too)
❌ Logging passwords/tokens
❌ GET request modifying state
❌ Missing rate limiting on LLM endpoints
```

---

## Quick Reference Commands

```bash
# Check file sizes
find frontend/src -name "*.svelte" -exec wc -l {} + | sort -n | tail -20
find frontend/src -name "*.ts" -exec wc -l {} + | sort -n | tail -20

# TypeScript strict check
cd frontend && npx tsc --noEmit

# Lint check
cd frontend && npm run lint
cd backend && ruff check .

# Test coverage
cd frontend && npm run test:coverage
```

---

## Document Responsibility

| Question | Answer |
|----------|--------|
| Is my code structured correctly? | CODING-ARCHITECTURE-RULES.md |
| Are my tests sufficient? | TESTING-RULES.md |
| What blocks Phase 2→3? | CODING-ARCHITECTURE-RULES.md only |
| What blocks Phase 3→4? | BOTH documents |
| What blocks Phase 4→5? | TESTING-RULES.md only |

---

## Agent Loading Guide

| Agent | Load This File | Also Load |
|-------|----------------|-----------|
| **All Agents (Phase 2)** | RULES-ESSENTIAL.md | PATTERN-LIBRARY.md |
| **Frontend-Agent** | RULES-ESSENTIAL.md | - |
| **Backend-Agent** | RULES-ESSENTIAL.md | - |
| **QA-Agent (Phase 3)** | RULES-ESSENTIAL.md | TESTING-RULES.md |
| **Full Review** | CODING-ARCHITECTURE-RULES.md | All details needed |

---

*For detailed code examples and full explanations, see `CODING-ARCHITECTURE-RULES.md`*
