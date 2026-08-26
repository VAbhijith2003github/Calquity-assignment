"""
header_chunker.py
------------------
Chunks Markdown text semantically using Markdown heading levels (# through ######).
Tracks the header hierarchy tree, keeps tables intact, and splits oversized
sections at paragraph boundaries to preserve semantic coherence.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("header_chunker")

class HeaderChunker:
    def __init__(self, max_chunk_chars: int = 2500):
        """
        Args:
            max_chunk_chars (int): The maximum character limit for any individual chunk.
                                   If a section is larger than this, it will be split on paragraph breaks.
        """
        self.max_chunk_chars = max_chunk_chars

    def chunk_markdown(self, markdown_text: str, default_doc_title: str) -> List[Dict[str, Any]]:
        """
        Parses Markdown text and splits it into semantic chunks based on header hierarchy.
        
        Args:
            markdown_text (str): The cleaned markdown text.
            default_doc_title (str): Fallback title representing the document root.
            
        Returns:
            List[Dict[str, Any]]: A list of raw chunk dictionaries containing:
                                  - "header_path": List[str] representing the heading tree
                                  - "section_heading": str (the current section's header)
                                  - "content": str (the text content of the chunk)
        """
        lines = markdown_text.split('\n')
        sections = []
        
        # Track current header path by level (1 to 6)
        current_headers = {1: default_doc_title}
        current_section_lines = []
        current_level = 1
        
        # Matches headings like: "# Heading 1", "## Heading 2", etc.
        header_regex = re.compile(r'^(#{1,6})\s+(.+)$')
        
        for line in lines:
            header_match = header_regex.match(line)
            if header_match:
                # Save the accumulated lines of the previous section before starting a new one
                if current_section_lines:
                    sections.append(self._create_section(current_headers, current_level, current_section_lines))
                    current_section_lines = []
                
                # Parse new heading attributes
                hashes, title = header_match.groups()
                level = len(hashes)
                title = title.strip()
                
                # Update the header path hierarchy
                current_headers[level] = title
                
                # Remove any existing subheadings at deeper levels (e.g. going from level 3 to 2 clears level 3)
                for l in list(current_headers.keys()):
                    if l > level:
                        del current_headers[l]
                
                current_level = level
            else:
                current_section_lines.append(line)
                
        # Save the final section
        if current_section_lines:
            sections.append(self._create_section(current_headers, current_level, current_section_lines))

        # Filter out empty or whitespace-only chunks
        valid_sections = []
        for sec in sections:
            sec["content"] = sec["content"].strip()
            if sec["content"]:
                valid_sections.append(sec)

        # Handle splitting of sections that exceed maximum character limits
        final_chunks = []
        for sec in valid_sections:
            if len(sec["content"]) <= self.max_chunk_chars:
                final_chunks.append(sec)
            else:
                # Split large sections semantically
                split_chunks = self._split_oversized_section(sec)
                final_chunks.extend(split_chunks)

        logger.info(f"Chunking finished. Generated {len(final_chunks)} chunks from document.")
        return final_chunks

    def _create_section(self, current_headers: Dict[int, str], level: int, lines: List[str]) -> Dict[str, Any]:
        """Constructs a basic section dictionary from hierarchy and content lines."""
        sorted_levels = sorted(current_headers.keys())
        header_path = [current_headers[l] for l in sorted_levels]
        section_heading = header_path[-1] if header_path else ""
        
        return {
            "header_path": header_path,
            "section_heading": section_heading,
            "content": "\n".join(lines)
        }

    def _split_oversized_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits content that is too large into smaller chunks by grouping paragraphs
        together, while avoiding splits in the middle of markdown tables.
        """
        content = section["content"]
        header_path = section["header_path"]
        section_heading = section["section_heading"]
        
        # Split section content into paragraphs, taking care to keep tables intact
        lines = content.split('\n')
        paragraphs = []
        current_paragraph = []
        in_table = False
        
        for line in lines:
            stripped = line.strip()
            # A table row starts with '|' or contains multiple '|' columns
            is_table_row = stripped.startswith('|') or (len(stripped) > 0 and stripped.count('|') >= 2)
            
            if is_table_row:
                in_table = True
            elif in_table and stripped == "":
                # Table ends when we encounter a blank line after starting one
                in_table = False
                
            if stripped == "" and not in_table:
                if current_paragraph:
                    paragraphs.append("\n".join(current_paragraph))
                    current_paragraph = []
            else:
                current_paragraph.append(line)
                
        if current_paragraph:
            paragraphs.append("\n".join(current_paragraph))

        # Group paragraphs to maximize chunk size without exceeding max_chunk_chars
        sub_chunks = []
        current_group = []
        current_len = 0
        
        for p in paragraphs:
            p_len = len(p)
            # If adding the paragraph exceeds the limit, save the current group
            if current_len + p_len + 2 > self.max_chunk_chars and current_group:
                sub_chunks.append("\n\n".join(current_group))
                current_group = [p]
                current_len = p_len
            else:
                current_group.append(p)
                current_len += p_len + 2
                
        if current_group:
            sub_chunks.append("\n\n".join(current_group))

        # Re-build section dicts with split indicators
        results = []
        for idx, sub_content in enumerate(sub_chunks):
            results.append({
                "header_path": header_path,
                "section_heading": section_heading,
                "content": sub_content,
                "split_index": idx
            })
            
        return results
