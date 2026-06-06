#!/bin/bash
# LEXA LOCAL TESTING - QUICK REFERENCE CARD
# Copy-paste ready commands with expected outputs

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║    LEXA LOCAL TESTING - QUICK REFERENCE CARD                     ║"
echo "║    Phase 0 & 1 - Copy & Paste Ready Commands                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# ==========================================================================
# 1. CONFIGURATION TEST
# ==========================================================================
echo "1️⃣  CONFIGURATION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'EOF'
python -c "from backend.config.settings import settings; print(f'✓ {settings.API_TITLE}'); print(f'  Model: {settings.MODEL_NAME}'); print(f'  Debate Rounds: {settings.MAX_DEBATE_ROUNDS}')"

EXPECTED:
✓ LEXA API
  Model: llama3.1:8b
  Debate Rounds: 3
EOF
echo ""

# ==========================================================================
# 2. MODULE IMPORTS TEST
# ==========================================================================
echo "2️⃣  MODULE IMPORTS TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'EOF'
python << 'PYEOF'
try:
    from backend.config.settings import settings
    from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker
    from backend.processing.legal_ner import LegalNER
    from backend.processing.temporal_extractor import TemporalExtractor
    from backend.retrieval.sparse_retriever import SparseRetriever
    from backend.workflows.state import LEXAState
    print("✓ ALL 6 CORE MODULES IMPORTED")
except ImportError as e:
    print(f"✗ Import failed: {e}")
PYEOF

EXPECTED:
✓ ALL 6 CORE MODULES IMPORTED
EOF
echo ""

# ==========================================================================
# 3. NER EXTRACTION TEST
# ==========================================================================
echo "3️⃣  LEGAL NER - ENTITY EXTRACTION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'EOF'
python << 'PYEOF'
from backend.processing.legal_ner import LegalNER

text = "On 15-01-2024, Mr. Rajesh Kumar was arrested under Section 302 IPC for murder."
ner = LegalNER()
entities = ner.extract(text)

print(f"Persons: {len(entities['persons'])} - {[e['text'] for e in entities['persons']]}")
print(f"Dates: {len(entities['dates'])} - {[e['text'] for e in entities['dates']]}")
print(f"Sections: {len(entities['sections'])} - {[e['section_id'] for e in entities['sections']]}")
print(f"Acts: {len(entities['organizations'])} - {[e.get('act_code') for e in entities['organizations'][:2]]}")
PYEOF

EXPECTED:
Persons: 1 - ['Rajesh Kumar']
Dates: 1 - ['15-01-2024']
Sections: 1 - ['302']
Acts: 2 - ['IPC', ...]
EOF
echo ""

# ==========================================================================
# 4. TEMPORAL EXTRACTION TEST
# ==========================================================================
echo "4️⃣  TEMPORAL EXTRACTION - TIMELINE ANALYSIS TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'EOF'
python << 'PYEOF'
from backend.processing.temporal_extractor import TemporalExtractor

text = "Crime on 15-01-2024. Arrest on 20-01-2024. Confession on January 22, 2024."
extractor = TemporalExtractor()

dates = extractor.extract_dates(text)
print(f"✓ Extracted {len(dates)} dates")
for d in dates[:2]:
    print(f"  - {d['text']} → {d['parsed_date']}")

events = extractor.extract_events(text)
print(f"✓ Extracted {len(events)} events (chronological)")
PYEOF

EXPECTED:
✓ Extracted 3 dates
  - 15-01-2024 → 2024-01-15
  - 20-01-2024 → 2024-01-20
✓ Extracted 3 events (chronological)
EOF
echo ""

# ==========================================================================
# 5. BM25 RETRIEVER TEST
# ==========================================================================
echo "5️⃣  BM25 SPARSE RETRIEVER TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'EOF'
python << 'PYEOF'
from backend.retrieval.sparse_retriever import SparseRetriever

chunks = [
    {'id': '1', 'text': 'Section 34 defines common intention'},
    {'id': '2', 'text': 'Common intention requires agreement'},
    {'id': '3', 'text': 'Murder is serious crime'},
]

retriever = SparseRetriever()
retriever.build_index(chunks)
results = retriever.retrieve('common intention', top_k=2)

print(f"✓ BM25 index built with {len(chunks)} chunks")
print(f"✓ Query results ({len(results)}):")
for rank, (meta, score) in enumerate(results, 1):
    print(f"  {rank}. [{score:.2f}] {meta['text'][:40]}")
PYEOF

