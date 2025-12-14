"""Data models for PDF chunks and atoms."""
from typing import List, Optional
from pydantic import BaseModel, Field


class BBox(BaseModel):
    """Bounding box coordinates."""
    x0: float = Field(description="Left coordinate")
    y0: float = Field(description="Top coordinate")
    x1: float = Field(description="Right coordinate")
    y1: float = Field(description="Bottom coordinate")


class Atom(BaseModel):
    """Represents a single text atom with position information."""
    text: str = Field(description="Text content of the atom")
    page_num: int = Field(description="Page number (0-indexed)")
    bbox: BBox = Field(description="Bounding box coordinates")
    char_start: int = Field(description="Character start position in chunk text")
    char_end: int = Field(description="Character end position in chunk text")


class PDFMetadata(BaseModel):
    """Metadata about a PDF document."""
    pdf_id: str = Field(description="Unique identifier for the PDF")
    filename: str = Field(description="Original filename")
    total_pages: int = Field(description="Total number of pages")
    title: Optional[str] = Field(default=None, description="PDF title if available")


class Chunk(BaseModel):
    """Represents a chunk of text with associated atoms."""
    chunk_id: str = Field(description="Unique identifier for the chunk")
    text: str = Field(description="Full text content of the chunk")
    atoms: List[Atom] = Field(description="List of atoms that make up this chunk")
    pdf_id: str = Field(description="ID of the source PDF")
    page_start: int = Field(description="Starting page number (0-indexed)")
    page_end: int = Field(description="Ending page number (0-indexed)")
    section_title: Optional[str] = Field(default=None, description="Section title if available")

