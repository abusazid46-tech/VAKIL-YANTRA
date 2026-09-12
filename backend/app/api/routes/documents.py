from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db, require_roles
from app.domain.auth.schemas import CurrentUser, ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE, ROLE_CLERK
from app.domain.documents.schemas import DocumentDownloadUrl, DocumentRecord, UploadIntent, UploadIntentRequest
from app.domain.documents.service import create_download_url, create_upload_intent, list_documents, upload_document_bytes

router = APIRouter()


@router.post("/upload-intent", response_model=UploadIntent, status_code=201)
def upload_intent(
    payload: UploadIntentRequest,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE, ROLE_CLERK)),
    db: Session = Depends(get_tenant_db),
) -> UploadIntent:
    return create_upload_intent(db, current_user, payload)


@router.post("/upload", response_model=DocumentRecord, status_code=201)
async def upload(
    file: UploadFile = File(...),
    matter_id: str | None = Form(default=None),
    folder_id: str | None = Form(default=None),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE, ROLE_CLERK)),
    db: Session = Depends(get_tenant_db),
) -> DocumentRecord:
    content = await file.read()
    return upload_document_bytes(
        db,
        current_user,
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        content=content,
        matter_id=matter_id or None,
        folder_id=folder_id or None,
    )


@router.get("", response_model=list[DocumentRecord])
def index(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[DocumentRecord]:
    return list_documents(db, current_user)


@router.get("/{document_id}/download-url", response_model=DocumentDownloadUrl)
def download_url(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> DocumentDownloadUrl:
    return create_download_url(db, current_user, document_id)
