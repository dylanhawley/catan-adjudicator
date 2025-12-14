"""Registry for tracking PDF files and their metadata."""
import json
import os
from pathlib import Path
from typing import Optional, Dict
from app.config import settings


class PDFRegistry:
    """Registry for mapping PDF IDs to file paths and metadata."""

    def __init__(self, registry_file: str = None):
        """
        Initialize PDF registry.
        
        Args:
            registry_file: Path to registry JSON file
        """
        if registry_file is None:
            registry_file = os.path.join(settings.chroma_persist_dir, "pdf_registry.json")
        self.registry_file = Path(registry_file)
        self._registry: Dict[str, Dict] = {}
        self._load_registry()

    def _load_registry(self):
        """Load registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self._registry = json.load(f)
            except Exception:
                self._registry = {}

    def _save_registry(self):
        """Save registry to disk."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self._registry, f, indent=2, ensure_ascii=False)

    def register_pdf(self, pdf_id: str, file_path: str, filename: str):
        """
        Register a PDF in the registry.
        
        Args:
            pdf_id: Unique PDF ID
            file_path: Path to the PDF file
            filename: Original filename
        """
        self._registry[pdf_id] = {
            "pdf_id": pdf_id,
            "file_path": str(file_path),
            "filename": filename
        }
        self._save_registry()

    def get_pdf_path(self, pdf_id: str) -> Optional[str]:
        """
        Get file path for a PDF ID.
        
        Args:
            pdf_id: PDF ID to look up
            
        Returns:
            File path if found, None otherwise
        """
        if pdf_id in self._registry:
            path = Path(self._registry[pdf_id]["file_path"])
            if path.exists():
                return str(path)
        return None

    def get_pdf_filename(self, pdf_id: str) -> Optional[str]:
        """
        Get filename for a PDF ID.
        
        Args:
            pdf_id: PDF ID to look up
            
        Returns:
            Filename if found, None otherwise
        """
        if pdf_id in self._registry:
            return self._registry[pdf_id].get("filename")
        return None

    def get_pdf_id_by_path(self, file_path: str) -> Optional[str]:
        """
        Get PDF ID for a file path if it already exists in the registry.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            PDF ID if found, None otherwise
        """
        file_path_str = str(file_path)
        for pdf_id, pdf_data in self._registry.items():
            if pdf_data.get("file_path") == file_path_str:
                return pdf_id
        return None

    def is_pdf_registered(self, file_path: str) -> bool:
        """
        Check if a PDF file path is already registered.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            True if the file is already registered, False otherwise
        """
        return self.get_pdf_id_by_path(file_path) is not None

