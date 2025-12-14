"""Question-answering service using LangChain RAG."""
import json
from typing import List, Optional
try:
    from langchain.prompts import PromptTemplate
except ImportError:
    from langchain_core.prompts import PromptTemplate
try:
    from langchain.schema import BaseOutputParser
except ImportError:
    from langchain_core.output_parsers import BaseOutputParser
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from app.config import settings
from app.models.response import QueryResponse, SourceReference
from app.services.vector_store import VectorStoreService


class JSONOutputParser(BaseOutputParser):
    """Parser for JSON output from LLM."""
    
    def parse(self, text: str) -> dict:
        """Parse JSON from LLM output."""
        # Try to extract JSON from markdown code blocks
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            raise ValueError(f"Could not parse JSON from: {text}")


class QAService:
    """Service for question-answering using RAG."""

    def __init__(self, vector_store_service: VectorStoreService):
        """
        Initialize the QA service.
        
        Args:
            vector_store_service: Vector store service instance
        """
        self.vector_store_service = vector_store_service
        self.llm = self._create_llm()
        self.output_parser = JSONOutputParser()

    def _create_llm(self):
        """Create the appropriate LLM based on configuration."""
        if settings.llm_provider == "openai":
            return ChatOpenAI(
                model_name=settings.openai_model,
                openai_api_key=settings.openai_api_key,
                temperature=0
            )
        elif settings.llm_provider == "vertex":
            return ChatVertexAI(
                model_name=settings.vertex_model,
                project=settings.vertex_project_id,
                location=settings.vertex_location,
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for RAG."""
        template = """You are a helpful assistant that answers questions about Catan board game rules based ONLY on the provided context from official rulebooks.

Context from rulebooks:
{context}

Question: {question}

Instructions:
1. Answer the question using ONLY the information provided in the context above.
2. If the answer is not in the provided context, say "I cannot answer this question based on the available rulebook content."
3. Cite specific sources by referencing the chunk IDs where you found the information.
4. Provide exact quotes from the rulebooks when possible.

Respond in the following JSON format:
{{
  "answer": "Your answer here",
  "sources": [
    {{
      "chunk_id": "chunk_id_here",
      "quote_char_start": 0,
      "quote_char_end": 50
    }}
  ]
}}

JSON Response:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

    def answer_question(self, question: str, k: int = 5) -> QueryResponse:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            k: Number of chunks to retrieve
            
        Returns:
            QueryResponse with answer and sources
        """
        # Retrieve relevant chunks
        retriever = self.vector_store_service.get_retriever(k=k)
        # Support both old and new LangChain API
        if hasattr(retriever, 'invoke'):
            relevant_docs = retriever.invoke(question)
        elif hasattr(retriever, 'get_relevant_documents'):
            relevant_docs = retriever.get_relevant_documents(question)
        else:
            # Fallback to direct vector store search
            relevant_docs = self.vector_store_service.search(question, k=k)
        
        if not relevant_docs:
            return QueryResponse(
                answer="I cannot answer this question as no relevant information was found in the rulebooks.",
                sources=[]
            )
        
        # Format context
        context_parts = []
        for doc in relevant_docs:
            chunk_id = doc.metadata.get("chunk_id", "")
            page_info = f"Page {doc.metadata.get('page_start', '?')}"
            section = doc.metadata.get("section_title", "")
            if section:
                context_parts.append(f"[Chunk {chunk_id}, {page_info}, Section: {section}]\n{doc.page_content}")
            else:
                context_parts.append(f"[Chunk {chunk_id}, {page_info}]\n{doc.page_content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Create prompt
        prompt_template = self._create_prompt_template()
        prompt = prompt_template.format(context=context, question=question)
        
        # Call LLM
        try:
            # Use invoke for newer LangChain versions, fallback to predict
            if hasattr(self.llm, 'invoke'):
                response = self.llm.invoke(prompt).content
            else:
                response = self.llm.predict(prompt)
            
            # Parse JSON response
            parsed = self.output_parser.parse(response)
            
            # Extract answer and sources
            answer = parsed.get("answer", "I cannot answer this question.")
            sources_data = parsed.get("sources", [])
            
            sources = [
                SourceReference(
                    chunk_id=src.get("chunk_id", ""),
                    quote_char_start=src.get("quote_char_start", 0),
                    quote_char_end=src.get("quote_char_end", 0)
                )
                for src in sources_data
            ]
            
            return QueryResponse(answer=answer, sources=sources)
            
        except Exception as e:
            # Fallback response on error
            return QueryResponse(
                answer=f"I encountered an error while processing your question: {str(e)}. Please try again.",
                sources=[]
            )

