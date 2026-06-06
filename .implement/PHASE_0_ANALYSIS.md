# PHASE 0 - ENVIRONMENT & DATA FOUNDATION — ANALYSIS REPORT

**Date:** 2026-06-06  
**Status:** ⚠️ INCOMPLETE - CRITICAL GAPS IDENTIFIED  
**Target Milestone:** Environment fully configured, legal corpus ingested, retrieval indices built

---

## CURRENT STATE AUDIT

### ✅ WHAT EXISTS

#### Backend Infrastructure
- **FastAPI setup**: `main.py` configured with CORS, Ollama health check
- **LLM integration**: `services/llm_service.py` using Ollama + Llama 3.1 8B
- **LangGraph skeleton**: `workflows/graph.py` with basic StateGraph
- **Core agents**: Evidence, Prosecutor, Defense, Judge (placeholder implementations)
- **Processing modules**: 
  - `document_processor.py` - PyMuPDF text extraction
  - `legal_ner.py` - NER extraction (placeholder)
  - `temporal_extractor.py` - Timeline extraction (placeholder)
  - `text_cleaner.py` - Text normalization (placeholder)

#### Dependencies
- Core: FastAPI, Uvicorn, LangGraph, LangChain, Pydantic
- Processing: PyMuPDF (fitz), spaCy
- Async: Celery, Redis
- Tooling: pytest, python-multipart, python-dotenv

#### Frontend
- React + Vite + TailwindCSS scaffold

---

### ❌ CRITICAL GAPS FOR PHASE 0

#### 1. **Data Infrastructure — MISSING**
- ❌ No `data/` directory structure
- ❌ No legal corpus (BNS, BNSS, BSA, Constitution)
- ❌ No DVC initialization for data versioning
- ❌ No corpus metadata tracking
- **Impact:** Cannot test retrieval pipelines; no evaluation baseline

#### 2. **Retrieval System — NOT BUILT**
- ❌ FAISS dense index manager (`backend/retrieval/dense_retriever.py`)
- ❌ Elasticsearch BM25 index (`backend/retrieval/sparse_retriever.py`)
- ❌ Hybrid retriever with RRF (`backend/retrieval/hybrid_retriever.py`)
- ❌ Cross-encoder reranker (`backend/retrieval/reranker.py`)
- ❌ HyDE query expansion (`backend/retrieval/hyde.py`)
- ❌ Index versioning controller (`backend/retrieval/index_manager.py`)
- **Impact:** Phase 2 cannot proceed; no RAG foundation

#### 3. **Chunking Strategy — INCOMPLETE**
- ⚠️ `text_cleaner.py` exists but lacks:
  - Hierarchical (section-aware) chunking
  - Legal structure preservation (Act → Chapter → Section)
  - Token counting and overlap management
  - Metadata tagging (section_id, act_id, jurisdiction, effective_date)
- **Impact:** RAG will lose legal context; chunks corrupt statute structure

#### 4. **Experiment Tracking — NOT SET UP**
- ❌ MLflow not initialized
- ❌ `backend/config/mlflow.yaml` missing
- ❌ No model registry
- ❌ No experiment tracking capability
- **Impact:** Cannot reproduce experiments; no baseline tracking

#### 5. **Data Versioning — NOT SET UP**
- ❌ DVC not initialized
- ❌ `.dvc/` directory missing
- ❌ No `dvc.yaml` pipeline definition
- ❌ No corpus versioning mechanism
- **Impact:** Cannot manage corpus updates; reproducibility broken

#### 6. **LangGraph State — TOO SHALLOW**
Current state in `workflows/state.py`:
```python
class CaseState(TypedDict):
    case_text: str
    extracted_evidence: Optional[Dict]
    entities: Optional[List]
    timeline: Optional[List]
    prosecutor_argument: Optional[str]
    defense_argument: Optional[str]
    verdict: Optional[str]
    reasoning: Optional[str]
    confidence: Optional[float]
    debate_round_count: Optional[int]
```

