"""PDF ingestion endpoint."""
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.response import IngestionResponse
from app.api.dependencies import get_pdf_parser, get_chunking_service, get_vector_store_service
from app.services.pdf_parser import PDFParser
from app.services.chunking import ChunkingService
from app.services.vector_store import VectorStoreService
from app.services.pdf_registry import PDFRegistry
import tempfile
import os
from pathlib import Path


router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("", response_model=IngestionResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    pdf_parser: PDFParser = Depends(get_pdf_parser),
    chunking_service: ChunkingService = Depends(get_chunking_service),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Ingest a PDF file into the vector store.
    
    Args:
        file: Uploaded PDF file
        pdf_parser: PDF parser service
        chunking_service: Chunking service
        vector_store: Vector store service
        
    Returns:
        IngestionResponse with status and chunk count
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Save uploaded file to persistent storage
    pdf_id = str(uuid.uuid4())
    storage_dir = Path("data/ingested")
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    saved_path = None
    
    try:
        # Save uploaded file
        saved_path = storage_dir / f"{pdf_id}.pdf"
        content = await file.read()
        with open(saved_path, 'wb') as f:
            f.write(content)
        
        # Register PDF
        registry = PDFRegistry()
        registry.register_pdf(pdf_id, saved_path, file.filename or "uploaded.pdf")
        
        # Parse PDF
        metadata, atoms = pdf_parser.parse_pdf(str(saved_path), pdf_id=pdf_id)
        
        # Chunk atoms
        chunks = chunking_service.group_atoms_into_chunks(
            atoms=atoms,
            pdf_id=pdf_id
        )
        
        # Add chunks to vector store (this also saves full chunks with atoms)
        if chunks:
            vector_store.add_chunks(chunks)
        
        return IngestionResponse(
            pdf_id=pdf_id,
            filename=metadata.filename,
            chunk_count=len(chunks),
            status="success"
        )
        
    except Exception as e:
        # Clean up on error
        if saved_path and saved_path.exists():
            os.unlink(saved_path)
        raise HTTPException(status_code=500, detail=f"Error ingesting PDF: {str(e)}")

