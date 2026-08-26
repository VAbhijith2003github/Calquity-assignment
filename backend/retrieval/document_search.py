import json
import logging
import re
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

from .config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, EMBEDDING_MODEL_NAME
from .embedding_service import SentenceTransformerEmbeddingService

logger = logging.getLogger("retrieval.document_search")

class DocumentSearcher:
    """
    Search service to retrieve relevant document chunks from Qdrant 
    with robust scoping and metadata filtering.
    """
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.embedder = SentenceTransformerEmbeddingService(model_name=EMBEDDING_MODEL_NAME)

    def search_documents(
        self,
        query: str,
        account_id: Optional[str] = None,
        document_types: Optional[List[str]] = None,
        include_deprecated: bool = False,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic search against Qdrant with metadata filters.
        
        Args:
            query (str): The search query.
            account_id (str | None): Optional customer account ID.
            document_types (list | None): Optional list of document types to filter by.
            include_deprecated (bool): Whether to include deprecated support policies.
            top_k (int): Number of top results to return.
            
        Returns:
            List[Dict[str, Any]]: List of matching chunks with metadata.
        """
        # 1. Embed query text
        query_embedding = self.embedder.embed_query(query)
        
        # 2. Build metadata filter conditions
        must_conditions = []
        
        # Filtering for deprecated documents (retrieval_enabled=False)
        if not include_deprecated:
            must_conditions.append(
                FieldCondition(key="retrieval_enabled", match=MatchValue(value=True))
            )
            
        # Filtering for account boundaries:
        # If account_id matches ACCT-001, include ACCT-001 documents OR general documents (account_id = "")
        # If account_id is None, include ONLY general documents (account_id = "")
        if account_id:
            must_conditions.append(
                Filter(
                    should=[
                        FieldCondition(key="account_id", match=MatchValue(value=account_id)),
                        FieldCondition(key="account_id", match=MatchValue(value="")),
                    ]
                )
            )
        else:
            must_conditions.append(
                FieldCondition(key="account_id", match=MatchValue(value=""))
            )
            
        # Document types filter
        if document_types:
            must_conditions.append(
                FieldCondition(key="document_type", match=MatchAny(any=document_types))
            )
            
        search_filter = Filter(must=must_conditions) if must_conditions else None
        
        # 3. Perform Qdrant query using the modern query_points API
        # Retrieve a modest candidate set before re-ranking.  Pure semantic
        # top-k can otherwise favour a broadly related section (for example,
        # escalation) over a section containing the exact requested target.
        candidate_limit = max(top_k * 4, 10)
        res = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=search_filter,
            limit=candidate_limit,
            with_payload=True
        )
        
        # 4. Format and restore metadata structures
        formatted = []
        for hit in res.points:
            if not hit.payload:
                continue
                
            payload = hit.payload
            
            # Restore JSON fields and None values
            restored_meta = {}
            nullable_fields = {"account_id", "effective_date", "customer_name"}
            
            for key, val in payload.items():
                if isinstance(val, str) and val.startswith("["):
                    try:
                        restored_meta[key] = json.loads(val)
                        continue
                    except json.JSONDecodeError:
                        pass
                
                if isinstance(val, str) and val == "" and key in nullable_fields:
                    restored_meta[key] = None
                else:
                    restored_meta[key] = val
                    
            formatted.append({
                "chunk_id": restored_meta.get("chunk_id"),
                "content": restored_meta.get("content"),
                "score": hit.score,
                "metadata": restored_meta
            })
            
        query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))

        def rerank_score(result: Dict[str, Any]) -> tuple:
            metadata = result["metadata"]
            searchable = " ".join(
                str(metadata.get(field, ""))
                for field in ("document_name", "section", "header_path", "content")
            ).lower()
            tokens = set(re.findall(r"[a-z0-9]+", searchable))
            lexical_matches = len(query_terms & tokens)
            exact_phrase = " ".join(re.findall(r"[a-z0-9]+", query.lower()))
            phrase_match = int(exact_phrase in " ".join(re.findall(r"[a-z0-9]+", searchable)))
            return (phrase_match, lexical_matches, result["score"])

        formatted.sort(key=rerank_score, reverse=True)
        return formatted[:top_k]

# Expose function-based API wrapper
def search_documents(
    query: str,
    account_id: Optional[str] = None,
    document_types: Optional[List[str]] = None,
    include_deprecated: bool = False,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    searcher = DocumentSearcher()
    return searcher.search_documents(
        query=query,
        account_id=account_id,
        document_types=document_types,
        include_deprecated=include_deprecated,
        top_k=top_k
    )
