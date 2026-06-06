"""
Hybrid Retriever combining BM25, dense search, and cross-encoder reranking.
This is the primary retrieval interface for LEXA legal corpus queries.
"""

from typing import List, Tuple, Dict, Any, Optional
from .sparse_retriever import SparseRetriever, RecipientRankFusion
from .dense_retriever import DenseRetriever
from .reranker import CrossEncoderReranker
import logging

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Multi-stage retrieval pipeline:
    1. Retrieve with BM25 (sparse)
    2. Retrieve with FAISS (dense)
    3. Merge with Reciprocal Rank Fusion
    4. Rerank with cross-encoder
    """
    
    def __init__(self, 
                 dense_retriever: DenseRetriever,
                 sparse_retriever: SparseRetriever,
                 reranker: Optional[CrossEncoderReranker] = None,
                 top_k_sparse: int = 20,
                 top_k_dense: int = 20,
                 top_k_reranked: int = 5):
        """
        Initialize hybrid retriever.
        
        Args:
            dense_retriever: Initialized DenseRetriever instance
            sparse_retriever: Initialized SparseRetriever instance
            reranker: Optional CrossEncoderReranker for final ranking
            top_k_sparse: Number of results from BM25
            top_k_dense: Number of results from FAISS
            top_k_reranked: Number of final results after reranking
        """
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.reranker = reranker
        self.top_k_sparse = top_k_sparse
        self.top_k_dense = top_k_dense
        self.top_k_reranked = top_k_reranked
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve and rerank results for a query.
        
        Args:
            query: Legal query
        
        Returns:
            List of ranked passages with metadata
        """
        logger.info(f"Hybrid retrieval for: {query[:60]}...")
        
        # Stage 1: Sparse retrieval (BM25)
        sparse_results = self.sparse_retriever.retrieve(query, self.top_k_sparse)
        logger.debug(f"  BM25: {len(sparse_results)} results")
        
        # Stage 2: Dense retrieval (FAISS)
        dense_results = self.dense_retriever.retrieve(query, self.top_k_dense)
        logger.debug(f"  FAISS: {len(dense_results)} results")
        
        # Stage 3: Reciprocal Rank Fusion
        merged_results = RecipientRankFusion.fuse(sparse_results, dense_results)
        # Take top results before reranking
        merged_results = merged_results[:self.top_k_sparse + self.top_k_dense]
        logger.debug(f"  Merged (RRF): {len(merged_results)} results")
        
        # Stage 4: Cross-encoder reranking (if available)
        if self.reranker:
            final_results = self.reranker.rerank(query, merged_results, self.top_k_reranked)
            logger.debug(f"  Reranked: {len(final_results)} results")
            
            # Return only metadata with added score
            return [
                {
                    **metadata,
                    "retrieval_score": float(score),
                    "retrieval_rank": rank
                }
                for rank, (metadata, score) in enumerate(final_results)
            ]
        else:
            # Return merged results without reranking
            return [
                {
                    **metadata,
                    "retrieval_score": float(score),
                    "retrieval_rank": rank
                }
                for rank, (metadata, score) in enumerate(merged_results[:self.top_k_reranked])
            ]
    
    def retrieve_batch(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Retrieve results for multiple queries.
        
        Args:
            queries: List of queries
        
        Returns:
            List of result lists
        """
        all_results = []
        for query in queries:
            results = self.retrieve(query)
            all_results.append(results)
        return all_results
