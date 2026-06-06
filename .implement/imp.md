# LEXA — Architecture Critical Review
**Reviewer Role:** Principal AI Architect + Research Engineer + NVIDIA AI Systems Engineer  
**Review Type:** Pre-implementation adversarial critique  
**Audience:** NVIDIA Engineers, AI Researchers, Capstone Evaluators

---

## TABLE OF CONTENTS

1. Architecture Critique
2. Missing Components
3. Better Design Alternatives
4. Folder Structure
5. Detailed Phase Breakdown
6. Risks and Mitigations
7. Research Contributions
8. Evaluation Methodology
9. GPU Optimization Strategy
10. Final Production Architecture

---

## 1. ARCHITECTURE CRITIQUE

### 1.1 Agent Architecture — Fatal Design Flaw

**Current design:** Linear sequential pipeline  
Evidence → Legal → Prosecutor → Defense → Contradiction → Judge → Jury

**Why this is wrong:**

The architecture claims to use LangGraph but doesn't leverage its core value proposition: **conditional graph execution with state accumulation**. What's described is a waterfall pipeline with fancy agent names — not a deliberative multi-agent system.

Critical failures:

- **No feedback loops.** If the Contradiction Agent detects a fatal timeline inconsistency, the system cannot loop back to re-extract evidence or re-query RAG. It just continues.
- **No adversarial iteration.** Prosecutor and Defense agents each run once. Real legal deliberation involves rounds of argumentation, counter-argument, and rebuttal. A single pass produces shallow reasoning.
- **Jury agent is not an ensemble.** One LLM asked to simulate "majority voting" is still one model. The variance you capture is prompt-level, not model-level. This is pseudo-ensemble and will be immediately challenged by any evaluator.
- **No conditional routing.** Low-confidence verdicts, high contradiction scores, and missing evidence should trigger different code paths — not just fall through to the same output.
- **No agent scratchpads or working memory.** LangGraph's `TypedDict` state needs to carry cumulative intermediate outputs (debate rounds, accumulated evidence updates, evolving confidence) — the current schema is too shallow.

**Concrete consequence:** Your "deliberation" will produce verdicts of the same quality as a single-agent chain-of-thought prompt. The multi-agent framing won't survive scrutiny.

---

### 1.2 RAG System — Structurally Incomplete

**Problem 1: Sparse retrieval is missing.**  
FAISS is a dense vector search index. Legal queries often use domain-specific terminology, section numbers, and case citations (e.g., "Section 302 IPC", "Arnesh Kumar v. State of Bihar"). Dense retrieval alone *undersupplies* on exact keyword and section-number matches. This is not a minor optimization — it's a correctness issue for legal citation retrieval.

**Problem 2: No reranker.**  
Without a cross-encoder reranker, top-k retrieval by cosine similarity will frequently return contextually similar but legally irrelevant passages. A prosecutor retrieving laws about "assault" shouldn't also get passages about "verbal assault under employment law."

**Problem 3: Chunking strategy is undefined.**  
Legal statutes have hierarchical structure: Act → Chapter → Section → Sub-section → Clause. Flat chunking by token count destroys this structure. A chunk that spans two sections is semantically corrupted for legal citation purposes.

**Problem 4: No HyDE (Hypothetical Document Embeddings).**  
Legal questions are often phrased differently than statute language. Query: "Can he be arrested without warrant?" → relevant section might say "Cognizable offence defined as..." Standard dense retrieval fails on this embedding gap.

**Problem 5: FAISS index versioning.**  
When the corpus is updated (Bharatiya Nyaya Sanhita amendments, court circulars), what is the rollback strategy? FAISS indices are not natively versioned.

---

### 1.3 Training Strategy — Insufficient Alignment

**Problem 1: SFT alone doesn't produce reasoning preference.**  
Supervised Fine-Tuning on `{facts → analysis → verdict}` trains the model to mimic the format of legal reasoning, not to *prefer* legally sound reasoning over plausible-but-wrong reasoning. Without a preference signal (DPO, ORPO, or GRPO), the model will confabulate confidently.

**Problem 2: Chain-of-thought structure is missing.**  
The training format lacks structured intermediate steps. For legal reasoning, the IRAC framework (Issue → Rule → Application → Conclusion) is the established decomposition. Training without this means the model won't reliably produce auditable reasoning chains.

**Problem 3: 100 cases is a benchmark, not a training set.**  
100 cases provides marginal fine-tuning signal. It's a reasonable evaluation set. Training needs either:
- Synthetic augmentation from statute + case combinations
- LLM-assisted annotation of 500–2000 examples
- Cross-lingual transfer from English legal LLM datasets

**Problem 4: No safety/alignment layer.**  
A system that generates legal verdicts without a constitutional AI constraint can produce outputs that are confidently wrong on life-affecting decisions. No refusal behavior is defined for out-of-scope requests.

---

### 1.4 GPU Strategy — Misaligned with H200 Capabilities

**Problem 1: Quantization rationale is wrong.**  
The NVIDIA H200 has 141GB HBM3e. Llama 3.1 8B in BF16 occupies ~16GB. You have 125GB of headroom. Quantizing for memory compression on this hardware is unjustifiable for a research benchmark — it reduces precision without necessity. The valid rationale for quantization experiments here is **training efficiency**, not serving memory constraints.

