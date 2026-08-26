"""
embedding_service.py
--------------------
Handles local embedding generation using the SentenceTransformers library.
Abstracts the embedding generation layer to allow switching between different
models or external APIs (e.g. OpenAI) in the future.
"""

import abc
import logging
from typing import List

logger = logging.getLogger("embedding_service")

class EmbeddingService(abc.ABC):
    """
    Abstract Base Class for generating vector embeddings.
    """
    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of text documents.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for.
            
        Returns:
            List[List[float]]: List of float lists containing the vector representations.
        """
        pass

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Embeds a single query string.
        
        Args:
            text (str): The search query.
            
        Returns:
            List[float]: The vector representation of the query.
        """
        pass


class SentenceTransformerEmbeddingService(EmbeddingService):
    """
    Generates embeddings locally using the SentenceTransformer library.
    Defaults to the lightweight 'all-MiniLM-L6-v2' model (384 dimensions).
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None  # Lazily instantiated on the first embedding call

    def _lazy_init(self):
        """Loads the model into memory only when needed."""
        if self.model is None:
            logger.info(f"Loading SentenceTransformer model '{self.model_name}' (runs locally)...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"SentenceTransformer model '{self.model_name}' loaded successfully.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._lazy_init()
        # Generates embeddings as numpy arrays, then converts them to python lists
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        self._lazy_init()
        # Generates embedding for a single text string
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding.tolist()
