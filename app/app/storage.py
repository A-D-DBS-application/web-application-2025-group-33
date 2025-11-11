"""
Simple file storage module using Supabase Storage.
This provides a straightforward interface for uploading and downloading PDFs.
"""

from supabase import create_client, Client
from config import Config
from typing import Optional

# Initialize Supabase client (for storage only)
_supabase_client: Optional[Client] = None


def get_storage_client() -> Client:
    """
    Get the Supabase client for file storage operations.
    Uses service_role key to bypass RLS on storage.
    """
    global _supabase_client
    if _supabase_client is None:
        if not Config.SUPABASE_URL or not Config.SUPABASE_SERVICE_KEY:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in config.")
        # Use service_role key for storage (bypasses RLS)
        _supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    return _supabase_client


def upload_paper_pdf(paper_id: str, pdf_file) -> str:
    """
    Upload a PDF file to Supabase Storage.

    Args:
        paper_id: UUID of the paper
        pdf_file: File object from request.files

    Returns:
        str: File path in storage (e.g., "papers/uuid.pdf")
    """
    client = get_storage_client()

    # Simple path: just paper_id.pdf in the papers bucket
    file_path = f"{paper_id}.pdf"

    # Read file content
    pdf_content = pdf_file.read()

    # Upload to Supabase Storage
    client.storage.from_('papers').upload(
        file_path,
        pdf_content,
        file_options={"content-type": "application/pdf", "upsert": "true"}
    )

    return file_path


def download_paper_pdf(file_path: str) -> bytes:
    """
    Download a PDF file from Supabase Storage.

    Args:
        file_path: Path in storage (e.g., "papers/uuid.pdf" or "uuid.pdf")

    Returns:
        bytes: PDF file content
    """
    client = get_storage_client()

    # Download from Supabase Storage
    response = client.storage.from_('papers').download(file_path)

    return response


def delete_paper_pdf(file_path: str) -> None:
    """
    Delete a PDF file from Supabase Storage.

    Args:
        file_path: Path in storage
    """
    client = get_storage_client()

    # Delete from Supabase Storage
    client.storage.from_('papers').remove([file_path])

