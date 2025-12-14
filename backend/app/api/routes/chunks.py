"""Chunk retrieval endpoint."""
from fastapi import APIRouter, HTTPException, Depends
from app.models.response import ChunkResponse
from app.api.dependencies import get_vector_store_service
from app.services.vector_store import VectorStoreService
from app.models.chunk import Atom


router = APIRouter(prefix="/api/chunks", tags=["chunks"])


@router.get("/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(
    chunk_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Retrieve a chunk by ID with full details including atoms.
    
    Args:
        chunk_id: Chunk ID to retrieve
        vector_store: Vector store service
        
    Returns:
        ChunkResponse with full chunk details
    """
    try:
        chunk = vector_store.get_chunk_by_id(chunk_id)
        
        if chunk is None:
            raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found")
        
        # Convert atoms to dict for JSON serialization
        atoms_dict = [atom.model_dump() for atom in chunk.atoms]
        
        return ChunkResponse(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            pdf_id=chunk.pdf_id,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            section_title=chunk.section_title,
            atoms=atoms_dict
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chunk: {str(e)}")

