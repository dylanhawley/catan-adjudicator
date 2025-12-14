"""Text chunking service to group atoms into semantic chunks."""
import uuid
from typing import List, Optional
from app.models.chunk import Atom, Chunk
from app.utils.text_utils import normalize_whitespace


class ChunkingService:
    """Service for grouping atoms into semantic chunks."""

    def __init__(self, max_chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize the chunking service.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def detect_section_header(self, atom: Atom, previous_atom: Optional[Atom] = None) -> bool:
        """
        Detect if an atom is likely a section header.
        
        Args:
            atom: The atom to check
            previous_atom: Previous atom for context
            
        Returns:
            True if likely a section header
        """
        if not atom.text:
            return False
        
        text = atom.text.strip()
        
        # Check for common header patterns
        # Headers are often short, all caps, or end with colon
        is_short = len(text) < 50
        is_all_caps = text.isupper() and len(text) > 3
        ends_with_colon = text.endswith(':')
        
        # Check if there's significant vertical spacing (likely header)
        has_spacing = False
        if previous_atom and previous_atom.page_num == atom.page_num:
            vertical_gap = atom.bbox.y0 - previous_atom.bbox.y1
            has_spacing = vertical_gap > 20  # Significant gap suggests header
        
        return (is_short and (is_all_caps or ends_with_colon)) or has_spacing

    def group_atoms_into_chunks(
        self,
        atoms: List[Atom],
        pdf_id: str,
        section_title: Optional[str] = None
    ) -> List[Chunk]:
        """
        Group atoms into semantic chunks (paragraphs/sections).
        
        Args:
            atoms: List of atoms to chunk
            pdf_id: ID of the source PDF
            section_title: Optional section title for the first chunk
            
        Returns:
            List of Chunk objects
        """
        if not atoms:
            return []
        
        chunks: List[Chunk] = []
        current_chunk_atoms: List[Atom] = []
        current_section_title: Optional[str] = section_title
        current_char_pos = 0
        
        for i, atom in enumerate(atoms):
            # Check if this atom is a section header
            previous_atom = atoms[i - 1] if i > 0 else None
            is_header = self.detect_section_header(atom, previous_atom)
            
            if is_header and current_chunk_atoms:
                # Finalize current chunk before starting new section
                chunk = self._create_chunk_from_atoms(
                    current_chunk_atoms,
                    pdf_id,
                    current_section_title,
                    current_char_pos
                )
                if chunk:
                    chunks.append(chunk)
                    current_char_pos = chunk.atoms[-1].char_end + 1
                
                current_chunk_atoms = []
                current_section_title = atom.text.strip()
            
            # Add atom to current chunk
            current_chunk_atoms.append(atom)
            
            # Check if we've exceeded max chunk size
            if current_chunk_atoms:
                chunk_text = self._atoms_to_text(current_chunk_atoms)
                if len(chunk_text) > self.max_chunk_size:
                    # Split chunk at paragraph boundary if possible
                    split_point = self._find_split_point(current_chunk_atoms)
                    
                    if split_point > 0:
                        # Create chunk up to split point
                        chunk_atoms = current_chunk_atoms[:split_point]
                        chunk = self._create_chunk_from_atoms(
                            chunk_atoms,
                            pdf_id,
                            current_section_title,
                            current_char_pos
                        )
                        if chunk:
                            chunks.append(chunk)
                            current_char_pos = chunk.atoms[-1].char_end + 1
                        
                        # Keep overlap atoms for next chunk
                        overlap_start = max(0, split_point - self.overlap // 50)  # Approximate
                        current_chunk_atoms = current_chunk_atoms[overlap_start:]
                    else:
                        # Force split at current position
                        chunk = self._create_chunk_from_atoms(
                            current_chunk_atoms,
                            pdf_id,
                            current_section_title,
                            current_char_pos
                        )
                        if chunk:
                            chunks.append(chunk)
                            current_char_pos = chunk.atoms[-1].char_end + 1
                        current_chunk_atoms = []
        
        # Create final chunk
        if current_chunk_atoms:
            chunk = self._create_chunk_from_atoms(
                current_chunk_atoms,
                pdf_id,
                current_section_title,
                current_char_pos
            )
            if chunk:
                chunks.append(chunk)
        
        return chunks

    def _atoms_to_text(self, atoms: List[Atom]) -> str:
        """Convert list of atoms to text string."""
        texts = [atom.text for atom in atoms]
        return " ".join(texts)

    def _find_split_point(self, atoms: List[Atom]) -> int:
        """
        Find a good split point in atoms (prefer paragraph boundaries).
        
        Args:
            atoms: List of atoms to find split point in
            
        Returns:
            Index to split at, or 0 if no good split point
        """
        # Look for paragraph breaks (significant vertical gaps)
        for i in range(len(atoms) - 1, max(0, len(atoms) // 2), -1):
            if i == 0:
                continue
            
            current_atom = atoms[i]
            previous_atom = atoms[i - 1]
            
            # Check for paragraph break (same page, significant vertical gap)
            if (current_atom.page_num == previous_atom.page_num and
                current_atom.bbox.y0 - previous_atom.bbox.y1 > 15):
                return i
        
        # Look for sentence endings near the middle
        mid_point = len(atoms) // 2
        for i in range(mid_point, max(0, mid_point - 10), -1):
            if i < len(atoms) and atoms[i].text.strip().endswith(('.', '!', '?')):
                return i + 1
        
        return 0

    def _create_chunk_from_atoms(
        self,
        atoms: List[Atom],
        pdf_id: str,
        section_title: Optional[str],
        char_start_offset: int
    ) -> Optional[Chunk]:
        """
        Create a Chunk from a list of atoms.
        
        Args:
            atoms: List of atoms to include in chunk
            pdf_id: ID of the source PDF
            section_title: Optional section title
            char_start_offset: Character position offset for recalculation
            
        Returns:
            Chunk object or None if atoms list is empty
        """
        if not atoms:
            return None
        
        # Recalculate character positions relative to chunk start
        chunk_text_parts = []
        current_pos = 0
        
        for atom in atoms:
            atom_text = atom.text
            chunk_text_parts.append(atom_text)
            
            # Update atom character positions relative to chunk
            atom.char_start = current_pos
            atom.char_end = current_pos + len(atom_text)
            current_pos = atom.char_end + 1  # Add space between atoms
        
        chunk_text = " ".join(chunk_text_parts)
        chunk_text = normalize_whitespace(chunk_text)
        
        # Recalculate positions after normalization
        # This is simplified - in production, you'd need more sophisticated mapping
        normalized_parts = chunk_text.split()
        pos = 0
        atom_idx = 0
        
        for part in normalized_parts:
            if atom_idx < len(atoms):
                # Find matching atom
                while atom_idx < len(atoms) and atoms[atom_idx].text.strip() not in part:
                    atom_idx += 1
                
                if atom_idx < len(atoms):
                    atoms[atom_idx].char_start = pos
                    atoms[atom_idx].char_end = pos + len(part)
                    pos = atoms[atom_idx].char_end + 1
                    atom_idx += 1
        
        chunk_id = str(uuid.uuid4())
        page_start = min(atom.page_num for atom in atoms)
        page_end = max(atom.page_num for atom in atoms)
        
        return Chunk(
            chunk_id=chunk_id,
            text=chunk_text,
            atoms=atoms,
            pdf_id=pdf_id,
            page_start=page_start,
            page_end=page_end,
            section_title=section_title
        )

