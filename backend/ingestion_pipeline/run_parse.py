import sys
from pathlib import Path

# Add the workspace root to sys.path so we can import from ingestion_pipeline
workspace_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(workspace_dir))

from ingestion_pipeline.docling_parser import DoclingParser

def main():
    pdf_path = workspace_dir / "AI Agent Assessment - Candidate Pack" / "01_Support_Policy_v3_CURRENT.pdf"
    if not pdf_path.exists():
         pdf_path = workspace_dir.parent / "AI Agent Assessment - Candidate Pack" / "01_Support_Policy_v3_CURRENT.pdf"
         
    output_md_path = workspace_dir / "ingestion_pipeline" / "data" / "markdown" / "support_policy_v3.md"
    
    print(f"Reading from: {pdf_path}")
    print(f"Saving to: {output_md_path}")
    
    parser = DoclingParser()
    markdown_content = parser.parse_pdf(pdf_path, output_md_path)
    
    print("\n--- Parsed Markdown Output (First 1500 characters) ---")
    print(markdown_content[:1500])
    print("\n--- End of Snippet ---")
    print(f"Total parsed length: {len(markdown_content)} characters.")

if __name__ == "__main__":
    main()
