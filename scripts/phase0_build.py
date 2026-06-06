#!/usr/bin/env python3
"""
Phase 0 Build Script
Initializes FAISS indices, BM25 indices, and validates retrieval quality.

Usage:
    python scripts/phase0_build.py --corpus-dir data/corpus --output-dir models
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.processing.hierarchical_chunker import HierarchicalStatuteChunker
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.sparse_retriever import SparseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.reranker import CrossEncoderReranker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_sample_corpus() -> None:
    """Create sample legal corpus for testing."""
    corpus_dir = Path("data/corpus")
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample statute for testing
    sample_bns = """ACT TITLE: Bharatiya Nyaya Sanhita, 2023
EFFECTIVE DATE: 2024-07-01
JURISDICTION: India

CHAPTER 1: PRELIMINARY

SECTION 1: Short title and commencement
This Act may be called the Bharatiya Nyaya Sanhita, 2023.

SECTION 2: Definitions
In this Act, unless the context otherwise requires,—
(1) "abetment" means instigating any person to do or omit to do any act.
(2) "Common intention" means the common intention as defined in Section 34.
(3) "Cognizable offence" means an offence for which, and "cognizable case" means a case in which, a police officer may, in accordance with the First Schedule or under any other law for the time being in force, arrest without warrant.

CHAPTER 2: GENERAL PRINCIPLES

SECTION 34: Acts done by several persons in furtherance of common intention
When a criminal act is done by several persons in furtherance of the common intention of all, each of such persons is liable for that act in the same manner as if the act were done by him alone.

SECTION 35: Joining criminal act with knowledge but without premeditation or concert
Whenever an act is done by several persons, and in the commission of a criminal act is common to all, each of such persons is liable in the manner as if the act were done by him alone.

CHAPTER 3: OFFENCES AGAINST PERSON

SECTION 100: Culpable homicide
Whoever causes death by doing an act with the intention of causing death, or with the knowledge that by such act he is likely to cause death, commits the offence of culpable homicide.

SECTION 101: Punishment for culpable homicide not amounting to murder
Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine not exceeding five hundred rupees.

SECTION 102: Causing death by rash or negligent act
Whoever causes death by doing any rash or negligent act not amounting to culpable homicide, shall be punished with imprisonment of either description for a term which may extend to two years, or with fine which may extend to one thousand rupees, or with both.
"""
    
    # Write sample statute
    sample_file = corpus_dir / "BNS_sample.txt"
    with open(sample_file, 'w') as f:
        f.write(sample_bns)
    
    logger.info(f"Created sample corpus at {sample_file}")


def chunk_corpus(corpus_dir: str) -> List[Dict[str, Any]]:
    """Chunk all statute files in corpus directory."""
    logger.info(f"Chunking corpus from {corpus_dir}...")
    
    chunker = HierarchicalStatuteChunker(max_tokens=512, overlap_tokens=128, min_tokens=100)
    all_chunks = []
    
    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        logger.warning(f"Corpus directory not found: {corpus_dir}")
        logger.info("Creating sample corpus...")
        prepare_sample_corpus()
    
    # Process all statute files
    for statute_file in sorted(corpus_path.glob("*.txt")):
        logger.info(f"  Processing: {statute_file.name}")
        with open(statute_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        chunks = chunker.chunk_statute(text, source_file=str(statute_file))
        
        # Convert LegalChunk dataclass to dict
        for chunk in chunks:
            chunk_dict = {
                "id": chunk.id,
                "text": chunk.text,
                "act_name": chunk.act_name,
                "act_id": chunk.act_id,
                "section_id": chunk.section_id,
                "section_title": chunk.section_title,
                "chapter_id": chunk.chapter_id,
                "chapter_name": chunk.chapter_name,
                "jurisdiction": chunk.jurisdiction,
                "effective_date": chunk.effective_date,
                "token_count": chunk.token_count,
                "source_file": chunk.source_file,
            }
            all_chunks.append(chunk_dict)
    
    logger.info(f"Total chunks created: {len(all_chunks)}")
    return all_chunks


def build_indices(chunks: List[Dict[str, Any]], output_dir: str) -> None:
    """Build FAISS and BM25 indices."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Build dense index
    logger.info("Building FAISS dense index...")
    try:
        dense_retriever = DenseRetriever(
            embedding_model="sentence-transformers/bge-large-en-v1.5",
            device="cpu"  # Use CPU for compatibility
        )
        dense_retriever.build_index(chunks, batch_size=8)
        
        index_path = output_path / "faiss_index.bin"
        metadata_path = output_path / "faiss_metadata.pkl"
        dense_retriever.save_index(str(index_path), str(metadata_path))
        logger.info(f"  ✓ Dense index saved to {index_path}")
    except Exception as e:
        logger.error(f"  ✗ Dense index build failed: {e}")
        logger.info("  Skipping dense index (GPU/transformers issue)")
    
    # Build sparse index
    logger.info("Building BM25 sparse index...")
    sparse_retriever = SparseRetriever()
    sparse_retriever.build_index(chunks)
    
    # Save sparse index metadata
    metadata_path = output_path / "bm25_metadata.json"
    with open(metadata_path, 'w') as f:
        # BM25 is in-memory, just save metadata
        json.dump(chunks, f, indent=2)
    logger.info(f"  ✓ BM25 index built")
    
    return dense_retriever, sparse_retriever


