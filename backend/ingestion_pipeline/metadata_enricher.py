"""
metadata_enricher.py
---------------------
Enriches document chunks with document-level and chunk-level metadata.
Generates deterministic, unique chunk IDs and content hashes (SHA-256)
to check for duplicates and changes in downstream processing.
"""

import re
import hashlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger("metadata_enricher")

class MetadataEnricher:
    def __init__(self):
        pass

    def slugify(self, text: str) -> str:
        """Converts text into a clean alphanumeric underscore-separated slug."""
        if not text:
            return "general"
        # Convert to lowercase, remove punctuation, replace spaces/dashes with underscores
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s_]', '', slug)
        slug = re.sub(r'[\s_\-]+', '_', slug)
        return slug.strip('_')

    def enrich_chunks(self, chunks: List[Dict[str, Any]], doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Enriches a list of raw chunks with metadata from the document registry,
        attaches deterministic IDs, and creates content hashes.
        
        Args:
            chunks (List[Dict[str, Any]]): The list of chunks from header_chunker.py.
            doc_metadata (Dict[str, Any]): The canonical metadata dictionary of the document.
            
        Returns:
            List[Dict[str, Any]]: The enriched chunks.
        """
        enriched_chunks = []
        section_counters = {}
        doc_id = doc_metadata["document_id"]

        for chunk in chunks:
            section_heading = chunk["section_heading"]
            section_slug = self.slugify(section_heading)
            
            # Keep a sequence counter for chunks within the same section to generate index suffixes (e.g. 001, 002)
            key = f"{doc_id}_{section_slug}"
            section_counters[key] = section_counters.get(key, 0) + 1
            index_str = f"{section_counters[key]:03d}"
            
            # Deterministic Chunk ID: document_id + section_slug + index
            chunk_id = f"{doc_id}_{section_slug}_{index_str}"
            
            # Generate SHA-256 hash of the content for idempotency validation
            content_to_hash = chunk["content"].strip()
            content_hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()
            
            enriched_chunk = {
                "chunk_id": chunk_id,
                "content": chunk["content"],
                "content_hash": content_hash,
                
                # Document-level metadata
                "document_id": doc_id,
                "document_name": doc_metadata["document_name"],
                "document_type": doc_metadata["document_type"],
                "status": doc_metadata["status"],
                "effective_date": doc_metadata.get("effective_date"),
                "account_id": doc_metadata.get("account_id"),
                "customer_name": doc_metadata.get("customer_name"),
                "authority_level": doc_metadata["authority_level"],
                "retrieval_enabled": doc_metadata["retrieval_enabled"],
                
                # Chunk-level metadata
                "section": section_heading,
                "header_path": chunk["header_path"]
            }
            
            enriched_chunks.append(enriched_chunk)
            
        logger.info(f"Enriched {len(enriched_chunks)} chunks for document: {doc_id}")
        return enriched_chunks