EXPECTED:
✓ BM25 index built with 3 chunks
✓ Query results (2):
  1. [0.65] Common intention requires agreement
  2. [0.58] Section 34 defines common intention
EOF
echo ""

# ==========================================================================
# 6. API UPLOAD TEST
# ==========================================================================
echo "6️⃣  API DOCUMENT UPLOAD TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'EOF'
# STEP 1: Start API server (terminal 1)
cd backend
uvicorn main:app --reload --port 8000 &
sleep 3

# STEP 2: Create and upload test file (terminal 2)
cat > /tmp/test_case.txt << 'CASE'
Case: Murder case
Date: 15-01-2024
Accused: Mr. Kumar
Section 302 IPC - Murder
Section 34 - Common intention
CASE

curl -X POST http://localhost:8000/api/v1/cases/upload \
  -F "file=@/tmp/test_case.txt" 2>/dev/null | python -m json.tool

EXPECTED (response):
{
  "case_id": "case_20260606_145230_1234",
  "status": "processing",
  "upload_timestamp": "2026-06-06T14:52:30.123456",
  "message": "Case case_20260606_145230_1234 queued for analysis"
}

# STEP 3: Check status after 2-3 seconds
curl http://localhost:8000/api/v1/cases/case_20260606_145230_1234/status 2>/dev/null

EXPECTED:
{
  "case_id": "case_20260606_145230_1234",
  "status": "completed",
  "message": "Case analysis completed successfully"
}

# STEP 4: Get full results
curl http://localhost:8000/api/v1/cases/case_20260606_145230_1234/results 2>/dev/null | python -m json.tool | head -30

EXPECTED:
{
  "case_id": "case_20260606_145230_1234",
  "status": "completed",
  "entities": {
    "persons": [...],
    "dates": [...],
    "sections": [{"section_id": "302"}, {"section_id": "34"}],
    ...
  },
  "timeline": [...]
}
EOF
echo ""

# ==========================================================================
# 7. FULL PIPELINE TEST
# ==========================================================================
echo "7️⃣  FULL PIPELINE END-TO-END TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'EOF'
python << 'PYEOF'
from backend.config.settings import settings
from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker
from backend.processing.legal_ner import LegalNER
from backend.processing.temporal_extractor import TemporalExtractor
from backend.retrieval.sparse_retriever import SparseRetriever

print("🔄 FULL PIPELINE TEST\n")

# 1. Parse statute
print("1️⃣  Parsing statute...")
statute = '''ACT TITLE: Sample Act
SECTION 1: Definition
This section defines the term.
SECTION 2: Punishment
This section provides punishment.
'''
chunker = HierarchicalStatuteChunker()
chunks = chunker.chunk_statute(statute)
print(f"   ✓ Created {len(chunks)} chunks\n")

# 2. Build retrieval
print("2️⃣  Building retrieval index...")
retriever = SparseRetriever()
chunk_dicts = [{'id': c.id, 'text': c.text} for c in chunks]
if chunk_dicts:
    retriever.build_index(chunk_dicts)
    print(f"   ✓ BM25 index built\n")

# 3. Extract entities
print("3️⃣  Extracting entities...")
ner = LegalNER()
case_text = "Section 1 and Section 2. On 15-01-2024, Mr. Kumar was charged."
entities = ner.extract(case_text)
print(f"   ✓ Extracted: {len(entities['sections'])} sections, {len(entities['persons'])} persons\n")

# 4. Extract timeline
print("4️⃣  Extracting timeline...")
extractor = TemporalExtractor()
timeline = extractor.extract_events(case_text)
print(f"   ✓ Extracted {len(timeline)} events\n")

print("✅ FULL PIPELINE COMPLETE!")
PYEOF

EXPECTED:
🔄 FULL PIPELINE TEST

1️⃣  Parsing statute...
   ✓ Created X chunks

2️⃣  Building retrieval index...
   ✓ BM25 index built

3️⃣  Extracting entities...
   ✓ Extracted: X sections, X persons

4️⃣  Extracting timeline...
   ✓ Extracted X events

✅ FULL PIPELINE COMPLETE!
EOF
echo ""

# ==========================================================================
# CLEANUP
# ==========================================================================
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              QUICK TEST REFERENCE COMPLETE                       ║"
echo "║                                                                  ║"
echo "║  📌 Copy-paste commands above into terminal                     ║"
echo "║  📌 Compare output with EXPECTED results                        ║"
echo "║  📌 All 7 tests should pass ✅                                   ║"
echo "║                                                                  ║"
echo "║  🛑 Stop here for testing before proceeding to Phase 2         ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