**Problem 2: vLLM is absent.**  
BF16/FP16 with standard HuggingFace `generate()` does not implement PagedAttention, continuous batching, or optimized CUDA kernels for KV cache management. On H200, using raw Transformers for serving benchmarks will underperform by 3–10x compared to vLLM. Your throughput numbers will be unrepresentative.

**Problem 3: FP8 is not mentioned.**  
The H100/H200 Transformer Engine natively supports FP8 computation. This is the primary precision advantage of H200 over A100. Not benchmarking FP8 training is a missed research contribution.

**Problem 4: Speculative decoding is absent.**  
For a multi-agent pipeline, each agent call is a sequential inference pass. Speculative decoding (8B model + ~1B draft model) can reduce token generation latency by 2–3x with no quality loss. On a latency-sensitive legal pipeline, this is material.

**Problem 5: Profiling scope is undefined.**  
"Profile with Nsight" is not a strategy. You need baseline kernel profiling targets: attention kernel compute efficiency, memory bandwidth saturation, GEMM utilization rates, and inter-kernel idle gaps. Without these baselines, you can't show what you optimized.

---

### 1.5 Production Architecture — Missing Fundamentals

| Gap | Risk Level |
|-----|-----------|
| No async task queue (Celery/Redis) | HIGH — PDF processing blocks the API thread |
| No audit logging | HIGH — Legal decisions require full provenance |
| No authentication/authorization | HIGH — Legal documents are sensitive |
| No streaming response | MEDIUM — 8B model responses will have 5–30s latency |
| No model versioning (MLflow) | MEDIUM — Can't reproduce results across experiments |
| No hallucination grounding check | HIGH — Legal AI without citation verification is dangerous |
| No data encryption at rest | MEDIUM — PII in case documents |
| No rate limiting | LOW for research, HIGH for deployment |

---

## 2. MISSING COMPONENTS

| # | Component | Reason Required | Phase | Priority |
|---|-----------|----------------|-------|----------|
| 1 | BM25 sparse retriever (Elasticsearch or Tantivy) | Exact section number and legal term matching | 2 | CRITICAL |
| 2 | Cross-encoder reranker (ms-marco-MiniLM-L-12-v2) | Precision improvement for top-k legal passages | 2 | CRITICAL |
| 3 | Legal NER model | Entity extraction: persons, dates, sections, offenses | 1 | HIGH |
| 4 | Temporal reasoner | Timeline construction, inconsistency detection | 3 | HIGH |
| 5 | NLI contradiction module (DeBERTa-v3-large-mnli) | Formal entailment-based contradiction detection | 3 | HIGH |
| 6 | HyDE query expansion | Bridge query-statute embedding gap | 2 | MEDIUM |
| 7 | DPO preference training | Reasoning alignment beyond SFT | 4 | HIGH |
| 8 | IRAC chain-of-thought training schema | Structured legal reasoning format | 4 | HIGH |
| 9 | Hallucination grounding checker | Verify citations exist in retrieved context | 3 | CRITICAL |
| 10 | vLLM serving backend | Production-grade inference with PagedAttention | 5 | HIGH |
| 11 | FP8 training experiments | H200-native precision benchmark | 5 | MEDIUM |
| 12 | Speculative decoding | Latency reduction for multi-agent pipeline | 5 | MEDIUM |
| 13 | MLflow experiment tracker | Reproducibility and model versioning | 2 | HIGH |
| 14 | DVC data versioning | Corpus and training data tracking | 1 | HIGH |
| 15 | Celery + Redis async queue | Non-blocking document processing | 2 | HIGH |
| 16 | Audit logger (structured JSON) | Full decision provenance chain | 2 | CRITICAL |
| 17 | Hierarchical chunker (section-aware) | Preserve statute structure in RAG | 1 | HIGH |
| 18 | Debate orchestrator (multi-round) | True adversarial iteration in LangGraph | 3 | HIGH |
| 19 | Confidence calibration module | Calibrate jury scores against empirical accuracy | 4 | MEDIUM |
| 20 | Streaming FastAPI response (SSE) | Real-time verdict streaming to frontend | 3 | MEDIUM |

---

## 3. BETTER DESIGN ALTERNATIVES

### 3.1 Agent Architecture — Redesign with LangGraph StateGraph

**Replace the linear pipeline with a conditional graph:**

```
LEXAState (TypedDict):
  ├── case_text: str
  ├── extracted_evidence: EvidenceOutput
  ├── retrieved_laws: List[LegalChunk]
  ├── prosecution_args: List[Argument]          # accumulates across rounds
  ├── defense_args: List[Argument]              # accumulates across rounds
  ├── contradictions: ContradictionOutput
  ├── debate_rounds: List[DebateRound]          # new — tracks iteration history
  ├── judge_assessment: JudgeOutput
  ├── jury_votes: List[JuryVote]
  ├── final_verdict: VerdictOutput
  ├── confidence: float
  ├── debate_round_count: int                   # gate condition
  └── contradiction_severity: float             # routing condition
```

**Graph edges (conditional):**

```
extract_evidence
    → retrieve_laws
        → [contradiction_severity > 0.7] → re_extract_evidence (loop, max 2x)
        → [else] → run_debate_round
            → [round < MAX_ROUNDS and confidence < THRESHOLD] → run_debate_round (loop)
            → [else] → judge_deliberation
                → jury_voting
                    → [jury_confidence < 0.6] → run_debate_round (one more round)
                    → [else] → generate_verdict
```

