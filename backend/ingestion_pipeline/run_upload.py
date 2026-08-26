"""
run_upload.py
-------------
End-to-end runner for the ParcelPilot ingestion pipeline.

For a given PDF it will:
  1. Parse PDF → Markdown (Docling)
  2. Normalize Markdown
  3. Chunk by headers
  4. Enrich chunks with metadata + deterministic IDs + content hashes
  5. Generate embeddings (local SentenceTransformer)
  6. Upload embeddings + metadata to Qdrant cloud

Usage:
    # Ingest just the current support policy
    python run_upload.py

    # Force re-upload even if the document is unchanged
    python run_upload.py --force

    # Ingest all 6 documents
    python run_upload.py --all
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Allow imports from the repo root
workspace_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(workspace_dir))

from ingestion_pipeline.docling_parser import DoclingParser
from ingestion_pipeline.markdown_normalizer import MarkdownNormalizer
from ingestion_pipeline.header_chunker import HeaderChunker
from ingestion_pipeline.metadata_enricher import MetadataEnricher
from ingestion_pipeline.embedding_service import SentenceTransformerEmbeddingService
from ingestion_pipeline.vector_store import QdrantVectorStore
from ingestion_pipeline.document_registry import DOCUMENT_REGISTRY

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_upload")

# ── Paths ─────────────────────────────────────────────────────────────────────
# Find PDF directory (prioritise backend-internal, fall back to root-level)
PDF_DIR = workspace_dir / "AI Agent Assessment - Candidate Pack"
if not (PDF_DIR / "01_Support_Policy_v3_CURRENT.pdf").exists():
    PDF_DIR = workspace_dir.parent / "AI Agent Assessment - Candidate Pack"

MD_DIR     = workspace_dir / "ingestion_pipeline" / "data" / "markdown"
CHUNKS_DIR = workspace_dir / "ingestion_pipeline" / "data" / "processed"
MD_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


def ingest_document(
    filename: str,
    doc_meta: dict,
    parser: DoclingParser,
    normalizer: MarkdownNormalizer,
    chunker: HeaderChunker,
    enricher: MetadataEnricher,
    embedder: SentenceTransformerEmbeddingService,
    store: QdrantVectorStore,
    force: bool = False,
) -> dict:
    """
    Runs the full ingestion pipeline for a single document.
    Returns a summary dict with status and chunk count.
    """
    doc_id   = doc_meta["document_id"]
    doc_name = doc_meta["document_name"]
    pdf_path = PDF_DIR / filename
    md_path  = MD_DIR / f"{doc_id}.md"

    logger.info(f"━━━ {doc_name} ({filename})")

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return {"document_id": doc_id, "status": "failed", "error": "PDF file not found"}

    try:
        # ── Step 1: Markdown ─────────────────────────────────────────────────
        # Reuse cached .md to skip heavy Docling conversion when possible
        if md_path.exists() and not force:
            logger.info("Using cached Markdown file.")
            markdown = md_path.read_text(encoding="utf-8")
        else:
            markdown = parser.parse_pdf(pdf_path, md_path)
            logger.info("Parsed with Docling → Markdown saved.")

        # ── Step 2: Normalize ────────────────────────────────────────────────
        markdown = normalizer.normalize(markdown)

        # ── Step 3: Chunk ────────────────────────────────────────────────────
        raw_chunks = chunker.chunk_markdown(markdown, default_doc_title=doc_name)

        # ── Step 4: Enrich (metadata + IDs + hashes) ────────────────────────
        enriched_chunks = enricher.enrich_chunks(raw_chunks, doc_meta)
        logger.info(f"Chunks created: {len(enriched_chunks)}")

        # ── Step 5: Idempotency check ────────────────────────────────────────
        new_hashes = {c["chunk_id"]: c["content_hash"] for c in enriched_chunks}
        existing_hashes = store.get_document_hashes(doc_id)

        if not force and existing_hashes == new_hashes:
            logger.info("Document unchanged in Qdrant — skipping upload.")
            return {"document_id": doc_id, "status": "skipped", "chunks_count": len(enriched_chunks)}

        # ── Step 6: Embed ────────────────────────────────────────────────────
        texts = [c["content"] for c in enriched_chunks]
        embeddings = embedder.embed_documents(texts)
        logger.info(f"Embeddings generated: {len(embeddings)}")

        # Remove stale points before upserting fresh ones
        if existing_hashes:
            store.delete_document_chunks(doc_id)

        # ── Step 7: Upload to Qdrant ─────────────────────────────────────────
        store.upsert_chunks(doc_id, enriched_chunks, embeddings)
        logger.info("Uploaded to Qdrant ✓")

        # Save chunk manifest to disk for local inspection
        chunks_path = CHUNKS_DIR / f"{doc_id}_chunks.json"
        chunks_path.write_text(json.dumps(enriched_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Chunk manifest saved → {chunks_path.name}")

        return {"document_id": doc_id, "status": "ingested", "chunks_count": len(enriched_chunks)}

    except Exception as exc:
        logger.error(f"Failed [{doc_name}]: {exc}")
        return {"document_id": doc_id, "status": "failed", "error": str(exc)}


def print_summary(results: list):
    """Prints a clean summary table after the pipeline run."""
    print("\n" + "=" * 60)
    print("  Ingestion Summary")
    print("=" * 60)
    print(f"  {'Document ID':<45} {'Status':<10} {'Chunks'}")
    print("-" * 60)
    for r in results:
        print(f"  {r['document_id']:<45} {r['status']:<10} {r.get('chunks_count', '-')}")
    print("=" * 60)

    ingested = sum(1 for r in results if r["status"] == "ingested")
    skipped  = sum(1 for r in results if r["status"] == "skipped")
    failed   = sum(1 for r in results if r["status"] == "failed")
    print(f"  [OK] Ingested: {ingested}  [SKIP] Skipped: {skipped}  [FAIL] Failed: {failed}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="ParcelPilot Qdrant Ingestion Runner")
    parser.add_argument("--force", action="store_true", help="Re-upload all chunks even if unchanged.")
    parser.add_argument("--all",   action="store_true", help="Ingest all 6 documents, not just the support policy.")
    args = parser.parse_args()

    # Decide which documents to process
    if args.all:
        docs_to_process = DOCUMENT_REGISTRY
    else:
        # Default: only ingest the current support policy as a quick test
        docs_to_process = {
            "01_Support_Policy_v3_CURRENT.pdf": DOCUMENT_REGISTRY["01_Support_Policy_v3_CURRENT.pdf"]
        }

    print(f"\n{'='*60}")
    print(f"  ParcelPilot Qdrant Ingestion Pipeline")
    print(f"  Documents: {len(docs_to_process)}  |  Force: {args.force}")
    print(f"{'='*60}\n")

    # Initialise all pipeline components once
    docling_parser = DoclingParser()
    normalizer     = MarkdownNormalizer()
    chunker        = HeaderChunker()
    enricher       = MetadataEnricher()
    embedder       = SentenceTransformerEmbeddingService(model_name="all-MiniLM-L6-v2")
    store          = QdrantVectorStore()

    results = []
    for filename, doc_meta in docs_to_process.items():
        result = ingest_document(
            filename=filename,
            doc_meta=doc_meta,
            parser=docling_parser,
            normalizer=normalizer,
            chunker=chunker,
            enricher=enricher,
            embedder=embedder,
            store=store,
            force=args.force,
        )
        results.append(result)

    print_summary(results)

    # Exit with error code if any document failed
    if any(r["status"] == "failed" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
