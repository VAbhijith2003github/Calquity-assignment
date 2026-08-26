"""
vector_store.py
---------------
Connects to the Qdrant cloud cluster and handles uploading of document chunk
embeddings and metadata. Supports upsert, deletion, and hash-based idempotency
checking to avoid re-uploading unchanged chunks.

Qdrant Collection: parcelpilot_documents
Embedding Dimensions: 384 (all-MiniLM-L6-v2)
"""

import json
import logging
import uuid
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    FilterSelector,
    PayloadSchemaType,
)

import os
from pathlib import Path
from dotenv import load_dotenv

# Walk up directories to find the .env file dynamically
env_path = None
for parent in Path(__file__).resolve().parents:
    candidate = parent / ".env"
    if candidate.exists():
        env_path = candidate
        break

if env_path:
    load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("vector_store")

# ── Qdrant Cloud Credentials ────────────────────────────────────────────────
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "parcelpilot_documents"
EMBEDDING_DIM = 384   # all-MiniLM-L6-v2 output dimension


class QdrantVectorStore:
    """
    Manages storage, upsert, and retrieval of document chunk embeddings
    in the Qdrant cloud cluster.
    """

    def __init__(self):
        logger.info(f"Connecting to Qdrant cluster at {QDRANT_URL}...")
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self._ensure_collection()

    # ── Collection Management ────────────────────────────────────────────────

    def _ensure_collection(self):
        """Creates the collection if it does not already exist."""
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            logger.info(f"Collection '{COLLECTION_NAME}' not found. Creating...")
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            logger.info(f"Collection '{COLLECTION_NAME}' created successfully.")
            # Create payload indexes for every field used in metadata filters.
            # Qdrant requires explicit indexes before filtering on a payload field.
            filterable_fields = {
                "document_id":      PayloadSchemaType.KEYWORD,
                "account_id":       PayloadSchemaType.KEYWORD,
                "document_type":    PayloadSchemaType.KEYWORD,
                "status":           PayloadSchemaType.KEYWORD,
                "retrieval_enabled": PayloadSchemaType.BOOL,
            }
            for field, schema_type in filterable_fields.items():
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field,
                    field_schema=schema_type,
                )
                logger.info(f"Created payload index: '{field}'")
        else:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists. Reusing.")

    # ── Idempotency Helpers ──────────────────────────────────────────────────

    def get_document_hashes(self, document_id: str) -> Dict[str, str]:
        """
        Retrieves all existing chunk_id → content_hash pairs for a document.
        Used by the pipeline to decide whether to skip or re-embed chunks.
        """
        results, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
            with_payload=True,
            with_vectors=False,
            limit=1000,   # Adjust if documents produce > 1000 chunks
        )
        return {
            pt.payload.get("chunk_id"): pt.payload.get("content_hash", "")
            for pt in results
            if pt.payload
        }

    def delete_document_chunks(self, document_id: str):
        """Removes all stored points belonging to a given document_id."""
        logger.info(f"Deleting existing chunks for document_id='{document_id}'...")
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                )
            ),
        )
        logger.info(f"Deleted all chunks for document_id='{document_id}'.")

    # ── Upsert ───────────────────────────────────────────────────────────────

    def upsert_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ):
        """
        Uploads chunks with their embeddings and metadata to Qdrant.
        Each point uses a deterministic UUID derived from the chunk_id
        so re-uploads always overwrite the same point.
        """
        if not chunks:
            logger.warning("No chunks to upsert.")
            return

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            # Derive a deterministic UUID from chunk_id for stable point IDs
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))

            # Qdrant payload: flatten any list values to JSON strings
            payload = self._prepare_payload(chunk)

            points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

        logger.info(f"Upserting {len(points)} points to '{COLLECTION_NAME}'...")
        self.client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info(f"Upserted {len(points)} chunks successfully.")

    # ── Search ───────────────────────────────────────────────────────────────

    def search(
        self,
        query_embedding: List[float],
        account_id: Optional[str] = None,
        document_types: Optional[List[str]] = None,
        include_deprecated: bool = False,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Performs a semantic search against the Qdrant collection with optional
        metadata filters for account, document type, and status.
        """
        must_conditions = []

        # 1. Exclude deprecated and retrieval-disabled documents by default
        if not include_deprecated:
            must_conditions.append(
                FieldCondition(key="retrieval_enabled", match=MatchValue(value=True))
            )

        # 2. Account-level scoping
        #    - account_id given  → return that customer's agreement + general docs (account_id = "")
        #    - no account_id     → return only general docs
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

        # 3. Optional document type filter
        if document_types:
            must_conditions.append(
                FieldCondition(key="document_type", match=MatchAny(any=document_types))
            )

        search_filter = Filter(must=must_conditions) if must_conditions else None

        res = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "chunk_id": hit.payload.get("chunk_id"),
                "content": hit.payload.get("content"),
                "score": hit.score,
                "metadata": self._restore_payload(hit.payload),
            }
            for hit in res.points
        ]

    # ── Payload Helpers ──────────────────────────────────────────────────────

    def _prepare_payload(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts a chunk dict into a Qdrant-compatible payload.
        Lists are serialized to JSON strings; None values use empty strings
        for fields that need to be filterable.
        """
        payload = {}
        for key, value in chunk.items():
            if isinstance(value, list):
                payload[key] = json.dumps(value)          # e.g. header_path
            elif value is None:
                payload[key] = ""                         # Qdrant can filter on ""
            else:
                payload[key] = value
        return payload

    def _restore_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restores a payload retrieved from Qdrant back to its original Python types.
        JSON-encoded lists are decoded; empty strings for nullable fields become None.
        """
        nullable_fields = {"account_id", "effective_date", "customer_name"}
        restored = {}
        for key, value in payload.items():
            if isinstance(value, str) and value.startswith("["):
                try:
                    restored[key] = json.loads(value)
                    continue
                except json.JSONDecodeError:
                    pass
            if isinstance(value, str) and value == "" and key in nullable_fields:
                restored[key] = None
            else:
                restored[key] = value
        return restored
