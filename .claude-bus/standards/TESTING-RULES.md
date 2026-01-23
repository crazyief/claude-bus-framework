# Testing Rules for GPT-OSS Agents

**Version**: 3.0
**Effective Date**: 2025-12-14
**Status**: MANDATORY - Non-negotiable enforcement

---

## Core Philosophy: Maximize Coverage Depth

**Every hour spent writing tests saves multiple hours of debugging at 2am.**

Don't just test the happy path. For EVERY feature, test:
- ✅ Happy path (feature works correctly)
- ✅ Validation errors (bad input rejected)
- ✅ API errors (400, 401, 403, 404, 500, etc.)
- ✅ Network errors (timeout, connection refused)
- ✅ Edge cases (empty, unicode, large payloads)
- ✅ Recovery (user can continue after error)

See `docs/TESTING-STANDARDS.md` for full details.

---

## Quick Pre-Flight Checklist (Read Before Writing Any Test)

### Svelte Store Syntax (Most Common Bug)
```typescript
// ❌ WRONG - "set is not a function" error
$selectedProjectId.set(123)

// ✅ CORRECT - Use store object, not $ prefix
selectedProjectId.set(123)
```

### Selector Verification
```typescript
// ❌ WRONG - Assumed selector
page.locator('textarea[name="message"]')

// ✅ CORRECT - Verified from MessageInput.svelte line 45
page.locator('textarea.message-textarea')
```

### API Endpoint Verification
```typescript
// ❌ WRONG - Guessed endpoint
page.waitForResponse(r => r.url().includes('/api/chat/chat'))

// ✅ CORRECT - Verified from sse-client.ts
page.waitForResponse(r => r.url().includes('/api/chat/stream'))
```

### Test Self-Sufficiency
```typescript
// ❌ WRONG - Skips if precondition not met
if (projects.length < 2) { test.skip(); return; }

// ✅ CORRECT - Creates its own prerequisites
await createTestProject('Test Project to Delete');
```

### User Message Selector
```typescript
// ❌ WRONG - Too generic
page.locator('.message-content').filter({ hasText: 'test' })

// ✅ CORRECT - UserMessage.svelte line 54
page.locator('.user-message-container[data-role="user"]').filter({ hasText: 'test' })
```

---

## Phase-to-Test Mapping

| Phase | Tests Run | Backend Required | Tools |
|-------|-----------|------------------|-------|
| Phase 1 (Planning) | None | No | N/A |
| Phase 2 (Development) | Write unit tests | No | N/A |
| **Phase 3 (Review)** | Unit + Contract + Integration | **No** | Vitest + Zod + MSW |
| **Phase 4 (Integration)** | E2E + Performance + Visual | **Yes** | Playwright |
| Phase 5 (Manual) | Manual testing | Yes | Human |

### Phase 3 Commands (Mocked)
```bash
npm run test              # Unit tests (Vitest)
npm run test:contract     # Contract tests (Vitest + Zod)
npm run test:integration  # Integration tests (Vitest + MSW)
```

### Phase 4 Commands (Real Backend)
```bash
docker-compose up -d
curl http://localhost:8000/health
npm run test:e2e          # E2E tests (Playwright)
npm run test:component    # Component tests
npm run test:performance  # Performance tests
npm run test:visual       # Visual regression
```

---

## Critical Rules

### Rule 1: Hybrid Testing Approach

**Test Pyramid Distribution**:
- 55-60% unit tests (Vitest)
- 5-10% contract tests (Vitest + Zod)
- 15% integration tests (Vitest + MSW)
- 10% component tests (Playwright)
- 10% E2E tests (Playwright with REAL backend)

**Violations** (BLOCK phase transition):
- Using only Vitest (missing browser testing)
- Test pyramid inverted (more E2E than unit)
- E2E tests using mocks instead of real backend

---

### Rule 1.1: Browser Matrix Selection (2025-12-14)

**Browser selection is project-specific, not one-size-fits-all.**

| Project Type | Desktop Browsers | Mobile Browsers |
|--------------|------------------|-----------------|
| Consumer web app | Chromium, Firefox, Safari | Mobile Chrome, Mobile Safari |
| **Enterprise desktop app** | **Chromium** (+ Firefox in CI) | **None** |
| Mobile-first app | Chromium | All mobile browsers |

**GPT-OSS Configuration** (Enterprise Desktop App):
- **Primary**: Chromium (local + CI)
- **Secondary**: Firefox (CI only - cross-browser validation)
- **Mobile**: Not applicable (desktop-only user base)

**Rationale**:
1. Target users are enterprise cybersecurity professionals on desktops
2. Mobile Safari WebKit cannot disable GPU, causes VIDEO_TDR_FAILURE crashes
3. Mobile testing adds 50%+ execution time with zero business value

**Responsive Testing Alternative**:
Instead of mobile browser projects, use viewport resize in Chromium:
```typescript
// Test mobile viewport without mobile browser
await page.setViewportSize({ width: 375, height: 667 });
```

**Performance Impact**:
```
Before: 1288 tests × 4 browsers = 5152 runs (1-2 hours)
After:  1288 tests × 1 browser  = 1288 runs (20-30 min locally)
Savings: 75% faster, GPU crash eliminated
```

**Decision Reference**: SUPER-AI-REVIEW-2025-12-14-E2E-OPTIMIZATION

---

### Rule 2: Coverage Thresholds

All stages require **≥ 70% coverage**.

**Enforcement**:
- Git commit BLOCKED if coverage < 70%
- Phase 3→4 BLOCKED if coverage < 70%

---

### Rule 3: File Size Limits

| File Type | Limit |
|-----------|-------|
| `*.svelte` | 500 lines |
| `*.ts`/`*.js`/`*.py` | 400 lines |
| `*.test.ts` | 500 lines |
| `*.css`/`*.scss` | 600 lines |

---

### Rule 4: Test Pyramid Compliance

**Valid** (140 tests): Unit 84 (60%), Integration 28 (20%), Component 14 (10%), E2E 14 (10%)

**Invalid**: Unit 20 (14%), E2E 60 (43%) ❌

---

### Rule 5: Performance Thresholds

| Metric | Good |
|--------|------|
| LCP | ≤ 2.5s |
| FCP | ≤ 1.8s |
| CLS | ≤ 0.1 |
| Bundle (gzipped) | ≤ 60 KB |

---

### Rule 6: Visual Regression

Test 5 critical UI states: Empty, Loading, Error, Success, Populated

```bash
npm run test:visual                        # Run tests
npm run test:e2e -- tests/visual/ --update-snapshots  # Update baselines
```

---

### Rule 7: User Journey Testing

Every feature in requirements MUST be accessible from UI:
1. ✅ UI Entry Point Exists (button, link, menu)
2. ✅ Entry Point is Visible
3. ✅ User Can Complete the Flow
4. ✅ Feedback is Provided

**Phase Gate**: BLOCKED if feature lacks UI access

---

### Rule 8: Store Interface Synchronization

When modifying ANY store interface:
1. ✅ Update all `*.test.ts` files using the store
2. ✅ Update all `.svelte` files subscribing
3. ✅ Run `npm run test` before committing
4. ✅ Never use `$store.set()` - use `store.set()`

---

### Rule 9: Regression Testing (Stage 2+)

Phase 3 QA Review MUST:
1. Run ALL previous stage tests: `npm run test`
2. Perform impact analysis if shared files changed
3. Document in QA report

**Phase Gate**: BLOCKED if previous stage tests fail

---

### Rule 10: E2E Must Use Real Backend

| Test Type | Backend |
|-----------|---------|
| Unit | None |
| Integration | MSW mocks |
| Component | MSW mocks |
| **E2E** | **REAL backend** |

**Phase Gate**: BLOCKED if E2E tests contain MSW handlers

