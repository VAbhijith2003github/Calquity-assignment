"""
markdown_normalizer.py
----------------------
Provides a normalization layer to clean up Markdown text extracted from PDFs.
It cleans up excessive whitespace, page headers/footers, page numbers,
and minor formatting inconsistencies without altering the original content.
"""

import re
import logging

logger = logging.getLogger("markdown_normalizer")

class MarkdownNormalizer:
    def __init__(self):
        pass

    def normalize(self, text: str) -> str:
        """
        Cleans and normalizes markdown text.
        
        Args:
            text (str): The raw markdown string extracted from a PDF.
            
        Returns:
            str: The cleaned and normalized markdown string.
        """
        if not text:
            return ""

        # Step 1: Remove common page number indicators and HTML page comments
        # Examples: "Page 1", "Page 1 of 12", "<!-- Page 5 -->", "--- Page 3 ---", "12"
        # We process these line-by-line using multiline regex flags
        cleaned = text
        
        # Match lines with page numbers optionally enclosed by comment tags, dashes, or just numbers
        cleaned = re.sub(r'^\s*Page\s+\d+(?:\s+of\s+\d+)?\s*$', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
        cleaned = re.sub(r'^\s*<!--\s*Page\s*\d+\s*-->\s*$', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
        cleaned = re.sub(r'^---\s*Page\s*\d+\s*---$', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
        cleaned = re.sub(r'^\s*\d+\s*$', '', cleaned, flags=re.MULTILINE)

        # Step 2: Fix missing spaces after heading hashes (e.g., "##Heading" -> "## Heading")
        cleaned = re.sub(r'^([#]{1,6})([^#\s])', r'\1 \2', cleaned, flags=re.MULTILINE)

        # Step 3: Fix missing spaces after list bullets (e.g., "-item" -> "- item")
        cleaned = re.sub(r'^([*\-+])([^ \-+\*\s])', r'\1 \2', cleaned, flags=re.MULTILINE)

        # Step 4: Remove trailing whitespaces on each line
        cleaned = re.sub(r'[ \t]+$', '', cleaned, flags=re.MULTILINE)

        # Step 5: Collapse three or more consecutive newlines down to exactly two (single blank line between blocks)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        # Step 6: Trim surrounding whitespace from the entire document
        cleaned = cleaned.strip()

        logger.info("Markdown normalization completed successfully.")
        return cleaned
