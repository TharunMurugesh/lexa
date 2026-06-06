# LEXA LOCAL TESTING GUIDE - Expected Outputs

**Date:** 2026-06-06  
**Phase Coverage:** Phase 0 & 1  
**Status:** ✅ Ready for Local Testing

---

## QUICK START - Run All Tests

```bash
cd /home/tm/Documents/work/projects/lexa
python TESTING_COMMANDS.py
```

Or run individual tests from sections below.

---

## TEST 1: Configuration Loading

**Purpose:** Verify Pydantic settings configuration loads correctly.

### Command
```bash
python << 'EOF'
from backend.config.settings import settings
print(f"✓ API Title: {settings.API_TITLE}")
print(f"✓ Model: {settings.MODEL_NAME}")
print(f"✓ Chunk Size: {settings.CHUNK_SIZE_TOKENS} tokens")
print(f"✓ Debate Rounds: {settings.MAX_DEBATE_ROUNDS}")
print(f"✓ Reranker Model: {settings.RERANKER_MODEL}")
EOF
```

### Expected Output
```
✓ API Title: LEXA API
✓ Model: llama3.1:8b
✓ Chunk Size: 512 tokens
✓ Debate Rounds: 3
✓ Reranker Model: cross-encoder/ms-marco-MiniLM-L-12-v2
```

### ✅ Validation Criteria
- All settings load without errors
- Default values correctly set
- No missing environment variables (uses defaults)

---

## TEST 2: Module Imports

**Purpose:** Verify all Phase 0 & 1 modules can be imported.

### Command
```bash
python << 'EOF'
from backend.config.settings import settings
from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker
from backend.processing.legal_ner import LegalNER
from backend.processing.temporal_extractor import TemporalExtractor
from backend.retrieval.sparse_retriever import SparseRetriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.reranker import CrossEncoderReranker
from backend.workflows.state import LEXAState
print("✓ All 8 core modules imported successfully!")
EOF
```

### Expected Output
```
✓ All 8 core modules imported successfully!
```

### ✅ Validation Criteria
- No ImportError exceptions
- All modules have correct classes/functions
- No missing dependencies (except optional GPU ones)

---

## TEST 3: Hierarchical Chunker

**Purpose:** Test statute parsing and semantic chunking.

### Command
```bash
python << 'EOF'
from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker

sample_statute = '''ACT TITLE: Bharatiya Nyaya Sanhita, 2023
EFFECTIVE DATE: 2024-07-01
JURISDICTION: India

CHAPTER 1: PRELIMINARY

SECTION 34: Acts done by several persons in furtherance of common intention
When a criminal act is done by several persons in furtherance of the common intention of all, 
each of such persons is liable for that act in the same manner as if the act were done by him alone.

SECTION 35: Joining criminal act with knowledge
Whenever an act is done by several persons, each of such persons is liable.
'''

chunker = HierarchicalStatuteChunker(max_tokens=256, overlap_tokens=64)
chunks = chunker.chunk_statute(sample_statute, source_file='BNS_sample.txt')

print(f"✓ Created {len(chunks)} chunks")
for chunk in chunks:
    print(f"  - Section {chunk.section_id}: {chunk.section_title[:50]}")
    print(f"    Tokens: {chunk.token_count} | Text: {chunk.text[:60]}...")
EOF
```

### Expected Output
```
✓ Created 2 chunks
  - Section 34: Acts done by several persons in furtherance of com
    Tokens: 45 | Text: When a criminal act is done by several persons in...
  - Section 35: Joining criminal act with knowledge
    Tokens: 18 | Text: Whenever an act is done by several persons, each...
```

### ✅ Validation Criteria
- ✓ Chunks created from statute sections
- ✓ Section metadata preserved (section_id, section_title)
- ✓ Token counts are reasonable (~20-100 tokens)
- ✓ Act metadata correctly extracted
- ✓ No errors on parsing

---

## TEST 4: Legal NER - Entity Extraction

**Purpose:** Test Indian law-specific named entity recognition.

