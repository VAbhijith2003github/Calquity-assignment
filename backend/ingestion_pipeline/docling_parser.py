import logging
from pathlib import Path
from docling.document_converter import DocumentConverter

# Set up logging for this module
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("docling_parser")

class DoclingParser:
    """
    Parser wrapper that uses Docling to convert PDF files into structured Markdown.
    It preserves headings, lists, tables, and document hierarchy.
    """
    def __init__(self):
        logger.info("Initializing Docling DocumentConverter (this may download models on first load)...")
        self.converter = DocumentConverter()
        logger.info("Docling DocumentConverter initialized successfully.")

    def parse_pdf(self, pdf_path: str | Path, output_md_path: str | Path) -> str:
        """
        Parses a PDF file and exports the result as Markdown to the target file.
        Returns the parsed markdown string.
        """
        pdf_path = Path(pdf_path)
        output_md_path = Path(output_md_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"Source PDF file does not exist at: {pdf_path}")

        logger.info(f"Starting conversion for: {pdf_path.name}")
        try:
            # Convert PDF using Docling
            result = self.converter.convert(pdf_path)
            
            # Export the document structure to standard Markdown representation
            markdown_content = result.document.export_to_markdown()
            
            # Ensure the parent directory for output Markdown exists
            output_md_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write markdown out to disk
            output_md_path.write_text(markdown_content, encoding="utf-8")
            logger.info(f"Successfully saved parsed Markdown to: {output_md_path}")
            
            return markdown_content
        except Exception as e:
            logger.error(f"Failed to parse document '{pdf_path.name}'. Stage: Docling conversion. Error: {e}")
            raise e