**Missing (required by spec):**
- `retrieved_laws: List[LegalChunk]` — RAG context
- `prosecution_args: List[Argument]` — accumulates across rounds
- `defense_args: List[Argument]` — accumulates across rounds
- `contradictions: ContradictionOutput` — structured contradiction analysis
- `debate_rounds: List[DebateRound]` — iteration history
- `judge_assessment: JudgeOutput` — judge reasoning
- `jury_votes: List[JuryVote]` — individual votes
- `final_verdict: VerdictOutput` — structured output
- `contradiction_severity: float` — gating condition for re-extraction
- `debate_round_count: int` — loop termination condition

**Impact:** Graph cannot implement required conditional routing and state accumulation

#### 7. **Async Task Queue — NOT CONFIGURED**
- ⚠️ Celery, Redis in `requirements.txt` but no implementation
- ❌ `backend/tasks/celery_app.py` exists but is empty/placeholder
- ❌ No task router for PDF processing
- ❌ No result backend configuration
- **Impact:** Blocking API calls; no async document processing

#### 8. **Configuration Management — INCOMPLETE**
- ❌ `backend/config/settings.py` missing (Pydantic BaseSettings)
- ❌ `.env` variables not documented in `.env.example`
- ❌ No configuration for:
  - FAISS index paths
  - Elasticsearch connection
  - MLflow tracking URI
  - DVC remote storage
  - Celery broker/result backend

#### 9. **Processing Quality — NOT VALIDATED**
- ❌ No test cases for document processing
- ❌ No benchmarks for NER/temporal extraction
- ❌ No evaluation of chunking quality
- ❌ No retrieval audit (manual inspection of 20 queries not completed)
- **Milestone requirement:** Retrieval Precision@5 > 80% not demonstrated

#### 10. **Directory Structure — INCOMPLETE**
Missing folders per spec:
```
backend/retrieval/               ← CRITICAL (retrieval system)
backend/processing/schemas/      ← Output dataclasses missing
backend/models/                  ← Embedding, NLI models missing
backend/training/                ← Will be Phase 4
backend/evaluation/              ← Metrics, benchmarking
backend/monitoring/              ← Audit logging, GPU monitoring
backend/config/                  ← Settings, prompts
backend/config/prompts/          ← YAML prompt templates
data/corpus/                     ← Legal documents
data/training/                   ← Datasets
data/evaluation/                 ← Test cases
models/faiss_indices/            ← Index versioning
models/checkpoints/              ← Model adapters
scripts/                         ← Ingest, indexing, benchmarking
notebooks/                       ← EDA, profiling
```

---

## PHASE 0 IMPLEMENTATION PLAN

### Block 1: Infrastructure Setup (Days 1–2)

1. **DVC Initialization**
   - `dvc init` in project root
   - Configure DVC remote (local disk for now, S3 for production)
   - Create `dvc.yaml` pipeline stub

2. **MLflow Setup**
   - Install MLflow
   - Create `mlflow.yaml` configuration
   - Start MLflow tracking server locally

3. **Directory Structure**
   - Create all missing directories per folder structure in imp.md
   - Add `.gitkeep` files to preserve empty directories

4. **Configuration Management**
   - Create `backend/config/settings.py` (Pydantic BaseSettings)
   - Populate `.env.example` with all required variables
   - Create prompt YAML files in `backend/config/prompts/`

### Block 2: Data Ingestion (Days 3–4)

1. **Legal Corpus Preparation**
   - Source BNS, BNSS, BSA, Constitution as PDFs/TXT
   - Place in `data/corpus/{act_name}/`
   - Version in DVC: `dvc add data/corpus/ && git add data/corpus/.gitignore`

2. **Corpus Metadata**
   - Build index mapping: `section_id → {act, chapter, text, effective_date}`
   - Store as `data/corpus/metadata.json`

### Block 3: Core Retrieval Pipeline (Days 5–6)