**Why this is better:**
- Debate rounds accumulate — each round sees prior arguments and can refute them
- Contradiction severity gates whether evidence needs re-extraction
- Low-confidence paths trigger additional deliberation, not just a weak verdict
- Every state transition is auditable in the `LEXAState` object

---

### 3.2 RAG Redesign — Hybrid Retrieval with Reranking

**Replace: FAISS-only dense retrieval**  
**With: BM25 + Dense + Cross-encoder reranking pipeline**

```
Query
  ├── BM25 retriever (Elasticsearch) → top-20 sparse candidates
  ├── Dense retriever (FAISS + BGE-large) → top-20 dense candidates
  ↓
Reciprocal Rank Fusion (merge to top-40 unique passages)
  ↓
Cross-encoder reranker (ms-marco-MiniLM-L-12-v2) → top-5 final passages
  ↓
Context assembly with source attribution
```

**HyDE for query expansion:**
```python
# Before retrieval, generate a hypothetical statute passage
hypothetical_passage = llm.generate(
    f"Write the relevant section of Bharatiya Nyaya Sanhita that governs: {query}"
)
# Embed the hypothetical passage for dense retrieval
retrieval_vector = embed(hypothetical_passage)
```

**Hierarchical chunking strategy:**
```
Act → Chapter → Section → Sub-section
Each chunk carries:
  - act_id, chapter_id, section_id
  - parent_context (section title)
  - full_text
  - token_count
Never split mid-section. Sub-sections are atomic units.
```

**Why not ChromaDB or Weaviate?**  
FAISS is the right call for this corpus size (<50K chunks). ChromaDB adds persistence overhead with no retrieval quality benefit at this scale. Weaviate is operationally heavy for a single-developer project. Stick with FAISS + Elasticsearch.

---

### 3.3 Training Redesign — SFT + DPO Pipeline

**Phase A: Supervised Fine-Tuning with IRAC schema**

Replace:
```json
{"facts": "...", "analysis": "...", "verdict": "..."}
```

With:
```json
{
  "instruction": "Analyze the following case using the IRAC framework.",
  "input": {
    "facts": "...",
    "retrieved_laws": ["Section X of BNS: ...", "Section Y of BNSS: ..."]
  },
  "output": {
    "issue": "The central legal question is...",
    "rule": "Applicable law: Section X states...",
    "application": "Applying Section X to the facts: ...",
    "conclusion": "Based on the above, the verdict is...",
    "citations": ["BNS §302", "BNSS §41A"],
    "confidence": 0.84
  }
}
```

**Phase B: Direct Preference Optimization (DPO)**  
Create preference pairs by:
1. Generating 3 candidate outputs per case using temperature sampling
2. Ranking by legal expert (or GPT-4 as proxy evaluator)
3. DPO training: `(prompt, chosen, rejected)` pairs

This teaches the model to *prefer* well-cited, properly structured reasoning over plausible-but-unsupported outputs.

**Dataset construction:**
- 100 curated real cases for evaluation (held out completely)
- 500–1000 synthetic cases from statute + scenario templates (training)
- 200 DPO preference pairs (training)

---

### 3.4 Serving Redesign — vLLM on H200

**Replace:** `model.generate()` with HuggingFace Transformers  
**With:** vLLM `AsyncLLMEngine` with OpenAI-compatible API

```python
# vLLM serving command for H200
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.85 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --speculative-model meta-llama/Llama-3.2-1B-Instruct \
  --num-speculative-tokens 5
```

**Why vLLM over raw HF:**
- PagedAttention: eliminates KV cache fragmentation (30–50% memory efficiency gain)
- Continuous batching: serves concurrent agent calls without queue starvation
- Prefix caching: legal system prompt + statute context reused across agents (significant latency win)
- Speculative decoding: 1B draft model reduces generation latency by ~2x with negligible quality loss

---

### 3.5 Contradiction Detection — NLI-based Formal Method

**Replace:** LLM self-evaluation of contradictions  
**With:** Pipeline using pretrained NLI + LLM synthesis

```python
# Step 1: Pairwise NLI scoring
from transformers import pipeline
nli = pipeline("text-classification", model="cross-encoder/nli-deberta-v3-large")

def detect_contradiction(claim_a: str, claim_b: str) -> float:
    result = nli(f"{claim_a} [SEP] {claim_b}")
    return result[0]["score"] if result[0]["label"] == "contradiction" else 0.0

# Step 2: Build contradiction graph
# Step 3: LLM synthesizes explanation for high-score pairs only
```

**Why:** NLI models are calibrated for entailment/contradiction. LLMs hallucinate contradiction analysis. Use the right tool for the right job.

---

## 4. FOLDER STRUCTURE

