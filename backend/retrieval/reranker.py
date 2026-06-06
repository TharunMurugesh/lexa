"""
Cross-Encoder Reranker for Legal Retrieval.
Refines top-k results from sparse/dense retrieval using semantic relevance.
"""

from typing import List, Tuple, Dict, Any
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Rerank passages using a cross-encoder model.
    More accurate than embedding-based similarity but slower.
    Recommended for top-k reranking (e.g., rerank top-40 to top-5).
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2", device: str = "cuda"):
        """
        Initialize reranker.
        
        Args:
            model_name: Name/path of cross-encoder model
            device: Device to run on (cuda/cpu)
        """
        self.model_name = model_name
        self.device = device
        
        logger.info(f"Loading cross-encoder model: {model_name}")
        try:
            self.model = CrossEncoder(model_name, device=device, max_length=512)
        except Exception as e:
            logger.error(f"Failed to load cross-encoder: {e}")
            raise
    
    def rerank(self, query: str, passages: List[Tuple[Dict[str, Any], float]], 
               top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rerank passages for a query.
        
        Args:
            query: Query text
            passages: List of (metadata, initial_score) tuples
            top_k: Number of top results to return
        
        Returns:
            List of (metadata, rerank_score) tuples, sorted by score
        """
        if not passages:
            return []
        
        # Extract passage texts and metadata
        passage_texts = [p[0]["text"] for p in passages]
        metadata_list = [p[0] for p in passages]
        
        # Create query-passage pairs
        pairs = [[query, passage] for passage in passage_texts]
        
        # Score with cross-encoder
        logger.debug(f"Reranking {len(pairs)} passages for query: {query[:50]}...")
        scores = self.model.predict(pairs)
        
        # Sort by score and return top-k
        scored_results = list(zip(metadata_list, scores))
        sorted_results = sorted(scored_results, key=lambda x: x[1], reverse=True)
        
        return sorted_results[:top_k]
    
    def rerank_batch(self, query: str, passage_batches: List[List[Dict[str, Any]]], 
                    top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rerank passages when too many for single batch.
        Useful for large retrieval result sets.
        
        Args:
            query: Query text
            passage_batches: List of lists of passage metadata
            top_k: Number of top results to return
        
        Returns:
            List of (metadata, rerank_score) tuples
        """
        all_results = []
        
        for batch in passage_batches:
            passage_texts = [p["text"] for p in batch]
            pairs = [[query, passage] for passage in passage_texts]
            scores = self.model.predict(pairs)
            all_results.extend(list(zip(batch, scores)))
        
        # Sort and return top-k
        sorted_results = sorted(all_results, key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
