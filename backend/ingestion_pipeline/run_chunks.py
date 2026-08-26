import sys
import json
from pathlib import Path

# Ensure import path works
workspace_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(workspace_dir))

from ingestion_pipeline.markdown_normalizer import MarkdownNormalizer
from ingestion_pipeline.header_chunker import HeaderChunker
from ingestion_pipeline.metadata_enricher import MetadataEnricher
from ingestion_pipeline.document_registry import DOCUMENT_REGISTRY

def main():
    md_path = workspace_dir / "ingestion_pipeline" / "data" / "markdown" / "support_policy_v3.md"
    
    if not md_path.exists():
        print(f"Error: Markdown file not found at {md_path}. Run parser first!")
        sys.exit(1)
        
    print(f"Reading markdown from: {md_path.name}")
    markdown_content = md_path.read_text(encoding="utf-8")
    
    # 1. Normalize
    normalizer = MarkdownNormalizer()
    normalized_content = normalizer.normalize(markdown_content)
    
    # 2. Chunk
    chunker = HeaderChunker()
    doc_metadata = DOCUMENT_REGISTRY["01_Support_Policy_v3_CURRENT.pdf"]
    raw_chunks = chunker.chunk_markdown(normalized_content, default_doc_title=doc_metadata["document_name"])
    
    # 3. Enrich
    enricher = MetadataEnricher()
    final_chunks = enricher.enrich_chunks(raw_chunks, doc_metadata)
    
    print(f"\nSuccessfully generated {len(final_chunks)} chunks.\n")
    
    # Print the chunks details in JSON format
    for idx, chunk in enumerate(final_chunks):
        print(f"--- Chunk {idx + 1} ---")
        print(json.dumps(chunk, indent=2, ensure_ascii=False))
        print("-" * 60)

if __name__ == "__main__":
    main()
