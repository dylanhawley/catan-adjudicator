"""Custom PDF parser using PyMuPDF for coordinate tracking."""
import fitz  # PyMuPDF
import uuid
from pathlib import Path
from typing import List, Tuple, Optional
from app.models.chunk import Atom, BBox, PDFMetadata
from app.utils.text_utils import normalize_whitespace


class PDFParser:
    """Parser for extracting text with coordinates from PDF files."""

    def __init__(self):
        """Initialize the PDF parser."""
        pass

    def parse_pdf(self, pdf_path: str, pdf_id: Optional[str] = None) -> Tuple[PDFMetadata, List[Atom]]:
        """
        Parse a PDF file and extract text atoms with coordinates.
        
        Args:
            pdf_path: Path to the PDF file
            pdf_id: Optional unique identifier for the PDF
            
        Returns:
            Tuple of (PDFMetadata, List[Atom])
        """
        if pdf_id is None:
            pdf_id = str(uuid.uuid4())
        
        doc = fitz.open(pdf_path)
        atoms: List[Atom] = []
        filename = Path(pdf_path).name
        
        # Extract title if available
        title = doc.metadata.get('title', None) if doc.metadata else None
        
        total_pages = len(doc)
        current_char_pos = 0
        
        for page_num in range(total_pages):
            page = doc[page_num]
            
            # Get text blocks with coordinates
            blocks = page.get_text("dict")
            
            for block in blocks.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        
                        # Get bounding box
                        bbox = span.get("bbox", [0, 0, 0, 0])
                        if len(bbox) == 4:
                            atom_bbox = BBox(
                                x0=bbox[0],
                                y0=bbox[1],
                                x1=bbox[2],
                                y1=bbox[3]
                            )
                            
                            # Calculate character positions
                            char_start = current_char_pos
                            char_end = current_char_pos + len(text)
                            
                            atom = Atom(
                                text=text,
                                page_num=page_num,
                                bbox=atom_bbox,
                                char_start=char_start,
                                char_end=char_end
                            )
                            atoms.append(atom)
                            
                            # Update character position (add space after each atom for separation)
                            current_char_pos = char_end + 1
        
        doc.close()
        
        metadata = PDFMetadata(
            pdf_id=pdf_id,
            filename=filename,
            total_pages=total_pages,
            title=title
        )
        
        return metadata, atoms

