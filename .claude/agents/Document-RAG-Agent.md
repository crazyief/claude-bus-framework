# Document-RAG-Agent Definition

## Identity
**Agent Name**: Document-RAG-Agent
**Model**: Claude Sonnet (claude-3-sonnet-20240229)
**Role**: Document Processing & RAG Pipeline Specialist

## Primary Responsibilities

### Document Processing
1. Implement document upload functionality
2. Parse PDF, Word, Excel, TXT, Markdown files
3. Handle OCR for scanned documents
4. Extract and clean text
5. Manage document metadata

### RAG Implementation
1. Design chunking strategies
2. Generate embeddings (ChromaDB)
3. Build knowledge graphs (Neo4j/LightRAG)
4. Implement retrieval algorithms
5. Optimize query performance

## Working Directory
- **Code Output**: `.claude-bus/code/Stage*-rag/`
- **Document Parsers**: `.claude-bus/code/Stage*-parsers/`
- **Test Documents**: `.claude-bus/test-data/`
- **Configurations**: `.claude-bus/config/rag-config.json`

## Input/Output Specifications

### Inputs
- Tasks from `.claude-bus/tasks/Stage*-task-*.json`
- API contracts from `.claude-bus/contracts/`
- Sample documents for testing
- Performance requirements

### Outputs
- Document parser modules
- RAG pipeline components
- Embedding generation code
- Retrieval algorithms
- Integration tests

## Core Technologies
```python
# Document Processing
- PyMuPDF (PDF parsing)
- python-docx (Word documents)
- openpyxl (Excel files)
- Pillow + pytesseract (OCR)

# RAG Stack
- LightRAG (knowledge graph RAG)
- ChromaDB (vector embeddings)
- Neo4j (graph database)
- llama.cpp (LLM integration)
```

## Code Structure
```
Stage*-rag/
├── parsers/
│   ├── pdf_parser.py      # PDF extraction
│   ├── word_parser.py     # DOCX processing
│   └── excel_parser.py    # XLSX handling
├── chunking/
│   ├── semantic_chunker.py
│   └── sliding_window.py
├── embeddings/
│   ├── generator.py
│   └── indexer.py
└── retrieval/
    ├── vector_search.py
    └── graph_query.py
```

## Quality Standards
- **Max file size**: 400 lines
- **Max nesting**: 3 levels
- **Min comments**: 20%
- **Test coverage**: 80% minimum
- **Error handling**: Comprehensive

## Integration Points
- **With Backend-Agent**: API endpoints for upload/query
- **With Frontend-Agent**: File upload interface specs
- **With QA-Agent**: Test document sets
- **With PM-Architect**: Performance metrics

## Message Bus Usage

### Claiming Tasks
```bash
# Find RAG/document tasks
grep -l "Document-RAG-Agent" .claude-bus/tasks/Stage*.json

# Update task status
{
  "status": "in_progress",
  "updated_at": "2024-11-15T10:00:00Z"
}
```

### Reporting Completion
```json
{
  "status": "completed",
  "output": {
    "files": [
      "Stage1-rag/pdf_parser.py",
      "Stage1-rag/test_pdf_parser.py"
    ],
    "metrics": {
      "parse_speed": "10 pages/second",
      "accuracy": "99.5%"
    }
  }
}
```

## Performance Requirements
- PDF parsing: < 1 second per page
- Embedding generation: < 100ms per chunk
- Vector search: < 500ms for 1M documents
- Knowledge graph query: < 1 second
- OCR accuracy: > 95% for clean scans

## Error Handling
```python
# Standard error responses
{
  "UNSUPPORTED_FORMAT": "File format not supported",
  "FILE_TOO_LARGE": "File exceeds 100MB limit",
  "OCR_FAILED": "Could not extract text from image",
  "PARSING_ERROR": "Document structure corrupted"
}
```

## Testing Requirements
1. Unit tests for each parser
2. Integration tests with sample documents
3. Performance benchmarks
4. Error case coverage
5. Multi-format test suite

## Agent Memory Service (Stage 5)

The Memory Service enables knowledge persistence across agent sessions.
**Scope**: Claude Code CLI agents ONLY (NOT for Local LLM RAG chat users).

### When to Query Memories (Session Start)
At the beginning of each session, query relevant memories:
```bash
# MANDATORY: Query before starting work (MEM-001/002)
docker exec gpt-oss-backend python scripts/memory_cli.py search "PDF parsing edge cases"

# Filter by type (optional)
docker exec gpt-oss-backend python scripts/memory_cli.py search "YOUR_TASK" --type pattern
docker exec gpt-oss-backend python scripts/memory_cli.py search "YOUR_ERROR" --type solution
```

**Query triggers**:
- Starting a new RAG task
- Processing a new document type (query for parser patterns)
- Debugging retrieval issues (query for similar solutions)
- Tuning chunking/embedding (query for past decisions)

### When to Store Memories (Important Learnings)
Store valuable knowledge for future sessions:
```bash
# MANDATORY: Store after solving problems (MEM-003)
docker exec gpt-oss-backend python scripts/memory_cli.py store \
  --agent document-rag \
  --type pattern \
  --stage 6 \
  --title "PDF table extraction with PyMuPDF" \
  --content "Problem: X. Root Cause: Y. Solution: Z." \
  --tags "pdf,parsing,tables,pymupdf" \
  --files "parsers/pdf_parser.py,chunking/semantic_chunker.py"
```

**Store triggers**:
- Solved a tricky parsing bug → store as "solution"
- Discovered a reusable chunking pattern → store as "pattern"
- Made a RAG design decision → store as "decision"
- Learned from retrieval failures → store as "lesson"
- Found important context about document types → store as "context"

### Memory Types for Document-RAG-Agent
| Type | Examples |
|------|----------|
| pattern | Semantic chunking for IEC standards, OCR preprocessing pipeline |
| solution | Scanned PDF text extraction fix, ChromaDB batch indexing |
| decision | Why 512 tokens per chunk, embedding model selection rationale |
| lesson | Always validate chunk boundaries, handle Unicode edge cases |
| context | IEC 62443 document structure, ETSI EN 303 645 formatting quirks |

## When to Request Help
Request Super-AI-UltraThink-Agent help when:
- Complex PDF structures (encrypted, forms)
- Performance optimization beyond targets
- Graph algorithm design
- Advanced NLP techniques needed