---

### Rule 10.1: E2E Test Data Teardown (NEW)

> **Super-AI raised**: No procedure for test data cleanup between E2E runs (risk of test pollution).

**All E2E tests MUST clean up their test data to prevent pollution.**

**Teardown Strategy**:

| Strategy | Use Case | Implementation |
|----------|----------|----------------|
| **Transaction Rollback** | Fast, isolated | Wrap test in transaction, rollback after |
| **Delete by Prefix** | Named test data | Create with `test_` prefix, delete matching |
| **Truncate Tables** | Full reset | Reset all tables between test suites |
| **Snapshot Restore** | Database backup | Restore from known-good state |

**Recommended Pattern** (Delete by Prefix):
```typescript
// tests/e2e/fixtures/test-helpers.ts
import { request } from '@playwright/test';

const TEST_PREFIX = 'e2e_test_';

export async function createTestProject(name: string) {
    const response = await request.post('/api/projects/create', {
        data: { name: `${TEST_PREFIX}${name}_${Date.now()}` }
    });
    return response.json();
}

export async function cleanupTestData() {
    // Delete all test projects (cascades to conversations, messages)
    await request.delete('/api/test/cleanup', {
        data: { prefix: TEST_PREFIX }
    });
}

// Backend endpoint for cleanup (only enabled in test environment)
// backend/app/api/test.py
@app.delete("/api/test/cleanup")
async def cleanup_test_data(prefix: str, db: Session = Depends(get_db)):
    if not settings.TESTING:
        raise HTTPException(403, "Cleanup only allowed in test environment")

    # Delete projects with test prefix (cascades to related data)
    db.query(Project).filter(Project.name.like(f"{prefix}%")).delete()
    db.commit()
    return {"status": "cleaned"}
```

**Playwright Global Teardown**:
```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
    globalSetup: require.resolve('./tests/e2e/global-setup.ts'),
    globalTeardown: require.resolve('./tests/e2e/global-teardown.ts'),
});

// tests/e2e/global-teardown.ts
import { request } from '@playwright/test';

async function globalTeardown() {
    const context = await request.newContext({
        baseURL: 'http://localhost:8000',
    });

    // Clean up all test data
    await context.delete('/api/test/cleanup', {
        data: { prefix: 'e2e_test_' }
    });

    await context.dispose();
}

export default globalTeardown;
```

**Per-Test Cleanup** (afterEach):
```typescript
// tests/e2e/chat-workflow.spec.ts
import { test } from '@playwright/test';
import { createTestProject, cleanupTestData } from './fixtures/test-helpers';

test.describe('Chat Workflow', () => {
    let testProjectId: number;

    test.beforeEach(async () => {
        const project = await createTestProject('chat_test');
        testProjectId = project.id;
    });

    test.afterEach(async () => {
        // Clean up this specific test's data
        await deleteProject(testProjectId);
    });

    test.afterAll(async () => {
        // Final cleanup of any orphaned test data
        await cleanupTestData();
    });

    test('user can send message', async ({ page }) => {
        // Test uses testProjectId
    });
});
```

**Environment Variable**:
```bash
# .env.test
TESTING=true
DATABASE_URL=sqlite:///./data/test.db  # Separate test database
```

**Phase Gate**: QA-Agent verifies teardown hooks present in E2E test files during Phase 3 review.

---

### Rule 11: Phase 4 Prerequisites Check

Before Phase 4, check for permission issues:
```bash
find frontend/node_modules/.vite -user root 2>/dev/null | head -1
```

If found, user must run:
```bash
sudo rm -rf frontend/node_modules/.vite
```

---

### Rule 12: Source Code Reference for E2E Tests

Before writing E2E test:
1. Read component source (`*.svelte`)
2. Extract exact selectors (`data-testid`, CSS classes)
3. Read `docker-compose.yml` for port config
4. Add header documenting source reference

---

### Rule 13: Multi-Root-Cause Discovery

When test fails:
1. Fix visible root cause
2. Re-run test
3. If new failure, GOTO 1
4. Continue until test PASSES
5. Document all root causes

**NEVER**: `test.skip('known issue')` without full investigation

---

### Rule 14: E2E Progress Monitoring

For tests >5 minutes, provide progress updates every 3 minutes:
```
📊 E2E Test Progress (6m elapsed):
├─ Passed: 180/310 (58%)
├─ Failed: 2
└─ ETA: ~9 minutes remaining
```

---

### Rule 15: Accessibility (A11y) Testing (NEW)

> **QA-Agent raised**: WCAG 2.1 AA compliance must be enforced in test pyramid.

**All UI must pass automated accessibility scans.**

**Test Command**:
```bash
npm run test:a11y          # Accessibility E2E tests (Playwright + axe-core)
```

**Setup** (add to package.json):
```json
{
  "scripts": {
    "test:a11y": "playwright test tests/a11y/"
  },
  "devDependencies": {
    "@axe-core/playwright": "^4.8.0"
  }
}
```

**Test Template**:
```typescript
// tests/a11y/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
    test('Home page has no a11y violations', async ({ page }) => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
            .analyze();

        expect(results.violations).toEqual([]);
    });

    test('Chat interface has no a11y violations', async ({ page }) => {
        await page.goto('/project/1');
        await page.waitForLoadState('networkidle');

        const results = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
            .exclude('.third-party-widget')  // Exclude if needed
            .analyze();

        expect(results.violations).toEqual([]);
    });

    test('Keyboard navigation works', async ({ page }) => {
        await page.goto('/');

        // Tab through interactive elements
        await page.keyboard.press('Tab');
        const firstFocused = await page.evaluate(() =>
            document.activeElement?.getAttribute('data-testid')
        );
        expect(firstFocused).toBeTruthy();

        // All buttons should be reachable via keyboard
        const buttons = await page.locator('button:visible').count();
        for (let i = 0; i < buttons; i++) {
            await page.keyboard.press('Tab');
        }
    });
});
```

**Critical Pages to Test**:
| Page | Required Checks |
|------|-----------------|
| Home/Project List | Navigation, buttons, forms |
| Chat Interface | Input, messages, scroll |
| Document Upload | File input, progress, feedback |
| Settings | Forms, toggles, dropdowns |
| Error Pages | Error messages, recovery actions |

**A11y Testing Checklist** (ALL must pass):

| # | Check | Method | Phase |
|---|-------|--------|-------|
| 1 | **Automated Scan** | axe-core via Playwright (`npm run test:a11y`) | Phase 3→4 |
| 2 | **Keyboard Navigation** | Tab through all interactive elements | Phase 3→4 |
| 3 | **Screen Reader Labels** | All icons/buttons have `aria-label` | Phase 3→4 |
| 4 | **Focus Indicators** | Visible `:focus-visible` on all focusable elements | Phase 3→4 |
| 5 | **Color Contrast** | 4.5:1 for normal text, 3:1 for large text | Phase 4→5 |
| 6 | **Form Labels** | All inputs have associated `<label>` | Phase 3→4 |
| 7 | **Error Announcements** | Errors linked via `aria-describedby` | Phase 4→5 |
| 8 | **Skip Links** | "Skip to main content" link present | Phase 4→5 |

**Keyboard Navigation Test Template**:
```typescript
test('All interactive elements reachable via keyboard', async ({ page }) => {
    await page.goto('/');

    // Collect all focusable elements
    const focusableSelectors = 'button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableCount = await page.locator(focusableSelectors).count();

    // Tab through all elements
    for (let i = 0; i < focusableCount; i++) {
        await page.keyboard.press('Tab');
        const focused = await page.evaluate(() => document.activeElement?.tagName);
        expect(focused).toBeTruthy();
    }

    // Verify Enter/Space activates buttons
    await page.locator('button').first().focus();
    await page.keyboard.press('Enter');
    // Assert expected action occurred
});
```