def test_retrieval(chunks: List[Dict[str, Any]], 
                  dense_retriever: DenseRetriever,
                  sparse_retriever: SparseRetriever) -> None:
    """Test retrieval on sample queries."""
    logger.info("\n=== Testing Retrieval Quality ===\n")
    
    test_queries = [
        "What is the punishment for culpable homicide?",
        "Section 34 common intention",
        "Definitions of abetment and cognizable offence",
        "Death caused by rash or negligent act",
        "Offences against person",
    ]
    
    for query in test_queries:
        logger.info(f"Query: {query}")
        
        # Sparse retrieval
        sparse_results = sparse_retriever.retrieve(query, top_k=3)
        logger.info(f"  BM25 Results:")
        for i, (metadata, score) in enumerate(sparse_results, 1):
            logger.info(f"    {i}. [{metadata['section_id']}] {metadata['section_title'][:60]} (score: {score:.2f})")
        
        # Dense retrieval
        dense_results = dense_retriever.retrieve(query, top_k=3)
        logger.info(f"  FAISS Results:")
        for i, (metadata, score) in enumerate(dense_results, 1):
            logger.info(f"    {i}. [{metadata['section_id']}] {metadata['section_title'][:60]} (similarity: {score:.2f})")
        
        logger.info("")


def main():
    parser = argparse.ArgumentParser(description="Phase 0 Build Script")
    parser.add_argument("--corpus-dir", default="data/corpus", help="Path to legal corpus")
    parser.add_argument("--output-dir", default="models/faiss_indices/v1", help="Output directory for indices")
    parser.add_argument("--test-only", action="store_true", help="Only run tests, don't rebuild")
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("PHASE 0 - ENVIRONMENT & DATA FOUNDATION")
    logger.info("Building legal corpus indices and validating retrieval")
    logger.info("="*60 + "\n")
    
    # Step 1: Prepare corpus
    if not os.path.exists(args.corpus_dir):
        prepare_sample_corpus()
    
    # Step 2: Chunk corpus
    chunks = chunk_corpus(args.corpus_dir)
    
    if not chunks:
        logger.error("No chunks created. Exiting.")
        sys.exit(1)
    
    # Step 3: Build indices
    logger.info("\nBuilding retrieval indices...")
    dense_retriever, sparse_retriever = build_indices(chunks, args.output_dir)
    
    # Step 4: Test retrieval
    test_retrieval(chunks, dense_retriever, sparse_retriever)
    
    logger.info("\n" + "="*60)
    logger.info("PHASE 0 BUILD COMPLETE")
    logger.info(f"Corpus statistics:")
    logger.info(f"  - Total chunks: {len(chunks)}")
    logger.info(f"  - Average chunk size: {sum(c['token_count'] for c in chunks) / len(chunks):.0f} tokens")
    logger.info(f"  - Indices location: {args.output_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
