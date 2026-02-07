"""Document upload request/response."""
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    upload_id: str
    namespace: str
    filename: str
    chunk_count: int
    message: str = "Document chunked and embeddings stored on Pinecone only. You can now query using this document."