```
lexa/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CaseUploader.tsx
│   │   │   ├── VerdictDashboard.tsx
│   │   │   ├── AgentTimeline.tsx           # visualizes debate rounds
│   │   │   ├── EvidenceExplorer.tsx
│   │   │   ├── CitationViewer.tsx
│   │   │   └── ConfidenceGauge.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Analysis.tsx
│   │   │   └── Benchmark.tsx
│   │   ├── hooks/
│   │   │   ├── useSSE.ts                   # streaming verdict hook
│   │   │   └── useCaseAnalysis.ts
│   │   └── types/
│   │       └── lexa.d.ts
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── cases.py                    # upload + trigger analysis
│   │   │   ├── verdicts.py                 # retrieve verdicts
│   │   │   ├── benchmark.py                # evaluation endpoints
│   │   │   └── health.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   ├── rate_limiter.py
│   │   │   └── audit.py                    # structured audit logging
│   │   └── main.py
│   │
│   ├── graph/
│   │   ├── state.py                        # LEXAState TypedDict
│   │   ├── workflow.py                     # LangGraph StateGraph definition
│   │   ├── conditions.py                   # conditional edge logic
│   │   └── debate_orchestrator.py          # multi-round debate controller
│   │
│   ├── agents/
│   │   ├── base_agent.py                   # abstract agent interface
│   │   ├── evidence_agent.py
│   │   ├── legal_research_agent.py
│   │   ├── prosecutor_agent.py
│   │   ├── defense_agent.py
│   │   ├── contradiction_agent.py          # NLI + LLM pipeline
│   │   ├── judge_agent.py
│   │   └── jury_agent.py
│   │
│   ├── retrieval/
│   │   ├── sparse_retriever.py             # BM25 via Elasticsearch
│   │   ├── dense_retriever.py              # FAISS + BGE-large
│   │   ├── reranker.py                     # cross-encoder reranking
│   │   ├── hybrid_retriever.py             # RRF fusion
│   │   ├── hyde.py                         # Hypothetical Document Embeddings
│   │   └── index_manager.py               # FAISS index versioning
│   │
│   ├── processing/
│   │   ├── document_processor.py           # PyMuPDF PDF/TXT parsing
│   │   ├── hierarchical_chunker.py         # section-aware statute chunking
│   │   ├── legal_ner.py                    # NER for legal entities
│   │   ├── temporal_extractor.py           # date/timeline extraction
│   │   └── text_cleaner.py
│   │
│   ├── models/
│   │   ├── llm_client.py                   # vLLM API client
│   │   ├── embedding_manager.py            # BGE-large + e5 management
│   │   ├── nli_module.py                   # DeBERTa NLI
│   │   └── reranker_model.py
│   │
│   ├── training/
│   │   ├── dataset_builder.py              # IRAC format dataset constructor
│   │   ├── synthetic_generator.py          # GPT-4 assisted data augmentation
│   │   ├── sft_trainer.py                  # LoRA SFT with TRL
│   │   ├── dpo_trainer.py                  # DPO preference training
│   │   ├── preference_collector.py         # preference pair constructor
│   │   └── eval_trainer.py                 # in-training evaluation hooks
│   │
│   ├── evaluation/
│   │   ├── metrics.py                      # all evaluation metrics
│   │   ├── irac_scorer.py                  # IRAC structure quality scorer
│   │   ├── citation_verifier.py            # grounding check
│   │   ├── hallucination_detector.py
│   │   ├── calibration.py                  # reliability diagrams
│   │   └── benchmark_runner.py
│   │
│   ├── monitoring/
│   │   ├── audit_logger.py                 # JSON structured audit trail
│   │   ├── metrics_collector.py            # Prometheus metrics
│   │   └── gpu_monitor.py                  # CUDA memory + utilization
│   │
│   ├── tasks/
│   │   ├── celery_app.py                   # Celery + Redis async queue
│   │   └── analysis_task.py                # async case analysis task
│   │
│   └── config/
│       ├── settings.py                     # Pydantic BaseSettings
│       └── prompts/
│           ├── evidence.yaml
│           ├── prosecutor.yaml
│           ├── defense.yaml
│           ├── judge.yaml
│           └── jury.yaml
│
├── data/
│   ├── corpus/
│   │   ├── bns/                            # Bharatiya Nyaya Sanhita
│   │   ├── bnss/                           # Bharatiya Nagarik Suraksha Sanhita
│   │   ├── bsa/                            # Bharatiya Sakshya Adhiniyam
│   │   └── constitution/
│   ├── training/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── dpo_pairs/
│   └── evaluation/
│       ├── cases/
│       └── ground_truth/
│
├── models/
│   ├── checkpoints/                        # LoRA adapters (tracked by MLflow)
│   └── faiss_indices/
│       ├── v1/
│       └── v2/
│
├── scripts/
│   ├── ingest_corpus.py
│   ├── build_faiss_index.py
│   ├── build_elastic_index.py
│   ├── run_sft.py
│   ├── run_dpo.py
│   ├── run_benchmark.py
│   └── profile_gpu.sh                      # Nsight Systems profiling script
│
├── notebooks/
│   ├── 01_corpus_eda.ipynb
│   ├── 02_retrieval_ablation.ipynb
│   ├── 03_agent_trace_analysis.ipynb
│   ├── 04_training_loss_curves.ipynb
│   └── 05_gpu_profiling_analysis.ipynb
│
├── tests/
│   ├── unit/
│   │   ├── test_retrieval.py
│   │   ├── test_agents.py
│   │   └── test_chunker.py
│   └── integration/
│       ├── test_pipeline_e2e.py
│       └── test_graph_routing.py
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── Dockerfile.vllm
│
├── docker-compose.yml
├── docker-compose.gpu.yml                  # H200 override config
├── mlflow.yaml                             # MLflow tracking config
├── dvc.yaml                                # DVC pipeline config
└── docs/
    ├── architecture.md
    ├── api_reference.md
    ├── training_guide.md
    └── gpu_benchmarks.md
```

