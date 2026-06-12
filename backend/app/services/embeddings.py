"""Embedding service using the OpenAI API directly."""
from typing import List

from openai import OpenAI

from app.config import settings


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single text."""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in one batched call."""
        response = self.client.embeddings.create(model=self.model, input=texts)
        # The API preserves input order; sort by index defensively
        return [item.embedding for item in sorted(response.data, key=lambda d: d.index)]