**A11y Workflow** (cross-reference with C13 in CODING-ARCHITECTURE-RULES.md):
```
Phase 2 (Development)
    │
    ├─ Implement C13 accessibility requirements
    │   └─ Keyboard nav, ARIA labels, focus indicators, form labels
    │
    ▼
Phase 3 (QA Review)
    │
    ├─ Run `npm run test:a11y` (automated axe-core scan)
    ├─ Run keyboard navigation tests
    ├─ Code review for C13 compliance
    │
    ▼
Phase 4 (Integration Testing)
    │
    ├─ Full axe-core scan on all pages
    ├─ Color contrast validation
    ├─ Screen reader testing (optional but recommended)
    │
    ▼
Phase 5 (Manual Approval)
```

**Phase Gate Integration**:
- **Phase 3→4**: A11y tests MUST pass (HIGH severity)
- **Phase 4→5**: Full a11y scan with axe-core MUST pass

**Enforcement**: QA-Agent runs `npm run test:a11y` during Phase 3 review.

> **See also**: Rule C13 (Accessibility Requirements) in `CODING-ARCHITECTURE-RULES.md` for implementation guidelines.

---

### Rule 16: RAG Pipeline Testing (NEW)

> **Document-RAG-Agent raised**: RAG-specific testing rules needed for chunking, embedding, and retrieval accuracy.

**All RAG components MUST have dedicated tests.**

**Test Command**:
```bash
npm run test:rag           # RAG-specific tests (Vitest)
```

**Test Categories**:

| Category | Test Type | Coverage Target |
|----------|-----------|-----------------|
| Chunking Logic | Unit | 80% |
| Embedding Consistency | Integration | 70% |
| Retrieval Accuracy | Integration/E2E | 70% |
| Document Processing | Integration | 70% |
| "I Cannot Answer" Protocol | E2E | 100% |

**1. Chunking Tests** (Unit):
```typescript
// src/lib/services/rag/chunking.test.ts
import { describe, it, expect } from 'vitest';
import { chunkDocument } from './chunking';

describe('Document Chunking', () => {
    it('should respect max chunk size (1200 tokens)', () => {
        const longText = 'word '.repeat(2000);  // ~2000 tokens
        const chunks = chunkDocument(longText, { maxTokens: 1200 });

        chunks.forEach(chunk => {
            expect(chunk.tokenCount).toBeLessThanOrEqual(1200);
        });
    });

    it('should maintain overlap between chunks (~100 tokens)', () => {
        const text = 'sentence one. sentence two. sentence three. sentence four.';
        const chunks = chunkDocument(text, { maxTokens: 50, overlap: 10 });

        // Verify overlap exists
        for (let i = 1; i < chunks.length; i++) {
            const prevEnd = chunks[i - 1].text.slice(-50);
            const currStart = chunks[i].text.slice(0, 50);
            expect(prevEnd).toContain(currStart.split(' ')[0]);
        }
    });

    it('should preserve semantic boundaries (sentences/paragraphs)', () => {
        const text = 'First paragraph.\n\nSecond paragraph.';
        const chunks = chunkDocument(text, { maxTokens: 100 });

        // Should not split mid-sentence
        chunks.forEach(chunk => {
            expect(chunk.text).not.toMatch(/\w$/);  // Should end with punctuation
        });
    });

    it('should handle edge cases', () => {
        expect(chunkDocument('')).toEqual([]);
        expect(chunkDocument('   ')).toEqual([]);
        expect(chunkDocument('short')).toHaveLength(1);
    });
});
```

**2. Embedding Consistency Tests** (Integration):
```typescript
// src/lib/services/rag/embedding.integration.test.ts
import { describe, it, expect } from 'vitest';
import { generateEmbedding, EMBEDDING_DIMENSION } from './embedding';

describe('Embedding Generation', () => {
    it('should produce consistent dimension', async () => {
        const texts = ['Hello world', 'Test document', '中文測試'];

        for (const text of texts) {
            const embedding = await generateEmbedding(text);
            expect(embedding.length).toBe(EMBEDDING_DIMENSION);  // e.g., 1536
        }
    });

    it('should produce similar embeddings for similar texts', async () => {
        const text1 = 'IEC 62443 security requirements';
        const text2 = 'IEC 62443 security standards';
        const text3 = 'Cooking recipes for pasta';

        const emb1 = await generateEmbedding(text1);
        const emb2 = await generateEmbedding(text2);
        const emb3 = await generateEmbedding(text3);

        const sim12 = cosineSimilarity(emb1, emb2);
        const sim13 = cosineSimilarity(emb1, emb3);

        expect(sim12).toBeGreaterThan(0.8);  // Similar texts
        expect(sim13).toBeLessThan(0.5);     // Different topics
    });

    it('should reject mismatched dimensions', async () => {
        // If collection was created with different dimension
        await expect(
            storeEmbedding('test', new Array(384).fill(0))  // Wrong dimension
        ).rejects.toThrow('dimension mismatch');
    });
});
```

**3. Retrieval Accuracy Tests** (Integration/E2E):
```typescript
// tests/e2e/rag-retrieval.spec.ts
import { test, expect } from '@playwright/test';

test.describe('RAG Retrieval Accuracy', () => {
    test('should retrieve relevant chunks for specific query', async ({ request }) => {
        // Query for specific IEC 62443 clause
        const response = await request.post('/api/rag/query', {
            data: {
                query: 'What is CR 2.11 in IEC 62443?',
                mode: 'hybrid',
                top_k: 5
            }
        });

        const result = await response.json();

        // At least one chunk should mention CR 2.11
        const relevantChunk = result.chunks.find(c =>
            c.text.includes('CR 2.11') || c.text.includes('2.11')
        );
        expect(relevantChunk).toBeTruthy();

        // Top result should have high similarity
        expect(result.chunks[0].score).toBeGreaterThan(0.7);
    });

    test('should return "I cannot answer" for insufficient data', async ({ request }) => {
        const response = await request.post('/api/rag/query', {
            data: {
                query: 'What is the capital of Mars?',  // Unrelated query
                mode: 'hybrid',
                top_k: 5
            }
        });

        const result = await response.json();

        // Should indicate insufficient data
        expect(result.confidence).toBeLessThan(0.5);
        expect(result.answer).toContain('cannot answer');
    });
});
```

**4. Document Processing Quality Tests** (Integration):
```typescript
// src/lib/services/rag/document-processing.integration.test.ts
describe('Document Processing Quality', () => {
    it('should extract text from PDF with >95% accuracy', async () => {
        const testPdf = await readFile('tests/fixtures/sample-iec62443.pdf');
        const extracted = await extractText(testPdf);

        // Compare against known ground truth
        const groundTruth = await readFile('tests/fixtures/sample-iec62443.txt');
        const accuracy = calculateTextSimilarity(extracted, groundTruth);

        expect(accuracy).toBeGreaterThan(0.95);
    });

    it('should reject files with >10% garbage characters', async () => {
        const corruptedPdf = await readFile('tests/fixtures/corrupted-scan.pdf');

        await expect(processDocument(corruptedPdf)).rejects.toThrow(
            'OCR quality too low'
        );
    });

    it('should handle Unicode and special characters', async () => {
        const unicodeDoc = 'Test: 中文, العربية, emoji 🔒';
        const processed = await processText(unicodeDoc);

        expect(processed).toContain('中文');
        expect(processed).toContain('العربية');
    });
});
```

