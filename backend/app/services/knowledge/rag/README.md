# RAG Service Module

This module provides Retrieval-Augmented Generation (RAG) capabilities for the Tiga backend, integrating vector search, knowledge graph retrieval, and LLM generation.

## Directory Structure

```
backend/app/services/rag/
├── config/             # Configuration & Environment
│   ├── settings.py     # Pydantic settings & path constants
├── retrieval/          # Search & Indexing
│   ├── engines/        # Search Engines (LightRAG, etc.)
│   ├── providers.py    # Vector Store abstractions
│   └── graph.py        # Graph specific retrieval logic
├── generation/         # LLM Generation & QA
│   ├── qa.py           # Main QA Service (Hybrid Search)
│   └── kg_query.py     # Knowledge Graph Query Service
├── knowledge/          # Knowledge Base Management
│   ├── service.py      # KB Service (Indexing, Management)
│   └── parser.py       # Document parsing utilities
├── utils/              # Shared Utilities
│   ├── chunking.py     # Text chunking logic
│   └── common.py       # Common helpers
├── schemas.py          # Pydantic Models & Schemas
├── service.py          # Main Facade Service (RagService)
└── __init__.py         # Public API
```

## Key Components

### 1. Retrieval Engine (`retrieval/engines/lightrag.py`)
- **LightRAG**: The core engine handling hybrid retrieval (Vector + Knowledge Graph).
- Manages vector stores and graph stores in `data/lightrag_store`.

### 2. Knowledge Service (`knowledge/service.py`)
- Handles document indexing, parsing, and deletion.
- Manages the lifecycle of knowledge base documents.

### 3. QA Service (`generation/qa.py`)
- Orchestrates the question-answering process.
- Combines results from vector search and graph search.
- Supports streaming responses with source citations.

### 4. Configuration (`config/settings.py`)
- Centralized configuration using Pydantic `BaseSettings`.
- Manages paths (`UPLOAD_DIR`, `LIGHTRAG_DIR`) and engine settings.

## Usage

```python
from app.services.rag.service import rag_service
from app.services.rag.schemas import SearchRequest

# Search
response = await rag_service.search(SearchRequest(query="AI trends"), db=session)

# Augment Prompt
response = await rag_service.augment_prompt(AugmentRequest(prompt="Explain AI"), db=session)
```

## Backward Compatibility

Aliases are provided for legacy imports:
- `rag/knowledge_base.py` -> `rag/knowledge/service.py`
- `rag/qa.py` -> `rag/generation/qa.py`
- `rag/kg_query.py` -> `rag/generation/kg_query.py`
