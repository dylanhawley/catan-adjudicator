"""Script to ingest existing PDFs from the data directory."""
import asyncio
import hashlib
import sys
from pathlib import Path
from app.services.pdf_parser import PDFParser
from app.services.chunking import ChunkingService
from app.services.vector_store import VectorStoreService
from app.services.pdf_registry import PDFRegistry


async def ingest_pdf_file(pdf_path: Path, pdf_id: str):
    """Ingest a single PDF file."""
    print(f"Ingesting {pdf_path.name}...")
    
    pdf_parser = PDFParser()
    chunking_service = ChunkingService()
    vector_store = VectorStoreService()
    registry = PDFRegistry()
    
    try:
        # Register PDF
        registry.register_pdf(pdf_id, str(pdf_path), pdf_path.name)
        
        # Parse PDF
        metadata, atoms = pdf_parser.parse_pdf(str(pdf_path), pdf_id=pdf_id)
        print(f"  Parsed {len(atoms)} atoms from {metadata.total_pages} pages")
        
        # Chunk atoms
        chunks = chunking_service.group_atoms_into_chunks(
            atoms=atoms,
            pdf_id=pdf_id
        )
        print(f"  Created {len(chunks)} chunks")
        
        # Add to vector store
        if chunks:
            vector_store.add_chunks(chunks)
            print(f"  ✓ Successfully ingested {pdf_path.name}")
        else:
            print(f"  ⚠ No chunks created for {pdf_path.name}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error ingesting {pdf_path.name}: {str(e)}")
        return False


def generate_pdf_id(file_path: Path) -> str:
    """
    Generate a deterministic PDF ID based on the file path.
    This ensures the same file always gets the same ID.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Deterministic PDF ID (hash-based)
    """
    # Use absolute path for consistency
    abs_path = str(file_path.resolve())
    # Generate SHA256 hash of the file path
    hash_obj = hashlib.sha256(abs_path.encode('utf-8'))
    # Use first 32 characters of hex digest as ID (similar to UUID format)
    return hash_obj.hexdigest()[:32]


async def main():
    """Main function to ingest all PDFs from data directory."""
    data_dir = Path(__file__).parent.parent / "data"
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s) to process\n")
    
    registry = PDFRegistry()
    results = []
    skipped = 0
    
    for pdf_file in pdf_files:
        # Check if PDF is already registered
        if registry.is_pdf_registered(str(pdf_file.resolve())):
            existing_pdf_id = registry.get_pdf_id_by_path(str(pdf_file.resolve()))
            print(f"⏭ Skipping {pdf_file.name} (already ingested with ID: {existing_pdf_id})")
            results.append((pdf_file.name, None))  # None indicates skipped
            skipped += 1
            print()
            continue
        
        # Generate deterministic ID based on file path
        pdf_id = generate_pdf_id(pdf_file)
        success = await ingest_pdf_file(pdf_file, pdf_id)
        results.append((pdf_file.name, success))
        print()
    
    # Summary
    print("=" * 50)
    print("Ingestion Summary:")
    successful = sum(1 for _, success in results if success is True)
    failed = sum(1 for _, success in results if success is False)
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Skipped (already ingested): {skipped}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    print()
    
    for filename, success in results:
        if success is None:
            status = "⏭"
            note = " (skipped)"
        elif success:
            status = "✓"
            note = ""
        else:
            status = "✗"
            note = ""
        print(f"  {status} {filename}{note}")


if __name__ == "__main__":
    asyncio.run(main())

