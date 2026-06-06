"""
Sparse Retriever using BM25.
Provides keyword/exact-match search for legal corpus.
Essential for section numbers and legal terminology searches.
"""

from typing import List, Tuple, Dict, Any
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger(__name__)


class SparseRetriever:
    """
    Sparse (keyword-based) retriever using BM25.
    Excellent for:
    - Exact section number matching (e.g., "Section 302")
    - Legal terminology searches (e.g., "IPC", "BNS")
    - Structured queries with specific phrases
    """
    
    def __init__(self):
        """Initialize sparse retriever."""
        self.bm25: BM25Okapi = None
        self.metadata: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
    
    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from chunks.
        
        Args:
            chunks: List of chunks with 'text' field and metadata
        """
        logger.info(f"Building BM25 index for {len(chunks)} chunks...")
        
        # Store metadata and tokenized corpus
        self.metadata = chunks
        
        # Tokenize: simple whitespace tokenization with section-aware cleaning
        self.corpus_tokens = []
        for chunk in chunks:
            # Simple tokenization: split by whitespace and clean
            text = chunk["text"].lower()
            # Enhance section/act references (e.g., "Section 302" → "section", "302")
            text = self._enhance_legal_terms(text)
            tokens = text.split()
            self.corpus_tokens.append(tokens)
        
        # Build BM25
        self.bm25 = BM25Okapi(self.corpus_tokens)
        logger.info(f"BM25 index built. Corpus size: {len(self.corpus_tokens)} documents")
    
    def _enhance_legal_terms(self, text: str) -> str:
        """Enhance legal terminology for better keyword matching."""
        # Keep section/act numbers as separate tokens
        text = text.replace("section ", "section ")
        text = text.replace("section\t", "section\t")
        return text
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve top-k chunks for a query using BM25.
        
        Args:
            query: Query text
            top_k: Number of results to return
        
        Returns:
            List of (chunk_metadata, bm25_score) tuples
        """
        if self.bm25 is None:
            raise ValueError("Index not built. Build index first.")
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                metadata = self.metadata[idx]
                score = scores[idx]
                results.append((metadata, score))
        
        return results
    
    def retrieve_batch(self, queries: List[str], top_k: int = 5) -> List[List[Tuple[Dict[str, Any], float]]]:
        """
        Retrieve results for multiple queries.
        
        Args:
            queries: List of query texts
            top_k: Number of results per query
        
        Returns:
            List of result lists
        """
        all_results = []
        for query in queries:
            results = self.retrieve(query, top_k)
            all_results.append(results)
        return all_results


class RecipientRankFusion:
    """
    Combine BM25 and dense retrieval results using Reciprocal Rank Fusion.
    Merges diverse ranking signals for better overall retrieval quality.
    """
    
    @staticmethod
    def fuse(sparse_results: List[Tuple[Dict[str, Any], float]], 
             dense_results: List[Tuple[Dict[str, Any], float]],
             k: int = 60) -> List[Tuple[Dict[str, Any], float]]:
        """
        Fuse sparse and dense retrieval results.
        
        Args:
            sparse_results: Results from BM25 (metadata, score) tuples
            dense_results: Results from dense retrieval (metadata, score) tuples
            k: RRF parameter (usually 60)
        
        Returns:
            Fused results sorted by combined RRF score
        """
        # Build rank dictionaries
        ranks = {}
        
        # Sparse ranks
        for rank, (metadata, _score) in enumerate(sparse_results):
            chunk_id = metadata.get("id", str(metadata))
            rrf_score = 1.0 / (k + rank + 1)
            ranks[chunk_id] = ranks.get(chunk_id, 0) + rrf_score
        
        # Dense ranks
        for rank, (metadata, _score) in enumerate(dense_results):
            chunk_id = metadata.get("id", str(metadata))
            rrf_score = 1.0 / (k + rank + 1)
            ranks[chunk_id] = ranks.get(chunk_id, 0) + rrf_score
        
        # Create metadata lookup
        all_metadata = {}
        for metadata, _ in sparse_results + dense_results:
            chunk_id = metadata.get("id", str(metadata))
            all_metadata[chunk_id] = metadata
        
        # Sort by RRF score and return
        sorted_results = sorted(ranks.items(), key=lambda x: x[1], reverse=True)
        
        return [(all_metadata[chunk_id], score) for chunk_id, score in sorted_results]