1. **Hierarchical Chunker**
   - Parse statute structure (Act → Chapter → Section)
   - Implement section-aware chunking (atomic chunks = sub-sections)
   - Add metadata tagging (act_id, section_id, jurisdiction)
   - Output format: `List[LegalChunk]` with fields: `id, text, metadata, token_count`

2. **FAISS Dense Index**
   - Embed corpus with BGE-large-en-v1.5
   - Build FAISS index
   - Save to `models/faiss_indices/v1/`
   - Version in DVC

3. **Elasticsearch BM25 Index**
   - Spin up ES container (Docker)
   - Index chunked corpus with section metadata
   - Verify exact section number searches work

4. **Hybrid Retriever**
   - Implement `BM25 → top-20 + FAISS → top-20 + RRF fusion → top-40`
   - Test on 20 manual legal queries
   - Document retrieval precision

### Block 4: State & Configuration Updates (Day 7)

1. **LangGraph State Enhancement**
   - Update `workflows/state.py` to full LEXAState spec
   - Add TypedDict dataclasses for intermediate outputs:
     - `EvidenceOutput`, `LegalChunk`, `Argument`, `DebateRound`
     - `ContradictionOutput`, `JudgeOutput`, `JuryVote`, `VerdictOutput`

2. **Processing Schemas**
   - Create `backend/schemas/` with output models
   - Ensure all agent outputs conform to schema

3. **Celery Configuration**
   - Implement `backend/tasks/celery_app.py` with Redis broker
   - Define document processing task

### Block 5: Validation & Auditing (Day 8)

1. **Retrieval Quality Audit**
   - Run retrieval audit on 20 legal queries (manual evaluation)
   - Target: Precision@5 > 80%
   - Document gaps in retrieval

2. **Document Processing Tests**
   - Test PDF extraction on 5 sample PDFs
   - Verify NER F1 > 0.65 on gold-standard annotations
   - Validate temporal extraction

3. **Test Case Setup**
   - Create `tests/unit/test_retrieval.py`
   - Create `tests/unit/test_chunker.py`
   - Create `tests/unit/test_document_processor.py`

---

## PHASE 0 COMPLETION CHECKLIST

- [ ] DVC initialized and corpus versioned
- [ ] MLflow tracking server running
- [ ] All required directories created
- [ ] `backend/config/settings.py` implemented
- [ ] `.env.example` fully documented
- [ ] Hierarchical chunker built and tested
- [ ] FAISS index built (v1) and versioned
- [ ] Elasticsearch BM25 index running
- [ ] Hybrid retriever implemented and tested
- [ ] Retrieval audit completed: Precision@5 > 80%
- [ ] LEXAState updated with full spec
- [ ] All schema/TypedDict classes created
- [ ] Celery + Redis async task queue configured
- [ ] Unit tests passing (retrieval, chunker, document_processor)
- [ ] Corpus metadata tracked in DVC
- [ ] Milestone validated: Can retrieve 5 relevant statute passages for any legal query with >80% precision

---

## RISKS & BLOCKERS

| Risk | Mitigation |
|------|-----------|
| Corpus copyright/licensing | Source from official government digital libraries |
| NER model not available for Indian law | Use spaCy + custom rules + domain-specific fine-tuning |
| FAISS index too large | Implement index sharding if corpus > 100K chunks |
| Elasticsearch OOM on corpus | Use disk-based backend or filter corpus to most relevant acts |
| DVC remote storage not configured | Use local `.dvc/cache` for initial development |

---

## ESTIMATED EFFORT

- **Total Phase 0 effort:** 8 days (solo developer, 4–5 hrs/day)
- **Critical path:** Data ingestion + retrieval pipeline (cannot parallelize)
- **Parallel tracks:** Configuration + directory structure + state design

**Next Phase:** Phase 1 begins after Phase 0 milestone validation.

---

*Report generated: 2026-06-06 by Automated Analysis Agent*
