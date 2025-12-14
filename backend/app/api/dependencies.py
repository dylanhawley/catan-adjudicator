"""Shared dependencies for API routes."""
from app.services.vector_store import VectorStoreService
from app.services.qa_service import QAService
from app.services.pdf_parser import PDFParser
from app.services.chunking import ChunkingService


# Global service instances (singletons)
_vector_store_service: VectorStoreService | None = None
_qa_service: QAService | None = None
_pdf_parser: PDFParser | None = None
_chunking_service: ChunkingService | None = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create vector store service instance."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service


def get_qa_service() -> QAService:
    """Get or create QA service instance."""
    global _qa_service
    if _qa_service is None:
        vector_store = get_vector_store_service()
        _qa_service = QAService(vector_store)
    return _qa_service


def get_pdf_parser() -> PDFParser:
    """Get or create PDF parser instance."""
    global _pdf_parser
    if _pdf_parser is None:
        _pdf_parser = PDFParser()
    return _pdf_parser


def get_chunking_service() -> ChunkingService:
    """Get or create chunking service instance."""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service

