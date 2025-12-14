"""Vector store service using LangChain and Chroma."""
from typing import List, Optional
try:
    from langchain.docstore.document import Document
except ImportError:
    from langchain_core.documents import Document
try:
    from langchain.vectorstores import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
try:
    from langchain.retrievers import VectorStoreRetriever
except ImportError:
    from langchain_core.retrievers import BaseRetriever as VectorStoreRetriever
from app.config import settings
from app.models.chunk import Chunk
from app.services.embeddings import EmbeddingService
from app.services.chunk_storage import ChunkStorageService


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
        self.vector_store: Optional[Chroma] = None
        self.chunk_storage = ChunkStorageService()
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize or load the Chroma vector store."""
        try:
            # Try to load existing collection
            self.vector_store = Chroma(
                persist_directory=settings.chroma_persist_dir,
                collection_name=self.collection_name,
                embedding_function=self.embedding_service.embeddings
            )
        except Exception:
            # Create new collection if it doesn't exist
            self.vector_store = Chroma(
                persist_directory=settings.chroma_persist_dir,
                collection_name=self.collection_name,
                embedding_function=self.embedding_service.embeddings
            )

    def add_chunks(self, chunks: List[Chunk]):
        """
        Add chunks to the vector store.
        
        Args:
            chunks: List of Chunk objects to add
        """
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            # Create LangChain Document
            doc = Document(
                page_content=chunk.text,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "pdf_id": chunk.pdf_id,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "section_title": chunk.section_title or ""
                }
            )
            documents.append(doc)
            metadatas.append(doc.metadata)
            ids.append(chunk.chunk_id)
        
        # Store full chunks with atoms separately
        self.chunk_storage.save_chunks(chunks)
        
        # Add to vector store
        if self.vector_store is None:
            self._initialize_vector_store()
        
        self.vector_store.add_documents(
            documents=documents,
            ids=ids
        )
        
        # Persist to disk
        self.vector_store.persist()

    def get_retriever(self, k: int = 5) -> VectorStoreRetriever:
        """
        Get a retriever for searching the vector store.
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            VectorStoreRetriever instance
        """
        if self.vector_store is None:
            self._initialize_vector_store()
        
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search the vector store for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of Document objects
        """
        if self.vector_store is None:
            self._initialize_vector_store()
        
        return self.vector_store.similarity_search(query, k=k)

    def search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """
        Search the vector store with similarity scores.
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        if self.vector_store is None:
            self._initialize_vector_store()
        
        return self.vector_store.similarity_search_with_score(query, k=k)

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a specific chunk by ID with full details including atoms.
        
        Args:
            chunk_id: Chunk ID to retrieve
            
        Returns:
            Chunk if found, None otherwise
        """
        return self.chunk_storage.get_chunk(chunk_id)

