#!/bin/bash
# LEXA Phase 0 & 1 Local Testing Guide
# Run each test and verify the expected outputs

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║           LEXA LOCAL TESTING - PHASE 0 & 1                       ║"
echo "║          Testing Configuration, Modules, and API                 ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# TEST 1: Configuration Loading
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Configuration Loading"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "COMMAND:"
echo "python -c \"from backend.config.settings import settings; print(f'✓ API Title: {settings.API_TITLE}'); print(f'✓ Model: {settings.MODEL_NAME}'); print(f'✓ Chunk Size: {settings.CHUNK_SIZE_TOKENS} tokens'); print(f'✓ Debate Rounds: {settings.MAX_DEBATE_ROUNDS}')\""
echo ""
echo "EXPECTED OUTPUT:"
echo "✓ API Title: LEXA API"
echo "✓ Model: llama3.1:8b"
echo "✓ Chunk Size: 512 tokens"
echo "✓ Debate Rounds: 3"
echo ""

# ============================================================================
# TEST 2: Module Imports
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Module Imports Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "COMMAND:"
echo "python << 'PYEOF'
from backend.config.settings import settings
from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker
from backend.processing.legal_ner import extract_entities, LegalNER
from backend.processing.temporal_extractor import extract_timeline, TemporalExtractor
from backend.retrieval.sparse_retriever import SparseRetriever, RecipientRankFusion
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.reranker import CrossEncoderReranker
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.workflows.state import LEXAState

print('✓ Configuration module loaded')
print('✓ Hierarchical chunker loaded')
print('✓ Legal NER module loaded')
print('✓ Temporal extractor module loaded')
print('✓ Sparse retriever (BM25) loaded')
print('✓ Dense retriever (FAISS) loaded')
print('✓ Cross-encoder reranker loaded')
print('✓ Hybrid retriever loaded')
print('✓ Enhanced LEXAState loaded')
print('')
print('All 9 core modules imported successfully!')
PYEOF"
echo ""
echo "EXPECTED OUTPUT:"
echo "✓ Configuration module loaded"
echo "✓ Hierarchical chunker loaded"
echo "✓ Legal NER module loaded"
echo "✓ Temporal extractor module loaded"
echo "✓ Sparse retriever (BM25) loaded"
echo "✓ Dense retriever (FAISS) loaded"
echo "✓ Cross-encoder reranker loaded"
echo "✓ Hybrid retriever loaded"
echo "✓ Enhanced LEXAState loaded"
echo ""
echo "All 9 core modules imported successfully!"
echo ""

# ============================================================================
# TEST 3: Hierarchical Chunker
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Hierarchical Chunker - Parsing & Chunking"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "COMMAND:"
echo "python << 'PYEOF'
from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker

sample_statute = '''ACT TITLE: Bharatiya Nyaya Sanhita, 2023
EFFECTIVE DATE: 2024-07-01
JURISDICTION: India

CHAPTER 1: PRELIMINARY

SECTION 34: Acts done by several persons in furtherance of common intention
When a criminal act is done by several persons in furtherance of the common intention of all, each of such persons is liable for that act in the same manner as if the act were done by him alone.

SECTION 35: Joining criminal act with knowledge but without premeditation
Whenever an act is done by several persons, and in the commission of a criminal act is common to all, each of such persons is liable in the manner as if the act were done by him alone.
'''

chunker = HierarchicalStatuteChunker(max_tokens=256, overlap_tokens=64, min_tokens=50)
print('✓ Chunker initialized (max=256, overlap=64, min=50 tokens)')

chunks = chunker.chunk_statute(sample_statute, source_file='BNS_sample.txt')
print(f'✓ Created {len(chunks)} chunks from sample statute')

for i, chunk in enumerate(chunks, 1):
    print(f'\\n  Chunk {i}:')
    print(f'    - ID: {chunk.id}')
    print(f'    - Section: {chunk.section_id} - {chunk.section_title[:40]}...')
    print(f'    - Act: {chunk.act_name}')
    print(f'    - Tokens: {chunk.token_count}')
    print(f'    - Text preview: {chunk.text[:80]}...')
