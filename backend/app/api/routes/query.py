"""Query endpoint for Q&A."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.models.response import QueryResponse
from app.api.dependencies import get_qa_service
from app.services.qa_service import QAService


router = APIRouter(prefix="/api/query", tags=["query"])


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str
    k: int = 5  # Number of chunks to retrieve


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    Answer a question about Catan rules.
    
    Args:
        request: Query request with question
        qa_service: QA service instance
        
    Returns:
        QueryResponse with answer and sources
    """
    try:
        response = qa_service.answer_question(
            question=request.question,
            k=request.k
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

