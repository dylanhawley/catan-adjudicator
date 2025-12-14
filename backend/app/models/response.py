"""Response models for API endpoints."""
from typing import List
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Reference to a source chunk with quote position."""
    chunk_id: str = Field(description="ID of the source chunk")
    quote_char_start: int = Field(description="Character start position of the quote")
    quote_char_end: int = Field(description="Character end position of the quote")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str = Field(description="Generated answer from LLM")
    sources: List[SourceReference] = Field(description="List of source references")


class IngestionResponse(BaseModel):
    """Response model for PDF ingestion endpoint."""
    pdf_id: str = Field(description="ID of the ingested PDF")
    filename: str = Field(description="Filename of the ingested PDF")
    chunk_count: int = Field(description="Number of chunks created")
    status: str = Field(description="Ingestion status")


class ChunkResponse(BaseModel):
    """Response model for chunk retrieval endpoint."""
    chunk_id: str = Field(description="Chunk ID")
    text: str = Field(description="Chunk text content")
    pdf_id: str = Field(description="PDF ID")
    page_start: int = Field(description="Starting page number")
    page_end: int = Field(description="Ending page number")
    section_title: str | None = Field(default=None, description="Section title")
    atoms: List[dict] = Field(description="List of atoms with coordinates")

