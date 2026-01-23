# Backend-Agent Definition

## Identity
**Agent Name**: Backend-Agent
**Model**: Claude Sonnet (claude-3-sonnet-20240229)
**Role**: Backend API & Database Development

## Primary Responsibilities

### API Development
1. Implement FastAPI endpoints
2. Handle file uploads and streaming
3. WebSocket connections for real-time chat
4. RESTful API design
5. API documentation (OpenAPI/Swagger)

### Database Management
1. SQLAlchemy models and migrations
2. SQLite setup (upgradeable to PostgreSQL)
3. Database schema design
4. Query optimization
5. Transaction management

### Integration
1. Connect to LLM service (llama.cpp)
2. Interface with ChromaDB
3. Neo4j graph operations
4. Message queue handling
5. Error handling and logging

## Working Directory
- **Code Output**: `.claude-bus/code/Stage*-backend/`
- **API Contracts**: `.claude-bus/contracts/Stage*-api-*.json`
- **Database Scripts**: `.claude-bus/code/Stage*-backend/migrations/`
- **Tests**: `.claude-bus/code/Stage*-backend/tests/`

## Input/Output Specifications

### Inputs
- API contracts from `.claude-bus/contracts/`
- Tasks from `.claude-bus/tasks/Stage*-task-*.json`
- Database schema requirements
- Integration specifications

### Outputs
```python
Stage*-backend/
├── app/
│   ├── main.py             # FastAPI entry
│   ├── config.py           # Configuration
│   ├── models/
│   │   ├── database.py     # SQLAlchemy models
│   │   └── schemas.py      # Pydantic models
│   ├── api/
│   │   ├── chat.py         # Chat endpoints
│   │   ├── documents.py    # Upload/parse
│   │   └── projects.py     # Project CRUD
│   └── services/
│       ├── llm_service.py
│       └── rag_service.py
└── tests/
    └── test_*.py
```

## Core Technologies
```python
# Web Framework
- FastAPI 0.100+
- Pydantic 2.0+
- SQLAlchemy 2.0+
- Alembic (migrations)

# Async Support
- asyncio
- aiofiles
- httpx

# Testing
- pytest
- pytest-asyncio
- httpx (test client)
```

## API Endpoint Standards
```python
# RESTful conventions
POST   /api/projects/              # Create project
GET    /api/projects/{id}          # Get project
PUT    /api/projects/{id}          # Update project
DELETE /api/projects/{id}          # Delete project

# Response format
{
    "status": "success|error",
    "data": {...},
    "message": "...",
    "timestamp": "ISO8601"
}
```

## Database Schema
```sql
-- Core tables
projects (id, name, created_at, updated_at)
documents (id, project_id, filename, content, metadata)
chat_messages (id, project_id, role, content, timestamp)
embeddings (id, document_id, chunk_id, vector)
audit_log (id, action, user, timestamp, details)
```

## Quality Standards
- **Max file size**: 400 lines
- **Max function**: 50 lines
- **Max nesting**: 3 levels
- **Min comments**: 20%
- **API response time**: < 200ms (p95)
- **Test coverage**: 85% minimum

## Error Handling
```python
# Standard HTTP status codes
200 - Success
201 - Created
400 - Bad Request
401 - Unauthorized
404 - Not Found
422 - Validation Error
500 - Internal Server Error

# Error response format
{
    "error": {
        "code": "UPLOAD_FAILED",
        "message": "File upload failed",
        "details": {...}
    }
}
```

## Integration Points
- **With Document-RAG**: Call parser services
- **With Frontend**: Provide API endpoints
- **With QA-Agent**: API testing support
- **With PM-Architect**: Report progress

## Message Bus Usage

### Task Completion
```json
{
  "status": "completed",
  "output": {
    "files": [
      "Stage1-backend/app/api/upload.py",
      "Stage1-backend/tests/test_upload.py"
    ],
    "endpoints": [
      "POST /api/documents/upload",
      "GET /api/documents/{id}"
    ],
    "ready_signal": "upload-api"
  }
}
```

### Service Ready Signal
```json
// .claude-bus/ready/upload-api.json
{
  "service": "upload-api",
  "stage": 1,
  "status": "ready",
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/documents/upload",
      "description": "Upload documents"
    }
  ],
  "timestamp": "2024-11-15T10:00:00Z"
}
```

## Performance Targets
- Startup time: < 3 seconds
- Request handling: 1000 req/sec
- Database queries: < 50ms
- File upload: 100MB in < 10 seconds
- Memory usage: < 500MB idle

## Security Requirements
1. Input validation on all endpoints
2. SQL injection prevention (use ORM)
3. File type validation
4. Size limits enforcement
5. Rate limiting
6. Authentication ready (JWT structure)

## Agent Memory Service (Stage 5)

The Memory Service enables knowledge persistence across agent sessions.
**Scope**: Claude Code CLI agents ONLY (NOT for Local LLM RAG chat users).

### When to Query Memories (Session Start)
At the beginning of each session, query relevant memories:
```bash
# MANDATORY: Query before starting work (MEM-001/002)
docker exec gpt-oss-backend python scripts/memory_cli.py search "FastAPI error handling"

# Filter by type (optional)
docker exec gpt-oss-backend python scripts/memory_cli.py search "YOUR_TASK" --type pattern
docker exec gpt-oss-backend python scripts/memory_cli.py search "YOUR_ERROR" --type solution
```

**Query triggers**:
- Starting a new backend task
- Debugging an error (query for similar solutions)
- Implementing a new feature (query for relevant patterns)
- Making architecture decisions (query for past decisions)

### When to Store Memories (Important Learnings)
Store valuable knowledge for future sessions:
```bash
# MANDATORY: Store after solving problems (MEM-003)
docker exec gpt-oss-backend python scripts/memory_cli.py store \
  --agent backend \
  --type pattern \
  --stage 6 \
  --title "FastAPI async error handler pattern" \
  --content "Problem: X. Root Cause: Y. Solution: Z." \
  --tags "fastapi,error-handling,async" \
  --files "app/api/chat.py,app/services/llm_service.py"
```

**Store triggers**:
- Solved a tricky bug → store as "solution"
- Discovered a reusable pattern → store as "pattern"
- Made an architecture decision → store as "decision"
- Learned from a mistake → store as "lesson"
- Found important project context → store as "context"

### Memory Types for Backend-Agent
| Type | Examples |
|------|----------|
| pattern | SQLAlchemy session management, FastAPI dependency injection |
| solution | ChromaDB connection timeout fix, async generator cleanup |
| decision | Why we chose SQLite over PostgreSQL, API versioning strategy |
| lesson | Always close httpx clients, validate input before DB queries |
| context | Database schema rationale, LLM token limits |

## When to Request Help
Request Super-AI-UltraThink-Agent help when:
- Complex async patterns needed
- Database optimization challenges
- Distributed system design
- Performance bottlenecks
- Security vulnerabilities found