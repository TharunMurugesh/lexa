"""
Dense Retriever using FAISS and Sentence Transformers.
Provides efficient semantic search over legal corpus.
"""

import os
import pickle
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import faiss
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class DenseRetriever:
    """
    Semantic search retriever using FAISS indices and sentence embeddings.
    Optimized for legal domain with BGE-large embeddings.
    """
    
    def __init__(self, embedding_model: str = "sentence-transformers/bge-large-en-v1.5",
                 index_path: Optional[str] = None, metadata_path: Optional[str] = None,
                 device: str = "cuda"):
        """
        Initialize dense retriever.
        
        Args:
            embedding_model: Name/path of sentence transformer model
            index_path: Path to saved FAISS index
            metadata_path: Path to saved metadata pickle
            device: Device to run embeddings on (cuda/cpu)
        """
        self.embedding_model_name = embedding_model
        self.device = device
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # Load embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        try:
            self.model = SentenceTransformer(embedding_model, device=device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
        
        self.index: Optional[faiss.IndexFlatL2] = None
        self.metadata: List[Dict[str, Any]] = []
        
        # Load existing index if provided
        if index_path and metadata_path:
            self.load_index(index_path, metadata_path)
    
    def build_index(self, chunks: List[Dict[str, Any]], batch_size: int = 32) -> None:
        """
        Build FAISS index from list of chunks.
        
        Args:
            chunks: List of chunks with 'text' field and metadata
            batch_size: Batch size for embedding
        """
        logger.info(f"Building FAISS index for {len(chunks)} chunks...")
        
        # Extract texts and metadata
        texts = [c["text"] for c in chunks]
        self.metadata = chunks
        
        # Encode texts in batches
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
        embeddings = np.array(embeddings, dtype=np.float32)
        
        # Create FAISS index
        logger.info(f"Embedding dimension: {embeddings.shape[1]}")
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        
        logger.info(f"Index built successfully. Total vectors: {self.index.ntotal}")
    
    def save_index(self, index_path: str, metadata_path: str) -> None:
        """Save FAISS index and metadata."""
        if self.index is None:
            raise ValueError("No index to save. Build index first.")
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path) or ".", exist_ok=True)
        
        # Save index
        faiss.write_index(self.index, index_path)
        logger.info(f"Saved FAISS index to {index_path}")
        
        # Save metadata
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        logger.info(f"Saved metadata to {metadata_path}")
    
    def load_index(self, index_path: str, metadata_path: str) -> None:
        """Load FAISS index and metadata."""
        try:
            self.index = faiss.read_index(index_path)
            logger.info(f"Loaded FAISS index from {index_path}")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise
        
        try:
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded metadata from {metadata_path} ({len(self.metadata)} chunks)")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            raise
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieve top-k chunks for a query.
        
        Args:
            query: Query text
            top_k: Number of results to return
        
        Returns:
            List of (chunk_metadata, similarity_score) tuples
        """
        if self.index is None:
            raise ValueError("Index not loaded. Load or build index first.")
        
        # Embed query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:  # FAISS returns -1 for unfound results
                continue
            
            metadata = self.metadata[idx]
            # Convert L2 distance to similarity score (0-1)
            # L2 distance to cosine similarity approximation
            similarity = 1.0 / (1.0 + distance)
            results.append((metadata, similarity))
        
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
        if self.index is None:
            raise ValueError("Index not loaded. Load or build index first.")
        
        # Embed all queries
        query_embeddings = self.model.encode(queries, convert_to_numpy=True)
        query_embeddings = np.array(query_embeddings, dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_embeddings, min(top_k, self.index.ntotal))
        
        all_results = []
        for query_idx in range(len(queries)):
            results = []
            for idx, distance in zip(indices[query_idx], distances[query_idx]):
                if idx == -1:
                    continue
                metadata = self.metadata[idx]
                similarity = 1.0 / (1.0 + distance)
                results.append((metadata, similarity))
            all_results.append(results)
        
        return all_results
    
    def add_chunks(self, new_chunks: List[Dict[str, Any]]) -> None:
        """
        Incrementally add new chunks to existing index.
        
        Args:
            new_chunks: List of chunks to add
        """
        if self.index is None:
            raise ValueError("Index not initialized. Build index first.")
        
        logger.info(f"Adding {len(new_chunks)} chunks to existing index...")
        
        # Embed new chunks
        new_texts = [c["text"] for c in new_chunks]
        new_embeddings = self.model.encode(new_texts, batch_size=32, show_progress_bar=True)
        new_embeddings = np.array(new_embeddings, dtype=np.float32)
        
        # Add to index
        self.index.add(new_embeddings)
        self.metadata.extend(new_chunks)
        
        logger.info(f"Index now contains {self.index.ntotal} vectors")