PYEOF"
echo ""
echo "EXPECTED OUTPUT:"
echo "✓ Chunker initialized (max=256, overlap=64, min=50 tokens)"
echo "✓ Created 2 chunks from sample statute"
echo ""
echo "  Chunk 1:"
echo "    - ID: BNS_34_0"
echo "    - Section: 34 - Acts done by several persons in furtherance..."
echo "    - Act: Bharatiya Nyaya Sanhita, 2023"
echo "    - Tokens: ~40-60"
echo "    - Text preview: When a criminal act is done by several persons..."
echo ""
echo "  Chunk 2:"
echo "    - ID: BNS_35_0"
echo "    - Section: 35 - Joining criminal act with knowledge but without..."
echo "    - Act: Bharatiya Nyaya Sanhita, 2023"
echo "    - Tokens: ~40-60"
echo "    - Text preview: Whenever an act is done by several persons..."
echo ""

# ============================================================================
# TEST 4: Legal NER
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Legal NER - Entity Extraction"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "COMMAND:"
echo "python << 'PYEOF'
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

print('✓ Legal NER extraction completed')
print(f'\\n📋 EXTRACTED ENTITIES:')
print(f'  Persons ({len(entities[\"persons\"])}): {[e[\"text\"] for e in entities[\"persons\"]]}')
print(f'  Dates ({len(entities[\"dates\"])}): {[e[\"text\"] for e in entities[\"dates\"]]}')
print(f'  Sections ({len(entities[\"sections\"])}): {[s[\"section_id\"] for s in entities[\"sections\"]]}')
print(f'  Offenses ({len(entities[\"offenses\"])}): {[e[\"text\"] for e in entities[\"offenses\"]]}')
print(f'  Organizations ({len(entities[\"organizations\"])}): {[e[\"text\"] for e in entities[\"organizations\"][:3]]}')
PYEOF"
echo ""
echo "EXPECTED OUTPUT:"
echo "✓ Legal NER extraction completed"
echo ""
echo "📋 EXTRACTED ENTITIES:"
echo "  Persons (2): ['Rajesh Kumar', 'Priya Sharma']"
echo "  Dates (2): ['January 15, 2024', 'December 25, 2023']"
echo "  Sections (2): ['302', '34']"
echo "  Offenses (3): ['murder', 'abetment', 'conspiracy']"
echo "  Organizations (1): ['Bharatiya Nyaya Sanhita']"
echo ""

# ============================================================================
# TEST 5: Temporal Extraction
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Temporal Extraction - Timeline Analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "COMMAND:"
echo "python << 'PYEOF'
from backend.processing.temporal_extractor import TemporalExtractor

sample_text = '''
The crime occurred on 15-01-2024. 
The suspect was arrested on 20-01-2024. 
He confessed on January 22, 2024.
Prior incident on 10-01-2024 was also reported.
'''

extractor = TemporalExtractor()

# Test 1: Date extraction
dates = extractor.extract_dates(sample_text)
print(f'✓ Extracted {len(dates)} dates from text')
for date in dates:
    print(f'  - {date[\"text\"]:20} | Parsed: {date[\"parsed_date\"]}')

# Test 2: Event extraction
events = extractor.extract_events(sample_text)
print(f'\\n✓ Extracted {len(events)} events from text')
for event in events:
    print(f'  - Date: {event[\"date\"]:15} | {event[\"sentence\"][:60]}...')

# Test 3: Inconsistency detection
inconsistencies = extractor.detect_timeline_inconsistencies(events)
print(f'\\n✓ Detected {len(inconsistencies)} timeline inconsistencies')
for inc in inconsistencies:
    print(f'  - {inc[\"type\"]}: {inc[\"event1_date\"]} AFTER {inc[\"event2_date\"]}')