**5. "I Cannot Answer" Protocol Tests** (E2E):
```typescript
// tests/e2e/rag-cannot-answer.spec.ts
test.describe('"I Cannot Answer" Protocol (R9)', () => {
    const insufficientQueries = [
        'What happened in 2050?',           // Future events
        'Explain quantum computing',        // Out of domain
        'Who is the CEO of Company XYZ?',   // Unknown entity
    ];

    for (const query of insufficientQueries) {
        test(`should refuse to answer: "${query}"`, async ({ request }) => {
            const response = await request.post('/api/chat/stream', {
                data: { message: query, project_id: 1 }
            });

            const result = await response.json();

            expect(result.answer).toMatch(/cannot answer|insufficient|not found/i);
            expect(result.confidence).toBeLessThan(0.7);
            expect(result.reason).toBeTruthy();
        });
    }
});
```

**RAG Test Fixtures Required**:
```
tests/fixtures/
├── sample-iec62443.pdf      # Known PDF for extraction testing
├── sample-iec62443.txt      # Ground truth text
├── corrupted-scan.pdf       # Low-quality OCR test
├── unicode-document.pdf     # Unicode handling test
└── large-document.pdf       # Performance/chunking test (>100 pages)
```

**Phase Gate Integration**:
- **Phase 3→4**: RAG unit/integration tests MUST pass
- **Phase 4→5**: RAG E2E retrieval accuracy tests MUST pass

**Enforcement**: QA-Agent verifies RAG test coverage during Phase 3 review.

> **See also**: Rules R1-R9 (RAG Pipeline Rules) in `CODING-ARCHITECTURE-RULES.md` for implementation guidelines.

---

## Phase Transition Gates

### Phase 2 → Phase 3
- ✅ Git checkpoint created
- ✅ All new code has tests
- ✅ TypeScript compiles

### Phase 3 → Phase 4
- ✅ All tests passing (100%)
- ✅ Coverage ≥ 70%
- ✅ Test pyramid compliant
- ✅ Regression tests pass (Stage 2+)
- ✅ Permission check passed
- ✅ **A11y tests passing (Rule 15)** ← NEW

### Phase 4 → Phase 5
- ✅ All E2E tests passing
- ✅ Visual regression passing
- ✅ Performance tests passing
- ✅ **Full a11y scan passing (axe-core)** ← NEW

### Phase 5 → Stage Complete
- ✅ User manual testing completed
- ✅ User explicit approval
- ✅ Final git checkpoint created

---

## Enforcement Summary

| Rule | Severity | Gate | Action |
|------|----------|------|--------|
| Coverage < 70% | CRITICAL | Phase 3→4 | BLOCK |
| Pyramid violated | HIGH | Phase 3→4 | Refactor |
| Performance fail | HIGH | Phase 4→5 | Fix |
| Feature without UI | CRITICAL | Phase 3→4 | BLOCK |
| Regression fail | CRITICAL | Phase 3→4 | BLOCK |
| E2E uses mocks | CRITICAL | Phase 3→4 | BLOCK |
| Root-owned cache | CRITICAL | Phase 3→4 | BLOCK |
| **A11y violations** | **HIGH** | **Phase 3→4** | **Fix required** |

---

## Quick Reference Commands

```bash
# Unit & Integration Tests
npm run test              # All unit tests
npm run test:coverage     # With coverage report
npm run test:rag          # RAG-specific tests (NEW)

# E2E & Browser Tests
npm run test:e2e          # E2E tests (requires backend)
npm run test:visual       # Visual regression
npm run test:performance  # Performance tests
npm run test:a11y         # Accessibility tests

# Quality Checks
npm run check:bundle      # Bundle size check (NEW)
npm run check:complexity  # Code complexity
npm audit                 # Security audit
```

**Bundle Size Check Setup** (add to package.json):
```json
{
  "scripts": {
    "check:bundle": "npm run build && node scripts/check-bundle-size.js"
  }
}
```

**Bundle Size Check Script**:
```javascript
// scripts/check-bundle-size.js
import { readdirSync, statSync } from 'fs';
import { join } from 'path';
import { gzipSync } from 'zlib';
import { readFileSync } from 'fs';

const BUILD_DIR = '.svelte-kit/output/client';
const MAX_SIZE_KB = 60;  // 60KB gzipped limit

function getGzipSize(filePath) {
    const content = readFileSync(filePath);
    return gzipSync(content).length / 1024;  // KB
}

function checkBundleSize() {
    const jsFiles = readdirSync(BUILD_DIR)
        .filter(f => f.endsWith('.js'))
        .map(f => ({
            name: f,
            size: getGzipSize(join(BUILD_DIR, f))
        }));

    const totalSize = jsFiles.reduce((sum, f) => sum + f.size, 0);

    console.log('\n📦 Bundle Size Report:');
    console.log('─'.repeat(50));
    jsFiles.forEach(f => {
        const status = f.size > MAX_SIZE_KB / 2 ? '⚠️' : '✅';
        console.log(`${status} ${f.name}: ${f.size.toFixed(2)} KB`);
    });
    console.log('─'.repeat(50));
    console.log(`Total: ${totalSize.toFixed(2)} KB (limit: ${MAX_SIZE_KB} KB)`);

    if (totalSize > MAX_SIZE_KB) {
        console.error(`\n❌ FAIL: Bundle exceeds ${MAX_SIZE_KB}KB limit!`);
        process.exit(1);
    }

    console.log('\n✅ PASS: Bundle size within limit');
}

checkBundleSize();
```

**CI Integration** (GitHub Actions):
```yaml
# .github/workflows/test.yml
- name: Check bundle size
  run: npm run check:bundle
```

---

### Rule 17: Error Scenario Coverage (NEW)

> **Backend-Agent raised**: Need systematic error scenario generation for comprehensive API testing.

**Every API endpoint MUST have tests for ALL error scenarios.**

**Error Scenario Matrix**:

| Category | HTTP Status | Scenarios to Test |
|----------|-------------|-------------------|
| **Validation** | 400 | Missing required fields, invalid types, out of range |
| **Authentication** | 401 | No token, expired token, malformed token |
| **Authorization** | 403 | No permission, wrong role, resource owned by other |
| **Not Found** | 404 | Resource deleted, invalid ID format, wrong project |
| **Conflict** | 409 | Duplicate name, concurrent modification, state conflict |
| **Unprocessable** | 422 | Business rule violation, invalid state transition |
| **Rate Limit** | 429 | Too many requests (if applicable) |
| **Server Error** | 500 | Database error, external service failure |
| **Network** | N/A | Timeout, connection refused, DNS failure |

