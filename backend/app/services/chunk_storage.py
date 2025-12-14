"""Service for storing and retrieving full chunks with atoms."""
import json
import os
from pathlib import Path
from typing import Optional, Dict
from app.models.chunk import Chunk
from app.config import settings


class ChunkStorageService:
    """Service for storing full chunks with atoms (separate from vector store)."""

    def __init__(self, storage_dir: str = None):
        """
        Initialize chunk storage service.
        
        Args:
            storage_dir: Directory to store chunks (defaults to chroma_persist_dir/chunks)
        """
        if storage_dir is None:
            storage_dir = os.path.join(settings.chroma_persist_dir, "chunks")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for quick access
        self._cache: Dict[str, Chunk] = {}

    def _get_chunk_path(self, chunk_id: str) -> Path:
        """Get file path for a chunk."""
        return self.storage_dir / f"{chunk_id}.json"

    def save_chunk(self, chunk: Chunk):
        """
        Save a chunk to disk.
        
        Args:
            chunk: Chunk to save
        """
        chunk_path = self._get_chunk_path(chunk.chunk_id)
        
        # Convert to dict for JSON serialization
        chunk_dict = chunk.model_dump()
        
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_dict, f, indent=2, ensure_ascii=False)
        
        # Update cache
        self._cache[chunk.chunk_id] = chunk

    def save_chunks(self, chunks: list[Chunk]):
        """
        Save multiple chunks to disk.
        
        Args:
            chunks: List of chunks to save
        """
        for chunk in chunks:
            self.save_chunk(chunk)

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a chunk by ID.
        
        Args:
            chunk_id: Chunk ID to retrieve
            
        Returns:
            Chunk if found, None otherwise
        """
        # Check cache first
        if chunk_id in self._cache:
            return self._cache[chunk_id]
        
        # Load from disk
        chunk_path = self._get_chunk_path(chunk_id)
        if not chunk_path.exists():
            return None
        
        try:
            with open(chunk_path, 'r', encoding='utf-8') as f:
                chunk_dict = json.load(f)
            
            chunk = Chunk(**chunk_dict)
            self._cache[chunk_id] = chunk
            return chunk
        except Exception:
            return None

    def get_chunks_by_pdf(self, pdf_id: str) -> list[Chunk]:
        """
        Get all chunks for a specific PDF.
        
        Args:
            pdf_id: PDF ID
            
        Returns:
            List of chunks
        """
        chunks = []
        for chunk_file in self.storage_dir.glob("*.json"):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk_dict = json.load(f)
                    if chunk_dict.get("pdf_id") == pdf_id:
                        chunk = Chunk(**chunk_dict)
                        chunks.append(chunk)
                        self._cache[chunk.chunk_id] = chunk
            except Exception:
                continue
        
        return chunks