### Command
```bash
python << 'EOF'
from backend.processing.legal_ner import LegalNER

sample_text = '''
On January 15, 2024, Mr. Rajesh Kumar and Ms. Priya Sharma were arrested 
under Section 302 of the Bharatiya Nyaya Sanhita, 2023 for murder. 
The crime was committed on December 25, 2023. 
According to Section 34 IPC, common intention is established.
The offense includes abetment and conspiracy.
'''

ner = LegalNER()
entities = ner.extract(sample_text)

print(f"Persons: {[e['text'] for e in entities['persons']]}")
print(f"Dates: {[e['text'] for e in entities['dates']]}")
print(f"Sections: {[(e['section_id'], e['act']) for e in entities['sections']]}")
print(f"Offenses: {[e['text'] for e in entities['offenses']]}")
print(f"Organizations: {[e['text'] for e in entities['organizations'][:2]]}")
EOF
```

### Expected Output
```
Persons: ['Rajesh Kumar', 'Priya Sharma']
Dates: ['January 15, 2024', 'December 25, 2023']
Sections: [('302', 'Bharatiya Nyaya Sanhita'), ('34', 'IPC')]
Offenses: ['murder', 'abetment', 'conspiracy']
Organizations: ['Bharatiya Nyaya Sanhita', 'Bharatiya Nagarik Suraksha Sanhita', ...]
```

### ✅ Validation Criteria
- ✓ 2 persons extracted (Rajesh Kumar, Priya Sharma)
- ✓ 2 dates extracted (January 15, 2024 and December 25, 2023)
- ✓ 2 sections extracted (302, 34)
- ✓ 3 offenses extracted (murder, abetment, conspiracy)
- ✓ Legal acts recognized (BNS, BNSS, IPC)
- ✓ Confidence scores 0.8-0.95

---

## TEST 5: Temporal Extraction - Timeline Analysis

**Purpose:** Extract dates and construct timeline with inconsistency detection.

### Command
```bash
python << 'EOF'
from backend.processing.temporal_extractor import TemporalExtractor

sample_text = '''
The crime occurred on 15-01-2024. 
The suspect was arrested on 20-01-2024. 
He confessed on January 22, 2024.
Prior incident on 10-01-2024 was also reported.
'''

extractor = TemporalExtractor()

# Extract dates
dates = extractor.extract_dates(sample_text)
print(f"✓ Extracted {len(dates)} dates:")
for d in dates:
    print(f"  - {d['text']:20} → {d['parsed_date']}")

# Extract events (sorted chronologically)
events = extractor.extract_events(sample_text)
print(f"\n✓ Extracted {len(events)} events (chronological order):")
for e in events:
    print(f"  - {e['date']:15} | {e['sentence'][:50]}")

# Check for inconsistencies
inconsistencies = extractor.detect_timeline_inconsistencies(events)
print(f"\n✓ Timeline inconsistencies: {len(inconsistencies)}")
for inc in inconsistencies:
    print(f"  - {inc}")
EOF
```

### Expected Output
```
✓ Extracted 4 dates:
  - 15-01-2024           → 2024-01-15T00:00:00
  - 20-01-2024           → 2024-01-20T00:00:00
  - January 22, 2024     → 2024-01-22T00:00:00
  - 10-01-2024           → 2024-01-10T00:00:00

✓ Extracted 4 events (chronological order):
  - 10-01-2024      | Prior incident on 10-01-2024 was also reported.
  - 15-01-2024      | The crime occurred on 15-01-2024.
  - 20-01-2024      | The suspect was arrested on 20-01-2024.
  - January 22, 2024 | He confessed on January 22, 2024.

✓ Timeline inconsistencies: 0
```

### ✅ Validation Criteria
- ✓ All dates extracted (4 dates found)
- ✓ Dates correctly parsed to ISO format
- ✓ Events ordered chronologically
- ✓ No false timeline inconsistencies (events in order)
- ✓ Event context sentences captured

---

## TEST 6: BM25 Sparse Retriever

**Purpose:** Test keyword-based retrieval (essential for legal queries).

