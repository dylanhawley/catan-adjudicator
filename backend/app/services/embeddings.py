"""Embedding service using LangChain."""
from typing import List
try:
    from langchain.embeddings.base import Embeddings
except ImportError:
    from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_google_vertexai import VertexAIEmbeddings
from app.config import settings


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        """Initialize the embedding service based on configuration."""
        self.embeddings: Embeddings = self._create_embeddings()

    def _create_embeddings(self) -> Embeddings:
        """Create the appropriate embedding model based on configuration."""
        if settings.llm_provider == "openai":
            return OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key
            )
        elif settings.llm_provider == "vertex":
            return VertexAIEmbeddings(
                model_name=settings.vertex_embedding_model,
                project=settings.vertex_project_id,
                location=settings.vertex_location
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        return self.embeddings.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)