---

## 5. DETAILED PHASE BREAKDOWN

### Phase 0 — Environment & Data Foundation (Weeks 1–2)

**Goal:** Everything required to run experiments exists and is versioned.

| Task | Output | Tool |
|------|--------|------|
| Set up DVC for corpus versioning | `dvc.yaml` | DVC |
| Set up MLflow tracking server | `mlflow.yaml` | MLflow |
| Ingest BNS, BNSS, BSA, Constitution as raw text | `data/corpus/` | PyMuPDF / pdfminer |
| Build hierarchical chunker | `backend/processing/hierarchical_chunker.py` | Custom |
| Build FAISS dense index (BGE-large-en-v1.5) | `models/faiss_indices/v1/` | FAISS |
| Set up Elasticsearch with BM25 index | Running ES container | Docker |
| Validate retrieval quality (manual inspection, 20 queries) | Retrieval audit notebook | Jupyter |

**Milestone:** Can retrieve 5 relevant statute passages for any legal query with >80% precision (manual evaluation).

---

### Phase 1 — Document Processing Pipeline (Weeks 3–4)

**Goal:** Any uploaded PDF/TXT produces structured evidence JSON.

| Task | Output |
|------|--------|
| PyMuPDF PDF text extraction with layout recovery | `document_processor.py` |
| Text cleaning (OCR artifacts, headers/footers, page numbers) | `text_cleaner.py` |
| Legal NER (GLiNER or spaCy + custom rules for Indian law) | `legal_ner.py` |
| Temporal extraction (dates, timelines) | `temporal_extractor.py` |
| Evidence extraction agent (LLM-based, with structured output) | `evidence_agent.py` |
| FastAPI document upload endpoint | `/api/routes/cases.py` |
| Celery task queue for async processing | `tasks/analysis_task.py` |

**Milestone:** 20 test documents processed end-to-end. Evidence JSON validated against manual annotation (F1 > 0.7 for fact extraction).

---

### Phase 2 — Core RAG + Basic Agent Pipeline (Weeks 5–7)

**Goal:** Single-pass retrieval + basic legal research + minimal verdict.

| Task | Output |
|------|--------|
| Hybrid retriever (BM25 + FAISS + RRF fusion) | `hybrid_retriever.py` |
| Cross-encoder reranker integration | `reranker.py` |
| HyDE query expansion | `hyde.py` |
| Legal research agent | `legal_research_agent.py` |
| Basic judge agent (single-pass verdict, no debate) | `judge_agent.py` |
| LangGraph StateGraph v1 (linear, no loops) | `graph/workflow.py` |
| Hallucination grounding check (citation ∈ retrieved context) | `evaluation/citation_verifier.py` |
| FastAPI streaming endpoint (SSE) | Updated routes |
| Frontend: case upload + basic verdict display | React scaffold |

**Milestone:** End-to-end pipeline running. Hallucination rate on 20 test cases < 30%.

---

### Phase 3 — Multi-Agent Deliberation (Weeks 8–10)

**Goal:** Adversarial debate framework with contradiction detection and conditional routing.

| Task | Output |
|------|--------|
| Prosecutor agent with argument generation | `prosecutor_agent.py` |
| Defense agent with counter-argument generation | `defense_agent.py` |
| NLI-based contradiction detection (DeBERTa-v3) | `contradiction_agent.py` |
| Temporal reasoner for timeline consistency | `temporal_extractor.py` upgrade |
| Debate orchestrator (multi-round loop controller) | `debate_orchestrator.py` |
| LangGraph v2: conditional edges + debate loops | `graph/workflow.py` upgrade |
| Jury agent with explicit vote schema | `jury_agent.py` |
| LangGraph state accumulation for debate history | `graph/state.py` upgrade |
| Frontend: AgentTimeline component (debate visualizer) | React component |

**Milestone:** 3-round debate pipeline produces measurably different verdicts vs single-pass (verified on 20 cases). Contradiction detection F1 > 0.65 on manually labeled contradiction pairs.

---

### Phase 4 — Fine-Tuning Pipeline (Weeks 11–13)

**Goal:** LoRA fine-tuned Llama 3.1 8B outperforms base model on LEXA benchmark.

| Task | Output |
|------|--------|
| IRAC dataset schema design | `training/dataset_builder.py` |
| Synthetic case generation (500 examples) | `data/training/processed/` |
| DPO preference pair construction (200 pairs) | `data/training/dpo_pairs/` |
| LoRA SFT training (rank=16, alpha=32, target: q,v projections) | `training/sft_trainer.py` |
| DPO training on SFT checkpoint | `training/dpo_trainer.py` |
| LoRA adapter evaluation (ROUGE, IRAC score, citation F1) | `evaluation/metrics.py` |
| MLflow experiment logging | All training runs tracked |
| Ablation: LoRA rank comparison (8 vs 16 vs 32) | Notebook |

**Milestone:** Fine-tuned model improves IRAC structure quality by >15% over base model (human evaluation on 30 cases).

---

### Phase 5 — GPU Optimization (Weeks 14–15)

**Goal:** Characterized benchmarks on H200 with optimization ablations.

