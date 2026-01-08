"""Query endpoint for Q&A."""
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.models.response import QueryResponse, SourceReference
from app.api.dependencies import get_qa_service
from app.services.qa_service import QAService


router = APIRouter(prefix="/api/query", tags=["query"])


class ConversationMessage(BaseModel):
    """A message in the conversation history."""
    role: str  # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str
    k: int = 5  # Number of chunks to retrieve
    conversation_history: list[ConversationMessage] = []  # Previous messages for context


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


def generate_sse_events(qa_service: QAService, question: str, k: int, conversation_history: list = None):
    """
    Generator function for SSE events.

    Args:
        qa_service: QA service instance
        question: User's question
        k: Number of chunks to retrieve
        conversation_history: Previous conversation messages

    Yields:
        SSE formatted event strings
    """
    try:
        for event_type, data in qa_service.stream_answer_question(question, k, conversation_history or []):
            if event_type == "sources":
                # Convert SourceReference objects to dicts for JSON serialization
                sources_data = [
                    {
                        "chunk_id": src.chunk_id,
                        "quote_char_start": src.quote_char_start,
                        "quote_char_end": src.quote_char_end
                    }
                    for src in data
                ]
                yield f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
            elif event_type == "token":
                # Escape newlines in token data for SSE format
                escaped_data = data.replace("\n", "\\n")
                yield f"event: token\ndata: {escaped_data}\n\n"
            elif event_type == "done":
                yield f"event: done\ndata: {{}}\n\n"
            elif event_type == "error":
                yield f"event: error\ndata: {json.dumps({'error': data})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    qa_service: QAService = Depends(get_qa_service)
):
    """
    Stream an answer to a question about Catan rules using Server-Sent Events.
    
    Args:
        request: Query request with question
        qa_service: QA service instance
        
    Returns:
        StreamingResponse with SSE events
    """
    # Convert conversation history to list of dicts
    history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]

    return StreamingResponse(
        generate_sse_events(qa_service, request.question, request.k, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

