import abc
import logging
from typing import List

logger = logging.getLogger("retrieval.embedding_service")

class EmbeddingService(abc.ABC):
    """
    Abstract Base Class for generating vector embeddings.
    """
    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Embeds a single query string.
        """
        pass

class SentenceTransformerEmbeddingService(EmbeddingService):
    """
    Generates embeddings locally using the SentenceTransformer library.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

    def _lazy_init(self):
        if self.model is None:
            logger.info(f"Loading SentenceTransformer model '{self.model_name}' for query embedding...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer model loaded successfully.")

    def embed_query(self, text: str) -> List[float]:
        self._lazy_init()
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding.tolist()