### Command
```bash
python << 'EOF'
from backend.retrieval.sparse_retriever import SparseRetriever

# Create test corpus
test_chunks = [
    {'id': '1', 'text': 'Section 34 defines common intention in criminal law'},
    {'id': '2', 'text': 'Culpable homicide is defined as causing death with intention'},
    {'id': '3', 'text': 'Abetment means instigating someone to commit a crime'},
    {'id': '4', 'text': 'Murder is the most serious crime against person'},
    {'id': '5', 'text': 'Common intention requires agreement among co-conspirators'},
]

retriever = SparseRetriever()
retriever.build_index(test_chunks)
print("✓ BM25 index built with 5 chunks")

# Test Query 1
query1 = 'common intention'
results1 = retriever.retrieve(query1, top_k=3)
print(f"\n✓ Query 1: '{query1}' (Retrieved {len(results1)})")
for rank, (metadata, score) in enumerate(results1, 1):
    print(f"  {rank}. [BM25: {score:.3f}] {metadata['text'][:60]}")

# Test Query 2
query2 = 'death murder'
results2 = retriever.retrieve(query2, top_k=2)
print(f"\n✓ Query 2: '{query2}' (Retrieved {len(results2)})")
for rank, (metadata, score) in enumerate(results2, 1):
    print(f"  {rank}. [BM25: {score:.3f}] {metadata['text'][:60]}")
EOF
```

### Expected Output
```
✓ BM25 index built with 5 chunks

✓ Query 1: 'common intention' (Retrieved 3)
  1. [BM25: 0.651] Common intention requires agreement among co-cons
  2. [BM25: 0.577] Section 34 defines common intention in criminal l
  3. [BM25: 0.231] Culpable homicide is defined as causing death wit

✓ Query 2: 'death murder' (Retrieved 2)
  1. [BM25: 0.648] Murder is the most serious crime against person
  2. [BM25: 0.485] Culpable homicide is defined as causing death wit
```

### ✅ Validation Criteria
- ✓ Index builds successfully
- ✓ Retrieval returns ranked results
- ✓ BM25 scores are between 0-1
- ✓ Most relevant results ranked first
- ✓ Query variations handled correctly

---

## TEST 7: API Endpoints - Document Upload

**Purpose:** Test async document analysis API endpoints.

### Step 7.1: Start API Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Expected Output (Server Starting)
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
SUCCESS: Connected to Ollama and found 'llama3.1:8b'.
```

### Step 7.2: Check API Health (in another terminal)

```bash
curl -s http://localhost:8000/docs
```

### Expected Output
```
(HTML page with FastAPI interactive documentation)
- Endpoints listed: /api/v1/cases/upload, /api/v1/cases/{case_id}/status, etc.
```

### Step 7.3: Upload Document

```bash
# Create test case
cat > /tmp/test_case.txt << 'EOF'
Case Details:
Date: 15-01-2024
Accused: Mr. Rajesh Kumar
Charges: Section 302 IPC - Murder
Section 34: Common intention
Facts: The crime occurred on January 10, 2024
EOF

# Upload
curl -X POST http://localhost:8000/api/v1/cases/upload \
  -F "file=@/tmp/test_case.txt"
```

### Expected Output
```json
{
  "case_id": "case_20260606_145230_1234",
  "status": "processing",
  "upload_timestamp": "2026-06-06T14:52:30.123456",
  "message": "Case case_20260606_145230_1234 queued for analysis"
}
```

### Step 7.4: Check Status

```bash
curl http://localhost:8000/api/v1/cases/case_20260606_145230_1234/status
```

### Expected Output (after 2-3 seconds)
```json
{
  "case_id": "case_20260606_145230_1234",
  "status": "completed",
  "message": "Case analysis completed successfully",
  "last_updated": "2026-06-06T14:52:33.456789"
}
```

### Step 7.5: Retrieve Full Results

```bash
curl http://localhost:8000/api/v1/cases/case_20260606_145230_1234/results | python -m json.tool
```

### Expected Output
```json
{
  "case_id": "case_20260606_145230_1234",
  "filename": "test_case.txt",
  "status": "completed",
  "timestamp": "2026-06-06T14:52:33.456789",
  "case_text_length": 158,
  "entities": {
    "persons": [
      {"text": "Rajesh Kumar", "source": "spacy", "confidence": 0.9}
    ],
    "dates": [
      {"text": "15-01-2024", "parsed_date": "2024-01-15", "source": "regex", "confidence": 0.8},
      {"text": "January 10, 2024", "parsed_date": "2024-01-10", "source": "regex", "confidence": 0.8}
    ],
    "sections": [
      {"text": "Section 302 IPC", "section_id": "302", "act": "IPC", "source": "regex", "confidence": 0.95},
      {"text": "Section 34", "section_id": "34", "source": "regex", "confidence": 0.95}
    ],
    "offenses": [
      {"text": "Murder", "source": "regex", "confidence": 0.8}
    ]
  },
  "timeline": [
    {
      "date": "15-01-2024",
      "parsed_date": "2024-01-15",
      "sentence": "Date: 15-01-2024",
      "position": 13
    },
    {
      "date": "January 10, 2024",
      "parsed_date": "2024-01-10",
      "sentence": "Facts: The crime occurred on January 10, 2024",
      "position": 139
    }
  ],
  "stages_completed": [
    "document_processing",
    "ner",
    "temporal_extraction"
  ]
}
```

### ✅ Validation Criteria
- ✓ File uploads successfully (multipart form-data)
- ✓ Case ID generated (format: case_YYYYMMDD_HHMMSS_XXXX)
- ✓ Status transitions from "processing" to "completed"
- ✓ Results contain extracted entities and timeline
- ✓ Async processing works (check status after delay)
- ✓ All 3 processing stages completed

---

## TEST 8: Full End-to-End Pipeline

**Purpose:** Complete integration test.

### Command
```bash
python << 'EOF'
from backend.config.settings import settings
from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker
from backend.processing.legal_ner import LegalNER
from backend.processing.temporal_extractor import TemporalExtractor
from backend.retrieval.sparse_retriever import SparseRetriever

