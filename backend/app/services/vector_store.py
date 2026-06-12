"""Vector store service backed directly by Chroma."""
from dataclasses import dataclass, field
from typing import List, Optional

import chromadb

from app.config import settings
from app.models.chunk import Chunk
from app.services.embeddings import EmbeddingService
from app.services.chunk_storage import ChunkStorageService


@dataclass
class RetrievedChunk:
    """A chunk returned from a similarity search."""
    text: str
    metadata: dict = field(default_factory=dict)
    distance: Optional[float] = None


class VectorStoreService:
    """Service for managing vector store operations."""

    def __init__(self, collection_name: str = "catan_rules"):
        """
        Initialize the vector store service.

        Args:
            collection_name: Name of the Chroma collection
        """
        self.collection_name = collection_name
        self.embedding_service = EmbeddingService()
        self.chunk_storage = ChunkStorageService()
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[Chunk]):
        """
        Add chunks to the vector store.

        Args:
            chunks: List of Chunk objects to add
        """
        if not chunks:
            return

        # Store full chunks with atoms separately (used for PDF highlighting)
        self.chunk_storage.save_chunks(chunks)

        embeddings = self.embedding_service.embed_texts([chunk.text for chunk in chunks])

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "chunk_id": chunk.chunk_id,
                    "pdf_id": chunk.pdf_id,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "section_title": chunk.section_title or "",
                }
                for chunk in chunks
            ],
        )

    def search(self, query: str, k: int = 8) -> List[RetrievedChunk]:
        """
        Search the vector store for chunks similar to the query.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of RetrievedChunk objects, most similar first
        """
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedding_service.embed_text(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            RetrievedChunk(text=doc, metadata=meta or {}, distance=dist)
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a specific chunk by ID with full details including atoms.

        Args:
            chunk_id: Chunk ID to retrieve

        Returns:
            Chunk if found, None otherwise
        """
        return self.chunk_storage.get_chunk(chunk_id)