PYEOF"
echo ""
echo "EXPECTED OUTPUT:"
echo "✓ Extracted 4 dates from text"
echo "  - 15-01-2024           | Parsed: 2024-01-15"
echo "  - 20-01-2024           | Parsed: 2024-01-20"
echo "  - January 22, 2024     | Parsed: 2024-01-22"
echo "  - 10-01-2024           | Parsed: 2024-01-10"
echo ""
echo "✓ Extracted 4 events from text"
echo "  - Date: 10-01-2024      | Prior incident on 10-01-2024 was also reported."
echo "  - Date: 15-01-2024      | The crime occurred on 15-01-2024."
echo "  - Date: 20-01-2024      | The suspect was arrested on 20-01-2024."
echo "  - Date: 22-01-2024      | He confessed on January 22, 2024."
echo ""
echo "✓ Detected 0 timeline inconsistencies (events in chronological order)"
echo ""

# ============================================================================
# TEST 6: BM25 Sparse Retriever
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: BM25 Sparse Retriever - Keyword Search"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "COMMAND:"
echo "python << 'PYEOF'
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
print('✓ BM25 index built with 5 chunks')

# Test retrieval
query = 'common intention'
results = retriever.retrieve(query, top_k=3)
print(f'\\n✓ Retrieved {len(results)} results for query: \"{query}\"')
for rank, (metadata, score) in enumerate(results, 1):
    print(f'  {rank}. [{score:.2f}] {metadata[\"text\"]}')

# Test another query
query2 = 'death murder'
results2 = retriever.retrieve(query2, top_k=2)
print(f'\\n✓ Retrieved {len(results2)} results for query: \"{query2}\"')
for rank, (metadata, score) in enumerate(results2, 1):
    print(f'  {rank}. [{score:.2f}] {metadata[\"text\"]}')
PYEOF"
echo ""
echo "EXPECTED OUTPUT:"
echo "✓ BM25 index built with 5 chunks"
echo ""
echo "✓ Retrieved 3 results for query: \"common intention\""
echo "  1. [0.64] Section 34 defines common intention in criminal law"
echo "  2. [0.32] Common intention requires agreement among co-conspirators"
echo "  3. [0.11] Culpable homicide is defined as causing death with intention"
echo ""
echo "✓ Retrieved 2 results for query: \"death murder\""
echo "  1. [0.45] Murder is the most serious crime against person"
echo "  2. [0.38] Culpable homicide is defined as causing death with intention"
echo ""