**Error Scenario Test Template**:
```typescript
// src/lib/services/api/projects.error.test.ts
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { createProject, getProject, deleteProject } from './projects';

const server = setupServer();
beforeAll(() => server.listen());
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

describe('Projects API - Error Scenarios', () => {
    // 400 Validation Errors
    describe('400 Bad Request', () => {
        it('should handle missing name', async () => {
            server.use(
                http.post('/api/projects/create', () => {
                    return HttpResponse.json(
                        { detail: 'name is required' },
                        { status: 400 }
                    );
                })
            );
            await expect(createProject({ name: '' })).rejects.toThrow('name is required');
        });

        it('should handle name too long', async () => {
            server.use(
                http.post('/api/projects/create', () => {
                    return HttpResponse.json(
                        { detail: 'name must be <= 200 characters' },
                        { status: 400 }
                    );
                })
            );
            await expect(createProject({ name: 'x'.repeat(300) })).rejects.toThrow();
        });
    });

    // 401 Authentication Errors
    describe('401 Unauthorized', () => {
        it('should handle expired token', async () => {
            server.use(
                http.get('/api/projects/:id', () => {
                    return HttpResponse.json(
                        { detail: 'Token expired' },
                        { status: 401 }
                    );
                })
            );
            await expect(getProject(1)).rejects.toThrow('Token expired');
        });
    });

    // 404 Not Found Errors
    describe('404 Not Found', () => {
        it('should handle non-existent project', async () => {
            server.use(
                http.get('/api/projects/:id', () => {
                    return HttpResponse.json(
                        { detail: 'Project not found' },
                        { status: 404 }
                    );
                })
            );
            await expect(getProject(99999)).rejects.toThrow('Project not found');
        });
    });

    // 409 Conflict Errors
    describe('409 Conflict', () => {
        it('should handle duplicate project name', async () => {
            server.use(
                http.post('/api/projects/create', () => {
                    return HttpResponse.json(
                        { detail: 'Project with this name already exists' },
                        { status: 409 }
                    );
                })
            );
            await expect(createProject({ name: 'Existing' })).rejects.toThrow('already exists');
        });
    });

    // 500 Server Errors
    describe('500 Internal Server Error', () => {
        it('should handle database error', async () => {
            server.use(
                http.post('/api/projects/create', () => {
                    return HttpResponse.json(
                        { detail: 'Database connection failed' },
                        { status: 500 }
                    );
                })
            );
            await expect(createProject({ name: 'Test' })).rejects.toThrow();
        });
    });

    // Network Errors
    describe('Network Errors', () => {
        it('should handle timeout', async () => {
            server.use(
                http.get('/api/projects/:id', async () => {
                    await new Promise(r => setTimeout(r, 10000)); // Simulate timeout
                    return HttpResponse.json({});
                })
            );
            // Set fetch timeout in actual implementation
            await expect(getProject(1, { timeout: 1000 })).rejects.toThrow('timeout');
        });

        it('should handle connection refused', async () => {
            server.use(
                http.get('/api/projects/:id', () => {
                    return HttpResponse.error();
                })
            );
            await expect(getProject(1)).rejects.toThrow();
        });
    });
});
```

**Error Scenario Checklist Per Endpoint**:

| Endpoint | 400 | 401 | 403 | 404 | 409 | 422 | 500 | Network |
|----------|-----|-----|-----|-----|-----|-----|-----|---------|
| POST /projects/create | ✅ | ✅ | - | - | ✅ | - | ✅ | ✅ |
| GET /projects/:id | ✅ | ✅ | ✅ | ✅ | - | - | ✅ | ✅ |
| PUT /projects/:id | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ |
| DELETE /projects/:id | - | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ |
| POST /chat/stream | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ |

**UI Error Display Tests** (E2E):
```typescript
// tests/e2e/error-handling.spec.ts
test.describe('Error Handling UI', () => {
    test('should display validation error message', async ({ page }) => {
        await page.goto('/projects/new');
        await page.locator('[data-testid="submit-btn"]').click();

        await expect(page.locator('[data-testid="error-message"]'))
            .toContainText('Name is required');
    });

    test('should display network error with retry', async ({ page }) => {
        // Simulate offline
        await page.route('**/api/**', route => route.abort('connectionfailed'));

        await page.goto('/projects');

        await expect(page.locator('[data-testid="error-banner"]'))
            .toContainText('Connection failed');
        await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();
    });

    test('should recover after retry', async ({ page }) => {
        let requestCount = 0;
        await page.route('**/api/projects/', route => {
            requestCount++;
            if (requestCount === 1) {
                return route.abort('connectionfailed');
            }
            return route.fulfill({ status: 200, body: JSON.stringify([]) });
        });

        await page.goto('/projects');
        await page.locator('[data-testid="retry-btn"]').click();

        await expect(page.locator('[data-testid="project-list"]')).toBeVisible();
    });
});
```

**Error Scenario Generator Script** (optional helper):
```typescript
// scripts/generate-error-tests.ts
// Usage: npx ts-node scripts/generate-error-tests.ts src/lib/services/api/projects.ts

interface ErrorScenario {
    status: number;
    name: string;
    detail: string;
}

const STANDARD_ERRORS: ErrorScenario[] = [
    { status: 400, name: 'Bad Request', detail: 'Invalid request body' },
    { status: 401, name: 'Unauthorized', detail: 'Token expired' },
    { status: 403, name: 'Forbidden', detail: 'No permission' },
    { status: 404, name: 'Not Found', detail: 'Resource not found' },
    { status: 409, name: 'Conflict', detail: 'Resource already exists' },
    { status: 422, name: 'Unprocessable', detail: 'Validation failed' },
    { status: 500, name: 'Server Error', detail: 'Internal server error' },
];

function generateErrorTests(apiFile: string): string {
    // Parse API file and generate test skeleton for each function
    // Output: *.error.test.ts file
}
```

**Phase Gate Integration**:
- **Phase 3→4**: Error scenario tests for all new endpoints MUST exist
- **Phase 4→5**: UI error handling E2E tests MUST pass

**Coverage Target**: Each API endpoint should have ≥5 error scenario tests.

---

### Rule 18: Session Journey Testing (一條龍測試) (NEW - 2025-12-14)

> **Multi-Agent Meeting Conclusion**: Isolated tests miss state accumulation bugs. Serial session tests catch bugs that only appear when features are used in sequence.

**Problem**: 322 tests pass, but manual testing finds bugs in minutes.
- Tests start fresh with `page.goto('/')` each time
- `fullyParallel: true` prevents state sharing
- No `storageState` - session not preserved
- No `test.describe.serial` - order not guaranteed

**Solution**: Session Journey tests that maintain state across multiple steps.

**Test Command**:
```bash
npm run test:e2e -- tests/e2e/user-session-journey.spec.ts
```

**Key Playwright Features Used**:
```typescript
// Serial execution (order matters)
test.describe.serial('Journey: Create → Edit → Delete', () => {
    let page: Page;
    let projectId: number;  // Shared state

    test.beforeAll(async ({ browser }) => {
        const context = await browser.newContext();
        page = await context.newPage();
        await page.goto(BASE_URL);
    });

    test.afterAll(async () => {
        await page.close();
    });

    test('Step 1: Create project', async () => {
        // Creates project, stores ID in projectId
        projectId = await createProject(page, 'Test');
        expect(projectId).toBeDefined();
    });

    test('Step 2: Edit project (uses projectId)', async () => {
        // Uses projectId from Step 1
        await editProject(page, projectId, 'New Name');
    });

    test('Step 3: Delete project', async () => {
        // Uses projectId from Step 1
        await deleteProject(page, projectId);
    });
});
```

**Session Journey Test Categories**:

| Journey | Tests | Catches |
|---------|-------|---------|
| **Project Lifecycle** | Create → Edit → Select → Delete | State persistence, cascading deletes |
| **Chat Workflow** | New Chat → Send Message → Reply → View History | Message ordering, streaming completion |
| **Cross-Tab Navigation** | Chat → Projects → Documents → Chat | State loss on navigation |
| **Multi-Operation** | Create 5 chats → Count verification | Counter synchronization bugs |

**Journey Test Template**:
```typescript
// tests/e2e/user-session-journey.spec.ts
test.describe.serial('Journey N: Feature Workflow', () => {
    let page: Page;
    const sessionState = { /* shared data */ };

    test.beforeAll(async ({ browser }) => {
        const context = await browser.newContext();
        page = await context.newPage();
    });

    test.afterAll(async () => {
        // Cleanup test data
        await cleanupTestData(sessionState);
        await page.close();
    });

    test('Step 1: Initial action', async () => { /* ... */ });
    test('Step 2: Dependent action', async () => { /* ... */ });
    test('Step 3: Verify state', async () => { /* ... */ });
});
```

**Phase Gate Integration**:
- **Phase 4→5**: At least 3 session journey tests MUST pass
- **Regression**: Journey tests included in regression suite

**Test File Location**: `tests/e2e/user-session-journey.spec.ts`

---

### Rule 19: State Consistency Testing (跨元件資料一致性) (NEW - 2025-12-14)

