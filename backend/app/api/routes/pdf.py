"""PDF serving endpoint."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.services.pdf_registry import PDFRegistry


router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.get("/{pdf_id}")
async def get_pdf(pdf_id: str):
    """
    Serve a PDF file by ID.
    
    Args:
        pdf_id: PDF ID to retrieve
        
    Returns:
        PDF file response
    """
    registry = PDFRegistry()
    pdf_path = registry.get_pdf_path(pdf_id)
    filename = registry.get_pdf_filename(pdf_id)
    
    if not pdf_path:
        raise HTTPException(status_code=404, detail=f"PDF {pdf_id} not found")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename or "document.pdf"
    )

