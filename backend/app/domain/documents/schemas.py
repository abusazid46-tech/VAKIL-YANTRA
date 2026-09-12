from pydantic import BaseModel, Field


class UploadIntentRequest(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = Field(gt=0, le=50_000_000)
    matter_id: str | None = None
    folder_id: str | None = None


class UploadIntent(BaseModel):
    document_id: str
    upload_url: str
    fields: dict[str, str]
    expires_in_seconds: int = 600


class DocumentDownloadUrl(BaseModel):
    document_id: str
    download_url: str
    expires_in_seconds: int = 600


class DocumentRecord(BaseModel):
    id: str
    firm_id: str
    filename: str
    content_type: str
    matter_id: str | None
    folder_id: str | None = None
    status: str
    storage_key: str | None = None
    checksum: str | None = None
    created_at: str | None = None