| Task | Output |
|------|--------|
| Baseline profiling (HF generate, BF16, no optimization) | Nsight Systems trace |
| Flash Attention 2 profiling | Comparative trace |
| vLLM deployment with PagedAttention | `docker/Dockerfile.vllm` |
| FP8 training experiment | Training run + loss curve |
| Speculative decoding benchmark (1B draft) | Latency comparison |
| Prefix caching for system prompt reuse | vLLM config experiment |
| KV cache tuning (`--gpu-memory-utilization` sweep) | Memory vs throughput curves |
| Multi-agent pipeline throughput benchmark | Tokens/sec per agent call |
| Nsight Compute kernel-level analysis of attention kernels | Compute efficiency report |

**Milestone:** Full benchmark table: latency × throughput × memory across all configurations. vLLM shows >3x throughput improvement over baseline.

---

### Phase 6 — Evaluation, Research Paper, Polish (Weeks 16–18)

**Goal:** Research-quality evaluation. Presentable system. Paper outline.

| Task | Output |
|------|--------|
| Run full benchmark on 100 evaluation cases | `evaluation/benchmark_runner.py` |
| Baseline comparisons (base Llama, GPT-4 via API, LegalBERT) | Comparison table |
| Statistical significance testing (McNemar's test for verdict agreement) | Stats notebook |
| Confidence calibration reliability diagram | Calibration curve |
| Frontend polish: full dashboard with all components | Production build |
| Docker Compose production configuration | `docker-compose.yml` |
| API documentation | `docs/api_reference.md` |
| Research paper outline (arXiv preprint target) | `docs/paper_draft.md` |
| Demo video / live demo preparation | Presentation assets |

---

## 6. RISKS AND MITIGATIONS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Training dataset too small for meaningful SFT | HIGH | HIGH | Synthetic augmentation pipeline in Phase 4; use SFT primarily for format alignment, not knowledge |
| DPO preference pairs are biased by GPT-4 as annotator | MEDIUM | MEDIUM | Include 50 human-annotated pairs as gold standard; report annotation agreement |
| NLI model underperforms on legal domain contradictions | MEDIUM | HIGH | Fine-tune DeBERTa on a small set of manually labeled legal contradiction pairs; fall back to LLM-based detection with explicit prompting |
| FAISS index drift on corpus updates | LOW | MEDIUM | Version indices with DVC; document rebuild procedure |
| LangGraph debate loop never terminates | MEDIUM | HIGH | Hard iteration cap (MAX_ROUNDS=3); convergence condition based on confidence delta |
| H200 access is intermittent or quota-limited | MEDIUM | HIGH | All experiments must be reproducible on A100/A10 fallback; document hardware requirements explicitly |
| Evidence agent hallucinates facts not in document | HIGH | CRITICAL | Grounding check: every extracted fact must trace to a document span (extractive verification) |
| Legal RAG retrieves wrong jurisdiction's law | MEDIUM | HIGH | Tag each corpus chunk with `{act, jurisdiction, effective_date}`; filter by jurisdiction before retrieval |
| Verdict quality doesn't exceed GPT-4 baseline | MEDIUM | MEDIUM | Frame research contribution as *explainability and attribution*, not verdict accuracy — this is the defensible research claim |
| Single developer scope creep | HIGH | HIGH | Strict phase gates: do not start Phase N+1 until Phase N milestone is verified |

---

## 7. RESEARCH CONTRIBUTIONS

The current spec has no clearly articulated research contribution. "We built a legal AI system" is an engineering project, not a research claim. These are defensible novel contributions:

### Contribution 1: Indian Legal Corpus Benchmark (ILB-100)
**Claim:** First publicly released evaluation benchmark for generative LLM legal reasoning over Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, and Bharatiya Sakshya Adhiniyam.  
**Evidence required:** 100 annotated cases with ground-truth verdicts, citations, and reasoning chains.  
**Venue:** COLING, LREC, or EMNLP Findings

### Contribution 2: Adversarial Multi-Agent Deliberation for Legal Reasoning
**Claim:** Multi-round adversarial deliberation between prosecutor/defense agents with NLI-gated contradiction detection produces statistically significantly better-calibrated verdict confidence than single-pass reasoning.  
**Evidence required:** Ablation study: single-agent vs. 1-round vs. 3-round debate, with calibration curves.  
**Venue:** AAAI, ACL, or NAACL

### Contribution 3: Legal Hallucination Grounding Metric (LHGM)
**Claim:** Existing hallucination metrics (FActScore, HaluEval) are not adapted for statute-grounded legal reasoning. We define LHGM as the fraction of cited sections that are: (a) retrievable from corpus, (b) semantically entail the stated legal proposition.  
**Evidence required:** Correlation of LHGM with human legal expert ratings.  
**Venue:** ACL Workshop on Legal NLP

### Contribution 4: FP8 vs BF16 vs LoRA Training Efficiency on H200
**Claim:** Comparative benchmark of precision formats and LoRA rank configurations for legal LLM fine-tuning on NVIDIA H200.  
**Evidence required:** Training throughput, loss curves, downstream task accuracy per configuration.  
**Venue:** MLSys, or NVIDIA technical report

---

## 8. EVALUATION METHODOLOGY

### 8.1 Primary Metrics

| Metric | Definition | Measurement |
|--------|-----------|-------------|
| **Verdict Agreement Rate (VAR)** | % cases where LEXA verdict matches ground truth | Automated + human verified |
| **IRAC Structure Score (ISS)** | Automated scoring: Issue (present/absent), Rule (citation valid), Application (length + grounding), Conclusion (matches verdict) | Rule-based + NLI |
| **Legal Hallucination Grounding Metric (LHGM)** | % citations that are (a) in corpus, (b) entail stated proposition | Citation lookup + NLI |
| **Contradiction Recall** | % of planted contradictions detected | Synthetic contradiction injection |
| **Calibration Error (ECE)** | Expected Calibration Error of jury confidence scores | Reliability diagrams |
| **Retrieval Precision@5** | % of top-5 retrieved passages rated relevant by expert | Manual annotation |
| **Reasoning Consistency** | % verdicts unchanged across 3 runs with temperature=0 | Automated re-run |

### 8.2 Baselines (Required for Research Validity)

| Baseline | Rationale |
|----------|-----------|
| GPT-4o (zero-shot, same prompt) | Commercial upper bound |
| Llama 3.1 8B base (no fine-tuning, no RAG) | Ablation: contribution of RAG |
| Llama 3.1 8B + RAG (no fine-tuning) | Ablation: contribution of fine-tuning |
| LEXA single-agent (no debate) | Ablation: contribution of multi-agent |
| LEXA 1-round debate | Ablation: contribution of multi-round |
| LEXA full system | System |

### 8.3 Statistical Testing

- McNemar's test for verdict agreement comparison between baselines
- Bootstrap confidence intervals (n=1000) for all aggregate metrics
- Cohen's κ for inter-annotator agreement on human evaluation (minimum 2 annotators, 50 cases)
- Report p-values; do not claim improvement without p < 0.05

### 8.4 Adversarial Evaluation

Inject synthetic adversarial cases:
1. **Contradictory witnesses** — two witness statements with planted factual conflicts
2. **Missing evidence** — cases with deliberately incomplete timelines
3. **Inapplicable law** — retrieved passages that are irrelevant but lexically similar
4. **Section hallucination** — correct legal reasoning but fabricated section numbers

Report performance on adversarial vs clean cases separately. This is what separates a research paper from a demo.

---

## 9. GPU OPTIMIZATION STRATEGY

### 9.1 Profiling Baseline (Step 0 — Do This First)

Before any optimization, establish documented baselines:

```bash
# Nsight Systems: trace the full inference pipeline
nsys profile \
  --trace=cuda,nvtx,osrt \
  --output=baseline_inference \
  python scripts/run_single_inference.py

# Nsight Compute: kernel-level attention analysis
ncu --metrics sm__throughput.avg.pct_of_peak_sustained_elapsed,\
    l1tex__t_bytes_pipe_lsu_mem_global_op_ld.sum,\
    gpu__time_duration.sum \
  --target-processes all \
  python scripts/run_attention_kernel.py
```

Record these baselines:
- Time-to-first-token (TTFT)
- Time-per-output-token (TPOT)
- GPU memory high-water mark
- Attention kernel compute efficiency %
- Memory bandwidth utilization %

### 9.2 Optimization Experiment Matrix

| Experiment | Variable | Expected Gain | Measurement |
|-----------|----------|--------------|-------------|
| BF16 vs FP16 | dtype | Stability, not speed on H200 | Loss curves + perplexity |
| FP8 training (Transformer Engine) | dtype | ~2x training throughput | Tokens/sec, GPU util % |
| Flash Attention 2 vs PyTorch SDPA | Attention kernel | 20-40% memory reduction | Memory high-water mark |
| LoRA rank ablation (8, 16, 32, 64) | Rank | Quality vs compute tradeoff | ISS + training time |
| vLLM PagedAttention vs HF generate | Serving | 3-10x throughput | Requests/sec at batch 8,16,32 |
| Speculative decoding (1B draft, k=5) | Decoding | ~2x TPOT reduction | TPOT ms |
| Prefix caching (system prompt) | KV cache | ~30% latency reduction on repeat calls | TTFT with/without cache |
| Chunked prefill | Prefill strategy | Reduces prefill latency variance | TTFT distribution |
| GPU memory utilization sweep (0.7, 0.8, 0.85, 0.9) | KV cache size | Throughput vs OOM risk | Max sustained batch size |
| Multi-agent concurrent batching | Concurrency | Overall pipeline throughput | Total case analysis time |

### 9.3 H200-Specific Optimizations

**FP8 via Transformer Engine (most important H200-specific experiment):**
```python
import transformer_engine.pytorch as te

# Replace standard nn.Linear with FP8-capable layers
class FP8Linear(te.Linear):
    pass

# Enable FP8 autocasting
with te.fp8_autocast(enabled=True, fp8_recipe=recipe):
    output = model(input)
```

**Flash Attention 3 (H100/H200 specific — different from FA2):**  
Flash Attention 3 is optimized for Hopper architecture (H100/H200) and achieves ~75% of theoretical peak FLOPs. Install from the FA3 branch and benchmark against FA2.

**KV Cache Quantization (INT8 KV):**  
```bash
vllm serve model --kv-cache-dtype fp8_e5m2
```
Reduces KV cache memory by ~50%, enabling larger batch sizes or longer contexts.

### 9.4 Target Benchmarks

| Metric | Baseline (HF generate, BF16) | Target (vLLM + FA2 + FP8) |
|--------|------------------------------|--------------------------|
| TTFT (prompt=512 tokens) | ~800ms | < 200ms |
| TPOT | ~40ms/token | < 15ms/token |
| Throughput @ batch=8 | ~200 tokens/sec | > 1000 tokens/sec |
| Peak GPU memory (8B, BF16) | ~16GB | ~18GB (larger KV cache budget) |
| Full case analysis latency | ~45s | < 15s |

---

## 10. FINAL PRODUCTION ARCHITECTURE

```
┌──────────────────────────────────────────────────────┐
│                     FRONTEND                          │
│   React + TypeScript + TailwindCSS                    │
│   Components: Upload, AgentTimeline, VerdictDash      │
│   SSE streaming for real-time agent updates           │
└────────────────────┬─────────────────────────────────┘
                     │ HTTPS / SSE
┌────────────────────▼─────────────────────────────────┐
│                  FastAPI GATEWAY                       │
│   Auth middleware → Rate limiter → Audit logger        │
│   POST /cases/analyze  →  Celery task dispatch         │
│   GET  /cases/{id}/stream  →  SSE verdict stream       │
└────────┬───────────────────────────┬─────────────────┘
         │                           │
    Celery Worker              Redis (broker)
         │
┌────────▼────────────────────────────────────────────┐
│               LEXA ANALYSIS PIPELINE                  │
│                                                       │
│  ┌─────────────────────────────────────────────┐     │
│  │  DOCUMENT PROCESSOR                          │     │
│  │  PyMuPDF → text cleaner → legal NER          │     │
│  │  → temporal extractor → section chunker      │     │
│  └──────────────────┬──────────────────────────┘     │
│                     │                                 │
│  ┌──────────────────▼──────────────────────────┐     │
│  │  LANGGRAPH STATEGRAPH (LEXAState)            │     │
│  │                                              │     │
│  │  EvidenceAgent                               │     │
│  │      ↓                                       │     │
│  │  HybridRetriever ──────────────────────────┐ │     │
│  │  [BM25 + FAISS + RRF + CrossEncoder]        │ │     │
│  │      ↓                                      │ │     │
│  │  LegalResearchAgent                         │ │     │
│  │      ↓                                 RAG  │ │     │
│  │  ┌─ DebateOrchestrator (max 3 rounds) ──┐   │ │     │
│  │  │  ProsecutorAgent                     │   │ │     │
│  │  │  DefenseAgent                        │◄──┘ │     │
│  │  │  ContradictionAgent (NLI + LLM)      │     │     │
│  │  └─[confidence < θ → loop]──────────────┘     │     │
│  │      ↓                                        │     │
│  │  JudgeAgent                                   │     │
│  │      ↓                                        │     │
│  │  JuryAgent (3 independent votes)              │     │
│  │      ↓                                        │     │
│  │  HallucinationGroundingCheck                  │     │
│  │      ↓                                        │     │
│  │  VerdictGenerator (IRAC output)               │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
└──────────────┬────────────────────────────────────────┘
               │
┌──────────────▼────────────────────────────────────────┐
│              INFERENCE LAYER                           │
│  vLLM AsyncLLMEngine (Llama 3.1 8B, BF16/FP8)        │
│  + Flash Attention 2/3                                 │
│  + PagedAttention KV cache                             │
│  + Speculative decoding (Llama 3.2 1B draft)          │
│  + Prefix caching (system prompts)                     │
└───────────────────────────────────────────────────────┘
               │                    │
┌──────────────▼──────┐  ┌──────────▼──────────────────┐
│   FAISS INDEX        │  │  ELASTICSEARCH (BM25)        │
│   BGE-large-en-v1.5  │  │  Legal corpus sparse index   │
│   Versioned via DVC  │  └─────────────────────────────┘
└─────────────────────┘
               │
┌──────────────▼────────────────────────────────────────┐
│              OBSERVABILITY                             │
│  MLflow: experiment tracking, model registry           │
│  DVC: corpus + training data versioning                │
│  Audit Logger: structured JSON per decision            │
│  Prometheus + Grafana: GPU metrics, API latency        │
│  Nsight Systems/Compute: kernel-level profiling        │
└───────────────────────────────────────────────────────┘
```

### Final Architecture — Key Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | LangGraph StateGraph with conditional edges | True deliberation, not pipeline |
| LLM serving | vLLM + LoRA adapter | PagedAttention + continuous batching |
| Retrieval | BM25 + FAISS + Cross-encoder | Precision over pure dense retrieval |
| Training | LoRA SFT + DPO | Format alignment + reasoning preference |
| Training format | IRAC chain-of-thought | Auditable legal reasoning |
| Contradiction detection | DeBERTa NLI + LLM synthesis | NLI for signal, LLM for explanation |
| GPU precision | BF16 serving, FP8 training experiment | H200-native capability |
| Hallucination control | Citation grounding check post-generation | Legal correctness requirement |
| Async processing | Celery + Redis | Non-blocking document analysis |
| Reproducibility | DVC + MLflow + Docker | Full experiment provenance |

---

*Review completed. This specification is ready for implementation planning.*  
*Estimated total development time for a single B.Tech student: 16–18 weeks at 20–25 hrs/week.*  
*Minimum viable research contribution (ILB-100 benchmark + multi-agent ablation) achievable by Week 14.*