# Step 1: Parse statute
statute = '''ACT TITLE: Sample Act
CHAPTER 1: PRELIMINARY
SECTION 1: Definition
This defines the term.
'''
chunker = HierarchicalStatuteChunker()
chunks = chunker.chunk_statute(statute)
print(f"Step 1: ✓ Created {len(chunks)} chunks")

# Step 2: Build retrieval index
retriever = SparseRetriever()
chunk_dicts = [{'id': c.id, 'text': c.text} for c in chunks]
if chunk_dicts:
    retriever.build_index(chunk_dicts)
    print(f"Step 2: ✓ Built BM25 index")

# Step 3: Extract entities from case
ner = LegalNER()
case_text = "Section 1 defines the term. On 15-01-2024, Mr. Kumar was arrested."
entities = ner.extract(case_text)
print(f"Step 3: ✓ Extracted entities: {len(entities['sections'])} sections, {len(entities['persons'])} persons")

# Step 4: Extract timeline
extractor = TemporalExtractor()
timeline = extractor.extract_events(case_text)
print(f"Step 4: ✓ Extracted {len(timeline)} timeline events")

print("\n✅ FULL PIPELINE SUCCESSFUL")
EOF
```

### Expected Output
```
Step 1: ✓ Created X chunks
Step 2: ✓ Built BM25 index
Step 3: ✓ Extracted entities: X sections, X persons
Step 4: ✓ Extracted X timeline events

✅ FULL PIPELINE SUCCESSFUL
```

---

## TROUBLESHOOTING

### Issue: Module not found errors
**Solution:** Ensure Python path includes backend folder:
```bash
cd /home/tm/Documents/work/projects/lexa
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Issue: Settings not loading
**Solution:** Check `.env` file exists or use defaults:
```bash
# Use defaults (no .env needed for testing)
python -c "from backend.config.settings import settings; print(settings.API_TITLE)"
```

### Issue: Spacy NER not working
**Solution:** Optional - download spacy model:
```bash
python -m spacy download en_core_web_sm
```
(Tests work without it; uses regex fallback)

### Issue: API port 8000 in use
**Solution:** Use different port:
```bash
cd backend
uvicorn main:app --reload --port 8001
```

---

## QUICK REFERENCE - All Tests in One Script

Save as `run_tests.py`:
```bash
python TESTING_GUIDE.sh
```

Or create the file manually:
```bash
python << 'EOF'
# All 8 tests combined
# (See above for individual test code)
EOF
```

---

## SUMMARY - Expected Test Results

| Test | Components | Expected Output |
|------|------------|-----------------|
| **1** | Config | ✓ 6 settings loaded |
| **2** | Imports | ✓ 8 modules imported |
| **3** | Chunker | ✓ 2+ chunks created |
| **4** | NER | ✓ 2+ persons, 2+ dates, 2+ sections |
| **5** | Timeline | ✓ 4+ dates extracted, 0 inconsistencies |
| **6** | BM25 | ✓ 3+ results ranked correctly |
| **7** | API | ✓ Upload, status, results working |
| **8** | E2E | ✓ Full pipeline successful |

---

**Status:** ✅ All Tests Ready | Run and Validate Locally

*Generated: 2026-06-06 | Phase 0 & 1 Testing Guide*
