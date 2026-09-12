import hashlib
import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document as DocumentModel
from app.db.models import Matter, WorkspaceFolder, WorkspaceShare
from app.domain.auth.schemas import CurrentUser, ROLE_ADMIN_ADVOCATE
from app.domain.documents.schemas import DocumentDownloadUrl, DocumentRecord, UploadIntent, UploadIntentRequest
from app.integrations.storage import StorageError, get_storage_gateway


def create_upload_intent(db: Session, user: CurrentUser, payload: UploadIntentRequest) -> UploadIntent:
    validate_parent_access(db, user, payload.matter_id, payload.folder_id, minimum="edit")
    document = DocumentModel(
        firm_id=user.firm_id,
        filename=payload.filename,
        content_type=payload.content_type,
        matter_id=payload.matter_id,
        folder_id=payload.folder_id,
        created_by=user.user_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return UploadIntent(
        document_id=document.id,
        upload_url=f"/api/v1/documents/{document.id}/upload",
        fields={"x-document-id": document.id, "x-firm-id": user.firm_id},
    )


def upload_document_bytes(
    db: Session,
    user: CurrentUser,
    filename: str,
    content_type: str,
    content: bytes,
    matter_id: str | None = None,
    folder_id: str | None = None,
) -> DocumentRecord:
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")
    validate_parent_access(db, user, matter_id, folder_id, minimum="edit")
    document = DocumentModel(
        firm_id=user.firm_id,
        filename=filename,
        content_type=content_type,
        matter_id=matter_id,
        folder_id=folder_id,
        status="uploading",
        created_by=user.user_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    storage_key = f"{user.firm_id}/{document.id}/{safe_filename(filename)}"
    checksum = hashlib.sha256(content).hexdigest()
    try:
        get_storage_gateway().upload_bytes(storage_key, content, content_type)
    except StorageError as exc:
        document.status = "upload_failed"
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    document.storage_key = storage_key
    document.checksum = checksum
    document.status = "ready"
    db.commit()
    db.refresh(document)
    return to_record(document)


def create_download_url(db: Session, user: CurrentUser, document_id: str, expires_in_seconds: int = 600) -> DocumentDownloadUrl:
    document = get_document_for_user(db, user, document_id, minimum="view")
    if not document.storage_key or document.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document file is not ready")
    try:
        signed_url = get_storage_gateway().create_signed_download_url(document.storage_key, expires_in_seconds)
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return DocumentDownloadUrl(document_id=document.id, download_url=signed_url, expires_in_seconds=expires_in_seconds)


def list_documents(db: Session, user: CurrentUser) -> list[DocumentRecord]:
    records = db.scalars(select(DocumentModel).where(DocumentModel.firm_id == user.firm_id).order_by(DocumentModel.created_at.desc()))
    return [to_record(doc) for doc in records if can_access_document(db, user, doc, minimum="view")]


def get_document_for_user(db: Session, user: CurrentUser, document_id: str, minimum: str) -> DocumentModel:
    document = db.scalar(select(DocumentModel).where(DocumentModel.id == document_id, DocumentModel.firm_id == user.firm_id))
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not can_access_document(db, user, document, minimum):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document permission denied")
    return document


def can_access_document(db: Session, user: CurrentUser, document: DocumentModel, minimum: str) -> bool:
    if user.role == ROLE_ADMIN_ADVOCATE or document.created_by == user.user_id:
        return True
    if document.matter_id:
        return minimum == "view"
    if document.folder_id:
        folder = db.scalar(select(WorkspaceFolder).where(WorkspaceFolder.id == document.folder_id, WorkspaceFolder.firm_id == user.firm_id))
        if folder and folder.owner_user_id == user.user_id:
            return True
        share = db.scalar(
            select(WorkspaceShare).where(
                WorkspaceShare.firm_id == user.firm_id,
                WorkspaceShare.resource_type == "folder",
                WorkspaceShare.resource_id == document.folder_id,
                WorkspaceShare.grantee_user_id == user.user_id,
            )
        )
        if share and (minimum == "view" or share.permission == "edit"):
            return True
    share = db.scalar(
        select(WorkspaceShare).where(
            WorkspaceShare.firm_id == user.firm_id,
            WorkspaceShare.resource_type == "document",
            WorkspaceShare.resource_id == document.id,
            WorkspaceShare.grantee_user_id == user.user_id,
        )
    )
    return bool(share and (minimum == "view" or share.permission == "edit"))


def validate_parent_access(db: Session, user: CurrentUser, matter_id: str | None, folder_id: str | None, minimum: str) -> None:
    if matter_id:
        matter = db.scalar(select(Matter).where(Matter.id == matter_id, Matter.firm_id == user.firm_id))
        if not matter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")
    if folder_id:
        folder = db.scalar(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.firm_id == user.firm_id))
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
        if user.role == ROLE_ADMIN_ADVOCATE or folder.owner_user_id == user.user_id:
            return
        share = db.scalar(
            select(WorkspaceShare).where(
                WorkspaceShare.firm_id == user.firm_id,
                WorkspaceShare.resource_type == "folder",
                WorkspaceShare.resource_id == folder_id,
                WorkspaceShare.grantee_user_id == user.user_id,
            )
        )
        if not share or (minimum == "edit" and share.permission != "edit"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Folder permission denied")


def to_record(doc: DocumentModel) -> DocumentRecord:
    return DocumentRecord(
        id=doc.id,
        firm_id=doc.firm_id,
        filename=doc.filename,
        content_type=doc.content_type,
        matter_id=doc.matter_id,
        folder_id=doc.folder_id,
        status=doc.status,
        storage_key=doc.storage_key,
        checksum=doc.checksum,
        created_at=doc.created_at.isoformat(),
    )


def safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip(".-")
    return cleaned or "document"