# ============================================================================
# TEST 7: API Endpoints - Document Upload
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 7: API Endpoints - Health Check & Document Upload"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "STEP 7A: Start API Server"
echo "COMMAND:"
echo "cd backend && uvicorn main:app --reload --port 8000 &"
echo ""
echo "EXPECTED OUTPUT:"
echo "INFO:     Uvicorn running on http://127.0.0.1:8000"
echo "INFO:     Application startup complete"
echo ""
echo "STEP 7B: Check API Health"
echo "COMMAND:"
echo "curl -s http://localhost:8000/openapi.json | python -m json.tool | head -20"
echo ""
echo "EXPECTED OUTPUT:"
echo "{"
echo "  \"openapi\": \"3.1.0\","
echo "  \"info\": {"
echo "    \"title\": \"LEXA API\","
echo "    \"description\": \"Multi-agent legal reasoning system API\","
echo "    \"version\": \"0.1.0\""
echo "  },"
echo "  ... (rest of OpenAPI schema)"
echo ""
echo "STEP 7C: Test Document Upload"
echo "COMMAND:"
echo "# Create test file"
echo "cat > /tmp/test_case.txt << 'EOF'"
echo "Case Details:"
echo "Date: 15-01-2024"
echo "Accused: Mr. Rajesh Kumar"
echo "Charges: Section 302 IPC - Murder"
echo "Section 34: Common intention"
echo "Facts: The crime occurred on January 10, 2024"
echo "EOF"
echo ""
echo "# Upload file"
echo "curl -X POST http://localhost:8000/api/v1/cases/upload \\"
echo "  -F 'file=@/tmp/test_case.txt' \\"
echo "  -H 'Content-Type: multipart/form-data'"
echo ""
echo "EXPECTED OUTPUT:"
echo "{"
echo "  \"case_id\": \"case_20260606_145230_1234\","
echo "  \"status\": \"processing\","
echo "  \"upload_timestamp\": \"2026-06-06T14:52:30.123456\","
echo "  \"message\": \"Case case_20260606_145230_1234 queued for analysis\""
echo "}"
echo ""
echo "STEP 7D: Check Case Status"
echo "COMMAND:"
echo "curl http://localhost:8000/api/v1/cases/case_20260606_145230_1234/status"
echo ""
echo "EXPECTED OUTPUT (after 2-3 seconds):"
echo "{"
echo "  \"case_id\": \"case_20260606_145230_1234\","
echo "  \"status\": \"completed\","
echo "  \"message\": \"Case analysis completed successfully\","
echo "  \"last_updated\": \"2026-06-06T14:52:33.456789\""
echo "}"
echo ""
echo "STEP 7E: Retrieve Analysis Results"
echo "COMMAND:"
echo "curl http://localhost:8000/api/v1/cases/case_20260606_145230_1234/results | python -m json.tool"
echo ""
echo "EXPECTED OUTPUT:"
echo "{"
echo "  \"case_id\": \"case_20260606_145230_1234\","
echo "  \"filename\": \"test_case.txt\","
echo "  \"status\": \"completed\","
echo "  \"timestamp\": \"2026-06-06T14:52:33.456789\","
echo "  \"case_text_length\": 158,"
echo "  \"entities\": {"
echo "    \"persons\": ["
echo "      {\"text\": \"Rajesh Kumar\", \"source\": \"spacy\", \"confidence\": 0.9}"
echo "    ],"
echo "    \"dates\": ["
echo "      {\"text\": \"15-01-2024\", \"parsed_date\": \"2024-01-15\", \"source\": \"regex\", \"confidence\": 0.8},"
echo "      {\"text\": \"January 10, 2024\", \"parsed_date\": \"2024-01-10\", \"source\": \"regex\", \"confidence\": 0.8}"
echo "    ],"
echo "    \"sections\": ["
echo "      {\"text\": \"Section 302 IPC\", \"section_id\": \"302\", \"act\": \"IPC\", \"source\": \"regex\", \"confidence\": 0.95},"
echo "      {\"text\": \"Section 34\", \"section_id\": \"34\", \"source\": \"regex\", \"confidence\": 0.95}"
echo "    ],"
echo "    \"offenses\": ["
echo "      {\"text\": \"Murder\", \"source\": \"regex\", \"confidence\": 0.8}"
echo "    ]"
echo "  },"
echo "  \"timeline\": ["
echo "    {"
echo "      \"date\": \"15-01-2024\","
echo "      \"parsed_date\": \"2024-01-15\","
echo "      \"context\": \"Date: 15-01-2024 Accused: Mr. Rajesh Kumar\","
echo "      \"sentence\": \"Date: 15-01-2024\","
echo "      \"position\": 13"
echo "    },"
echo "    {"
echo "      \"date\": \"January 10, 2024\","
echo "      \"parsed_date\": \"2024-01-10\","
echo "      \"context\": \"Facts: The crime occurred on January 10, 2024\","
echo "      \"sentence\": \"Facts: The crime occurred on January 10, 2024\","
echo "      \"position\": 139"
echo "    }"
echo "  ],"
echo "  \"stages_completed\": ["
echo "    \"document_processing\","
echo "    \"ner\","
echo "    \"temporal_extraction\""
echo "  ]"
echo "}"
echo ""

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    TESTING COMPLETE                              ║"
echo "║                                                                  ║"
echo "║  All 7 test categories have expected outputs documented.        ║"
echo "║  Run each test and compare output with expected results.        ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