> **Multi-Agent Meeting Conclusion**: "30 chats vs 10 chats" bug - different UI components showing different values for the same data.

**Problem**: Same data displayed in multiple places but values don't match.
- Sidebar shows 30 conversations
- Project dropdown shows 10 conversations
- Stats panel shows 25 conversations
- All should show the SAME number

**Root Cause Identified** (Frontend-Agent):
```
Dual Store Architecture:
- conversations.items ← Chat tab uses this
- projectDetails.conversations ← Projects tab uses this
- NO synchronization between them!
```

**Solution**: State Consistency tests verify same data displays identically everywhere.

**Test Command**:
```bash
npm run test:e2e -- tests/e2e/state-consistency.spec.ts
```

**Consistency Test Pattern**:
```typescript
// Collect data from ALL UI locations that show it
interface ConsistencyResult {
    source: string;
    value: number | string;
    element: string;
}

async function collectConversationCounts(page: Page): Promise<ConsistencyResult[]> {
    const results: ConsistencyResult[] = [];

    // Source 1: Sidebar list count
    const sidebarItems = page.locator('[data-testid="conversation-item"]');
    results.push({
        source: 'sidebar-list',
        value: await sidebarItems.count(),
        element: '[data-testid="conversation-item"]'
    });

    // Source 2: Header counter
    const headerCount = page.locator('[data-testid="chat-count"]');
    if (await headerCount.isVisible()) {
        results.push({
            source: 'header-count',
            value: parseInt(await headerCount.textContent() || '0'),
            element: '[data-testid="chat-count"]'
        });
    }

    // Source 3: Project stats
    // ... more sources ...

    return results;
}

// Verify all sources show same value
function checkConsistency(results: ConsistencyResult[]): boolean {
    const values = results.map(r => r.value);
    return values.every(v => v === values[0]);
}
```

**Consistency Test Categories**:

| Data | Sources to Compare |
|------|-------------------|
| **Conversation Count** | Sidebar list, Header counter, Project stats, Dropdown label |
| **Project Count** | Project list, Project dropdown, Move-to dropdown |
| **Selected Project** | Dropdown selection, Highlighted item in list |
| **Conversation Title** | Sidebar preview, Chat header, Browser tab title |
| **Message Count** | Per-conversation, Total in project |

**Test Template**:
```typescript
// tests/e2e/state-consistency.spec.ts
test.describe('State Consistency', () => {
    test('conversation count matches across all UI elements', async ({ page }) => {
        await page.goto('/');

        const counts = await collectConversationCounts(page);

        console.log('Collected counts:', counts);

        // Use soft assertions to log ALL inconsistencies
        expect.soft(checkConsistency(counts),
            `Inconsistency detected: ${JSON.stringify(counts)}`
        ).toBe(true);
    });

    test('API vs UI consistency', async ({ page }) => {
        // Get count from API
        const apiResponse = await page.request.get('/api/conversations/list');
        const apiData = await apiResponse.json();
        const apiCount = apiData.data?.items?.length || 0;

        // Get count from UI
        const uiCount = await page.locator('[data-testid="conversation-item"]').count();

        expect(uiCount).toBe(apiCount);
    });
});
```

**Soft Assertions for Discovery**:
```typescript
// Use soft assertions to find ALL issues, not just first
expect.soft(sidebarCount, 'Sidebar count').toBe(apiCount);
expect.soft(headerCount, 'Header count').toBe(apiCount);
expect.soft(statsCount, 'Stats count').toBe(apiCount);

// Test will report all failures, not stop at first
```

**Phase Gate Integration**:
- **Phase 4→5**: State consistency tests MUST pass
- **Regression**: Include in CI for catching dual-store bugs

**Test File Location**: `tests/e2e/state-consistency.spec.ts`

**Architecture Fix Recommendation** (deferred to future stage):
```typescript
// Future: Single source of truth
// Instead of:
// - conversations.items (Chat tab)
// - projectDetails.conversations (Projects tab)

// Use:
// - conversations.items (single source)
// - Derived data for all views
```

---

### Rule 20: Test Type Summary Table (Updated 2025-12-14)

| Test Type | Tool | Backend | Execution | Purpose |
|-----------|------|---------|-----------|---------|
| Unit | Vitest | No | Parallel | Function/module isolation |
| Contract | Vitest + Zod | No | Parallel | Schema validation |
| Integration | Vitest + MSW | No | Parallel | API contract mocking |
| Component | Playwright | No | Parallel | Component rendering |
| E2E (Standard) | Playwright | **Yes** | Parallel | Feature validation |
| **E2E (Journey)** | Playwright | **Yes** | **Serial** | **State accumulation** |
| **E2E (Consistency)** | Playwright | **Yes** | Parallel | **Cross-component data** |
| Visual | Playwright | Yes | Parallel | Screenshot comparison |
| A11y | Playwright + axe | Yes | Parallel | Accessibility |
| Performance | Playwright | Yes | Parallel | Web vitals |

**New Test Categories Added**:
- **E2E (Journey)**: `user-session-journey.spec.ts` - Serial, shared state
- **E2E (Consistency)**: `state-consistency.spec.ts` - Data verification across UI

---

## Related Standards

| Document | Location | Description |
|----------|----------|-------------|
| `TESTING-STANDARDS.md` | `docs/` | Comprehensive testing guide |
| `CODING-ARCHITECTURE-RULES.md` | `.claude-bus/standards/` | Code quality rules |
| `PATTERN-LIBRARY.md` | `.claude-bus/standards/` | Reusable patterns |
| `CONTINUOUS-QUALITY.md` | `.claude-bus/standards/` | Real-time quality monitoring |

---

### Rule 21: Outcome Verification Testing (NEW - 2025-12-20)

> **Critical Bug Reference**: Projects Tab showed ALL 102 conversations instead of only the 5 belonging to the selected project. Root cause: wrong derived store used (`currentProjectConversations` vs `selectedProjectConversations`). ALL E2E tests passed because they only verified "click works" and "list appears" - NOT that the displayed data was correct.

**Problem**: Tests verify that UI actions complete (button clicked, list renders) but do NOT verify that the displayed DATA is correct.

```typescript
// BAD: Only verifies UI action completed
test('should show conversation list when project selected', async ({ page }) => {
    await page.locator('[data-testid="project-item"]').first().click();
    await expect(page.locator('.conversation-list')).toBeVisible();  // PASSES even with wrong data!
});

// GOOD: Verifies OUTCOME is correct
test('should show ONLY conversations belonging to selected project', async ({ page }) => {
    const projectId = 5;
    await page.locator(`[data-testid="project-item-${projectId}"]`).click();

    // Get all displayed conversation project_ids
    const conversations = page.locator('[data-testid="conversation-item"]');
    const count = await conversations.count();

    for (let i = 0; i < count; i++) {
        const convProjectId = await conversations.nth(i).getAttribute('data-project-id');
        expect(parseInt(convProjectId || '0')).toBe(projectId);  // FAILS if wrong data!
    }
});
```

**Outcome Verification Checklist**:

| Test Scenario | What Most Tests Check | What You MUST Also Check |
|---------------|----------------------|--------------------------|
| **Filter by project** | List renders | All items belong to that project |
| **Filter by date** | List renders | All items are within date range |
| **Search results** | Results appear | All results match search query |
| **Sorted list** | List renders | Items are actually in correct order |
| **Pagination** | "Next" button works | Page 2 has different items than Page 1 |
| **Delete item** | Item disappears | Item is NOT in list, AND count decreased |

**Mandatory Test Structure for Filtered Views**:

```typescript
test.describe('Filtered View: Project Conversations', () => {
    // 1. POSITIVE: Verify INCLUSION - items that SHOULD appear DO appear
    test('should include conversations from selected project', async ({ page }) => {
        await selectProject(page, projectId);
        const conversations = await getConversationProjectIds(page);

        // At least one conversation should exist
        expect(conversations.length).toBeGreaterThan(0);

        // All should belong to selected project
        conversations.forEach(convProjectId => {
            expect(convProjectId).toBe(projectId);
        });
    });

    // 2. NEGATIVE: Verify EXCLUSION - items that should NOT appear are absent
    test('should NOT include conversations from other projects', async ({ page }) => {
        await selectProject(page, projectId);
        const conversations = await getConversationProjectIds(page);

        // None should belong to other projects
        const otherProjectConversations = conversations.filter(id => id !== projectId);
        expect(otherProjectConversations.length).toBe(0);
    });

    // 3. COUNT: Verify count matches filtered result
    test('should show correct count for selected project', async ({ page }) => {
        await selectProject(page, projectId);

        // Get count from API for this specific project
        const apiCount = await getProjectConversationCount(page, projectId);

        // Get count from UI
        const uiCount = await page.locator('[data-testid="conversation-item"]').count();

        // Should match (accounting for pagination if applicable)
        expect(uiCount).toBeLessThanOrEqual(apiCount);
        if (apiCount <= PAGE_SIZE) {
            expect(uiCount).toBe(apiCount);
        }
    });
});
```

**Phase Gate Integration**:
- **Phase 4->5**: Filtered views MUST have outcome verification tests (inclusion + exclusion + count)
- **Regression**: Add to regression suite for all filter-related components

**Test File Location**: Tests should be co-located with existing E2E tests, e.g., `tests/e2e/project-conversations-filter.spec.ts`

---

### Rule 22: Data Attribute Requirements for Testing (NEW - 2025-12-20)

> **Root Cause of Bug**: The test could not verify which project each conversation belonged to because conversations did not expose `project_id` in the DOM.

**Problem**: Filtered lists render items but do not expose the filtering key in the DOM, making it impossible to verify correctness.

**Solution**: All filterable/sortable list items MUST expose their key attributes as `data-*` attributes.

**Mandatory Data Attributes**:

| Component | Required Attributes | Example |
|-----------|---------------------|---------|
| Conversation item | `data-conversation-id`, `data-project-id` | `<div data-testid="conversation-item" data-conversation-id="123" data-project-id="5">` |
| Project item | `data-project-id` | `<div data-testid="project-item-5" data-project-id="5">` |
| Message item | `data-message-id`, `data-conversation-id` | `<div data-message-id="456" data-conversation-id="123">` |
| Document item | `data-document-id`, `data-project-id` | `<div data-document-id="789" data-project-id="5">` |
| Sorted item | `data-sort-key` | `<div data-sort-key="2025-12-20T10:00:00Z">` |
| Filtered item | `data-filter-value` | `<div data-filter-value="IEC-62443">` |

**Implementation Example**:

```svelte
<!-- ChatHistoryItem.svelte -->
<div
    class="chat-history-item"
    data-testid="conversation-item"
    data-conversation-id={conversation.id}
    data-project-id={conversation.project_id}
    role="button"
>
    <!-- content -->
</div>
```

**Verification Test Pattern**:

```typescript
// Verify data attributes exist and are correct
test('conversation items should expose project_id for testing', async ({ page }) => {
    const conversations = page.locator('[data-testid="conversation-item"]');
    const count = await conversations.count();

    expect(count).toBeGreaterThan(0);

    for (let i = 0; i < count; i++) {
        const projectId = await conversations.nth(i).getAttribute('data-project-id');
        expect(projectId).not.toBeNull();
        expect(parseInt(projectId!)).toBeGreaterThan(0);
    }
});
```

**Phase Gate Integration**:
- **Phase 1 (Planning)**: UI selector contracts (o8) MUST include data attributes for all list items
- **Phase 3->4**: QA-Agent verifies data attributes are present in components

**Why This Matters**:
- Without data attributes, tests can only verify "list renders" not "list is correct"
- The bug that showed 102 conversations instead of 5 would have been caught immediately
- Enables outcome verification (Rule 21) to actually work

---

### Rule 23: Cross-Store Synchronization Testing (NEW - 2025-12-20)

> **Architecture Issue**: Multiple stores (`conversations.items`, `projectDetails.conversations`) hold the same data type but are NOT synchronized, causing UI inconsistencies.

**Problem**: Svelte stores that represent the same entity from different views can get out of sync.

**Known Dual-Store Pattern in GPT-OSS**:
```
conversations.items          <- Chat tab uses this (filtered by currentProjectId)
projectDetails.conversations <- Projects tab uses this (filtered by selectedProjectId)
```

**Test Pattern for Dual-Store Bugs**:

```typescript
test.describe('Cross-Store Synchronization', () => {
    test('conversations should be consistent across stores after project switch', async ({ page }) => {
        // Select project in Chat tab
        await selectProjectInChatTab(page, projectId);
        const chatTabConversations = await getConversationIds(page, 'chat-tab');

        // Switch to Projects tab, select same project
        await page.locator('#projects-tab').click();
        await selectProjectInProjectsTab(page, projectId);
        const projectsTabConversations = await getConversationIds(page, 'projects-tab');

        // Both should show the same conversations
        expect(chatTabConversations.sort()).toEqual(projectsTabConversations.sort());
    });

    test('new conversation should appear in both tabs', async ({ page }) => {
        // Create conversation in Chat tab
        await createConversation(page, projectId, 'Test message');
        const chatConvCount = await page.locator('.chat-history-item').count();

        // Switch to Projects tab
        await page.locator('#projects-tab').click();
        await selectProjectInProjectsTab(page, projectId);
        const projectConvCount = await page.locator('[data-testid="conversation-item"]').count();

        // Counts should match
        expect(projectConvCount).toBe(chatConvCount);
    });

    test('deleted conversation should disappear from both tabs', async ({ page }) => {
        // Delete conversation from Projects tab
        await deleteConversation(page, conversationId);
        const projectConvCount = await page.locator('[data-testid="conversation-item"]').count();

        // Switch to Chat tab
        await page.locator('#chat-tab').click();
        const chatConvCount = await page.locator('.chat-history-item').count();

        // Counts should match
        expect(chatConvCount).toBe(projectConvCount);
    });
});
```

**When to Write Cross-Store Tests**:
- When same data is displayed in multiple tabs/views
- When operations in one view should affect another view
- When filters are applied differently in different contexts

**Phase Gate Integration**:
- **Phase 4->5**: Cross-store synchronization tests MUST pass for all shared data types
- **Architecture Review**: Identify all dual-store patterns during Phase 1

---

### Rule 24: Filter Boundary Testing (NEW - 2025-12-20)

> **Pattern**: Filter bugs often occur at boundaries - when switching from "all" to "specific" or vice versa.

**Mandatory Boundary Test Cases**:

```typescript
test.describe('Filter Boundary Cases', () => {
    // 1. ALL -> SPECIFIC transition
    test('switching from "All Projects" to specific project should filter correctly', async ({ page }) => {
        // Start with "All Projects" selected
        await page.locator('[data-testid="project-selector"]').selectOption('all');
        const allCount = await page.locator('.chat-history-item').count();

        // Switch to specific project
        await page.locator('[data-testid="project-selector"]').selectOption(String(projectId));
        const filteredCount = await page.locator('.chat-history-item').count();

        // Filtered count should be <= all count
        expect(filteredCount).toBeLessThanOrEqual(allCount);

        // All visible items should belong to selected project
        const visibleProjectIds = await getConversationProjectIds(page);
        visibleProjectIds.forEach(pid => expect(pid).toBe(projectId));
    });

    // 2. SPECIFIC -> ALL transition
    test('switching from specific project to "All Projects" should show all', async ({ page }) => {
        // Start with specific project
        await page.locator('[data-testid="project-selector"]').selectOption(String(projectId));
        const filteredCount = await page.locator('.chat-history-item').count();

        // Switch to "All Projects"
        await page.locator('[data-testid="project-selector"]').selectOption('all');
        const allCount = await page.locator('.chat-history-item').count();

        // All count should be >= filtered count
        expect(allCount).toBeGreaterThanOrEqual(filteredCount);
    });

    // 3. SPECIFIC -> DIFFERENT SPECIFIC transition
    test('switching between projects should update filter correctly', async ({ page }) => {
        // Select first project
        await page.locator('[data-testid="project-selector"]').selectOption(String(projectId1));
        const project1Ids = await getConversationProjectIds(page);
        project1Ids.forEach(pid => expect(pid).toBe(projectId1));

        // Switch to different project
        await page.locator('[data-testid="project-selector"]').selectOption(String(projectId2));
        const project2Ids = await getConversationProjectIds(page);
        project2Ids.forEach(pid => expect(pid).toBe(projectId2));

        // No conversations from project1 should appear
        const leakedIds = project2Ids.filter(pid => pid === projectId1);
        expect(leakedIds.length).toBe(0);
    });

    // 4. Empty result case
    test('project with no conversations should show empty state', async ({ page }) => {
        // Select project with no conversations (or create one for test)
        await page.locator('[data-testid="project-selector"]').selectOption(String(emptyProjectId));

        // Should show empty state, not "All Projects" conversations
        const count = await page.locator('.chat-history-item').count();
        expect(count).toBe(0);

        // Empty state message should be visible
        await expect(page.locator('.empty-state, [data-testid="empty-conversations"]')).toBeVisible();
    });
});
```

**Phase Gate Integration**:
- **Phase 4->5**: All filter components MUST have boundary tests (all->specific, specific->all, specific->different, empty)

---

### Rule 25: Derived Store Correctness Testing (NEW - 2025-12-20)

> **Root Cause Pattern**: The bug occurred because a component used the WRONG derived store. The component used `currentProjectConversations` (filters by Chat tab's `currentProjectId`) instead of `selectedProjectConversations` (filters by Projects tab's `selectedProjectId`).

**Problem**: Multiple similar-sounding derived stores exist for different contexts, and using the wrong one passes all existing tests.

**Known Similar Stores**:
```typescript
// These sound similar but filter by DIFFERENT project IDs
currentProjectConversations   // Filters by currentProjectId (Chat tab)
selectedProjectConversations  // Filters by selectedProjectId (Projects tab)
```

**Mandatory Store Usage Verification**:

```typescript
// Unit test: Verify derived store uses correct source
test.describe('Derived Store: selectedProjectConversations', () => {
    test('should filter by selectedProjectId, NOT currentProjectId', () => {
        // Setup: Different values for currentProjectId and selectedProjectId
        currentProjectId.set(10);  // Chat tab project
        selectedProjectId.set(20); // Projects tab project

        conversations.setConversations([
            { id: 1, project_id: 10, title: 'Conv for project 10' },
            { id: 2, project_id: 20, title: 'Conv for project 20' },
            { id: 3, project_id: 30, title: 'Conv for project 30' },
        ]);

        // Get value from selectedProjectConversations
        const result = get(selectedProjectConversations);

        // Should ONLY have project 20's conversations (selectedProjectId)
        // NOT project 10's (currentProjectId)
        expect(result.length).toBe(1);
        expect(result[0].project_id).toBe(20);  // Uses selectedProjectId
        expect(result[0].project_id).not.toBe(10);  // Does NOT use currentProjectId
    });

    test('should return empty array when selectedProjectId is null', () => {
        selectedProjectId.set(null);
        currentProjectId.set(10);  // This should NOT affect result

        conversations.setConversations([
            { id: 1, project_id: 10, title: 'Conv' },
        ]);

        const result = get(selectedProjectConversations);

        // Should be empty because selectedProjectId is null
        expect(result.length).toBe(0);
    });
});
```

**Component Store Usage Verification**:

```typescript
// E2E test: Verify component uses correct store in correct context
test.describe('ProjectDetails Store Usage', () => {
    test('should use selectedProjectConversations, not currentProjectConversations', async ({ page }) => {
        // Setup: Select different projects in Chat and Projects tabs
        // Chat tab: project 10
        await page.locator('#chat-tab').click();
        await page.locator('[data-testid="project-selector"]').selectOption('10');

        // Projects tab: project 20
        await page.locator('#projects-tab').click();
        await page.locator('[data-testid="project-item-20"]').click();

        // Get conversations shown in ProjectDetails
        const conversations = page.locator('[data-testid="project-details"] [data-testid="conversation-item"]');
        const count = await conversations.count();

        // All should be from project 20 (Projects tab selection)
        // NOT from project 10 (Chat tab selection)
        for (let i = 0; i < count; i++) {
            const projectId = await conversations.nth(i).getAttribute('data-project-id');
            expect(parseInt(projectId || '0')).toBe(20);
        }
    });
});
```

**Phase Gate Integration**:
- **Phase 3->4**: Unit tests MUST verify derived stores filter by correct source
- **Phase 4->5**: E2E tests MUST verify components use correct store in context

---

### Rule 26: Test Summary Table (Updated 2025-12-20)

| Test Type | Tool | Backend | Execution | Purpose | Key Checks |
|-----------|------|---------|-----------|---------|------------|
| Unit | Vitest | No | Parallel | Function/module isolation | Logic correctness |
| Contract | Vitest + Zod | No | Parallel | Schema validation | Request/response shapes |
| Integration | Vitest + MSW | No | Parallel | API contract mocking | Error handling, flows |
| Component | Playwright | No | Parallel | Component rendering | UI states, interactions |
| E2E (Standard) | Playwright | **Yes** | Parallel | Feature validation | Happy path, errors |
| **E2E (Journey)** | Playwright | **Yes** | **Serial** | **State accumulation** | Cross-step consistency |
| **E2E (Consistency)** | Playwright | **Yes** | Parallel | **Cross-component data** | Same data everywhere |
| **E2E (Outcome)** | Playwright | **Yes** | Parallel | **Data correctness** | **Filtered results are correct** |
| **E2E (Boundary)** | Playwright | **Yes** | Parallel | **Filter transitions** | **All->Specific, vice versa** |
| Visual | Playwright | Yes | Parallel | Screenshot comparison | UI appearance |
| A11y | Playwright + axe | Yes | Parallel | Accessibility | WCAG compliance |
| Performance | Playwright | Yes | Parallel | Web vitals | LCP, FCP, CLS |

**New Test Categories Added (2025-12-20)**:
- **E2E (Outcome)**: `*-filter-outcome.spec.ts` - Verifies displayed data is correct
- **E2E (Boundary)**: `*-filter-boundary.spec.ts` - Verifies filter transitions work
- **Derived Store Unit Tests**: `*.derived-store.test.ts` - Verifies store uses correct source

---

## Related Standards

| Document | Location | Description |
|----------|----------|-------------|
| `TESTING-STANDARDS.md` | `docs/` | Comprehensive testing guide |
| `CODING-ARCHITECTURE-RULES.md` | `.claude-bus/standards/` | Code quality rules |
| `PATTERN-LIBRARY.md` | `.claude-bus/standards/` | Reusable patterns |
| `CONTINUOUS-QUALITY.md` | `.claude-bus/standards/` | Real-time quality monitoring |

---

**Document Owner**: PM-Architect-Agent
**Last Updated**: 2025-12-20 (Version 3.1 - Added Rules 21-26: Outcome Verification, Data Attributes, Cross-Store Sync, Filter Boundary, Derived Store Correctness)
