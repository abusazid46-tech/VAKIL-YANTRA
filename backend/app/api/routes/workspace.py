from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db
from app.db.models import Document, Firm, Matter, MatterTask, Membership, User, WorkspaceFolder, WorkspaceNote, WorkspaceShare
from app.domain.auth.schemas import CurrentUser, ROLE_ADMIN_ADVOCATE

router = APIRouter()


class WorkspaceItem(BaseModel):
    id: str
    item_type: str
    name: str
    permission: str


class WorkspaceFolderCreate(BaseModel):
    name: str = Field(min_length=2)
    parent_folder_id: str | None = None


class WorkspaceFolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    parent_folder_id: str | None = None


class WorkspaceNoteCreate(BaseModel):
    title: str = Field(min_length=2)
    body: str = ""
    folder_id: str | None = None


class WorkspaceNoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2)
    body: str | None = None
    folder_id: str | None = None


class WorkspaceShareCreate(BaseModel):
    resource_type: str
    resource_id: str
    grantee_user_id: str
    permission: str


class WorkspaceUserOption(BaseModel):
    user_id: str
    name: str
    email: str
    role: str


class WorkspaceFolderRecord(BaseModel):
    id: str
    name: str
    parent_folder_id: str | None
    owner_user_id: str
    permission: str
    notes_count: int
    documents_count: int
    created_at: str


class WorkspaceNoteRecord(BaseModel):
    id: str
    folder_id: str | None
    title: str
    body: str
    owner_user_id: str
    permission: str
    updated_at: str
    created_at: str


class WorkspaceDocumentRecord(BaseModel):
    id: str
    folder_id: str | None
    matter_id: str | None
    filename: str
    content_type: str
    status: str
    owner_user_id: str | None
    permission: str
    created_at: str


class WorkspaceShareRecord(BaseModel):
    id: str
    resource_type: str
    resource_id: str
    resource_name: str
    grantee_user_id: str
    grantee_name: str
    grantee_email: str
    permission: str
    created_at: str


class WorkspaceOverview(BaseModel):
    folders: list[WorkspaceFolderRecord]
    notes: list[WorkspaceNoteRecord]
    documents: list[WorkspaceDocumentRecord]
    shares: list[WorkspaceShareRecord]
    users: list[WorkspaceUserOption]


class DashboardMatter(BaseModel):
    id: str
    title: str
    court: str
    matter_type: str
    client_name: str
    next_action: str | None
    limitation_date: date | None


class DashboardDocument(BaseModel):
    id: str
    filename: str
    content_type: str
    matter_id: str | None
    status: str
    created_at: str


class DashboardDeadline(BaseModel):
    id: str
    matter_id: str
    matter_title: str
    label: str
    due_date: date
    source: str
    status: str


class DashboardStats(BaseModel):
    matters: int
    documents: int
    active_users: int
    open_tasks: int
    upcoming_deadlines: int


class DashboardFirm(BaseModel):
    id: str
    name: str
    plan: str


class DashboardResponse(BaseModel):
    firm: DashboardFirm
    user: CurrentUser
    stats: DashboardStats
    recent_matters: list[DashboardMatter]
    recent_documents: list[DashboardDocument]
    upcoming_deadlines: list[DashboardDeadline]


@router.get("/items", response_model=list[WorkspaceItem])
def items(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[WorkspaceItem]:
    overview = workspace_overview(current_user, db)
    return [
        *[WorkspaceItem(id=folder.id, item_type="folder", name=folder.name, permission=folder.permission) for folder in overview.folders],
        *[WorkspaceItem(id=note.id, item_type="note", name=note.title, permission=note.permission) for note in overview.notes],
        *[WorkspaceItem(id=document.id, item_type="document", name=document.filename, permission=document.permission) for document in overview.documents],
    ]


@router.get("/overview", response_model=WorkspaceOverview)
def workspace_overview(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> WorkspaceOverview:
    users = firm_users(db, current_user)
    folders = db.scalars(select(WorkspaceFolder).where(WorkspaceFolder.firm_id == current_user.firm_id).order_by(WorkspaceFolder.created_at.desc())).all()
    notes = db.scalars(select(WorkspaceNote).where(WorkspaceNote.firm_id == current_user.firm_id).order_by(WorkspaceNote.updated_at.desc())).all()
    documents = db.scalars(select(Document).where(Document.firm_id == current_user.firm_id).order_by(Document.created_at.desc())).all()
    shares = db.scalars(select(WorkspaceShare).where(WorkspaceShare.firm_id == current_user.firm_id).order_by(WorkspaceShare.created_at.desc())).all()
    folder_permissions = {
        folder.id: permission_for(current_user, folder.owner_user_id, shares, "folder", folder.id)
        for folder in folders
    }
    visible_folder_ids = {folder_id for folder_id, permission in folder_permissions.items() if permission != "none"}
    visible_notes = [note for note in notes if can_view(current_user, note.owner_user_id, shares, "note", note.id) or (note.folder_id in visible_folder_ids)]
    visible_documents = [
        document
        for document in documents
        if can_view(current_user, document.created_by, shares, "document", document.id) or (document.folder_id in visible_folder_ids)
    ]
    return WorkspaceOverview(
        folders=[
            folder_record(
                folder,
                current_user,
                shares,
                notes_count=sum(1 for note in notes if note.folder_id == folder.id),
                documents_count=sum(1 for document in documents if document.folder_id == folder.id),
            )
            for folder in folders
            if folder.id in visible_folder_ids
        ],
        notes=[note_record(note, current_user, shares, inherited_permission=folder_permissions.get(note.folder_id or "")) for note in visible_notes],
        documents=[
            document_record(document, current_user, shares, inherited_permission=folder_permissions.get(document.folder_id or ""))
            for document in visible_documents
        ],
        shares=[share_record(share, users, folders, notes, documents) for share in shares if current_user.role == ROLE_ADMIN_ADVOCATE or share.created_by == current_user.user_id],
        users=users,
    )


@router.post("/folders", response_model=WorkspaceFolderRecord, status_code=201)
def create_folder(
    payload: WorkspaceFolderCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> WorkspaceFolderRecord:
    if payload.parent_folder_id:
        ensure_workspace_permission(db, current_user, "folder", payload.parent_folder_id, "edit")
    folder = WorkspaceFolder(
        firm_id=current_user.firm_id,
        name=payload.name,
        parent_folder_id=payload.parent_folder_id,
        owner_user_id=current_user.user_id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder_record(folder, current_user, [], 0, 0)


@router.patch("/folders/{folder_id}", response_model=WorkspaceFolderRecord)
def update_folder(
    folder_id: str,
    payload: WorkspaceFolderUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> WorkspaceFolderRecord:
    folder = ensure_workspace_permission(db, current_user, "folder", folder_id, "edit")
    if payload.name is not None:
        folder.name = payload.name
    if "parent_folder_id" in payload.model_fields_set:
        folder.parent_folder_id = payload.parent_folder_id
    db.commit()
    db.refresh(folder)
    shares = db.scalars(select(WorkspaceShare).where(WorkspaceShare.firm_id == current_user.firm_id)).all()
    return folder_record(folder, current_user, shares, 0, 0)


@router.post("/notes", response_model=WorkspaceNoteRecord, status_code=201)
def create_note(
    payload: WorkspaceNoteCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> WorkspaceNoteRecord:
    if payload.folder_id:
        ensure_workspace_permission(db, current_user, "folder", payload.folder_id, "edit")
    note = WorkspaceNote(
        firm_id=current_user.firm_id,
        folder_id=payload.folder_id,
        title=payload.title,
        body=payload.body,
        owner_user_id=current_user.user_id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note_record(note, current_user, [])


@router.patch("/notes/{note_id}", response_model=WorkspaceNoteRecord)
def update_note(
    note_id: str,
    payload: WorkspaceNoteUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> WorkspaceNoteRecord:
    note = ensure_workspace_permission(db, current_user, "note", note_id, "edit")
    if payload.title is not None:
        note.title = payload.title
    if payload.body is not None:
        note.body = payload.body
    if "folder_id" in payload.model_fields_set:
        if payload.folder_id:
            ensure_workspace_permission(db, current_user, "folder", payload.folder_id, "edit")
        note.folder_id = payload.folder_id
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    shares = db.scalars(select(WorkspaceShare).where(WorkspaceShare.firm_id == current_user.firm_id)).all()
    return note_record(note, current_user, shares)


@router.post("/shares", response_model=WorkspaceShareRecord, status_code=201)
def share_resource(
    payload: WorkspaceShareCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> WorkspaceShareRecord:
    if payload.resource_type not in {"folder", "note", "document"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported resource type")
    if payload.permission not in {"view", "edit"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported permission")
    ensure_workspace_permission(db, current_user, payload.resource_type, payload.resource_id, "edit")
    if not active_firm_membership(db, current_user, payload.grantee_user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an active member of this firm")
    existing = db.scalar(
        select(WorkspaceShare).where(
            WorkspaceShare.firm_id == current_user.firm_id,
            WorkspaceShare.resource_type == payload.resource_type,
            WorkspaceShare.resource_id == payload.resource_id,
            WorkspaceShare.grantee_user_id == payload.grantee_user_id,
        )
    )
    if existing:
        existing.permission = payload.permission
        share = existing
    else:
        share = WorkspaceShare(
            firm_id=current_user.firm_id,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            grantee_user_id=payload.grantee_user_id,
            permission=payload.permission,
            created_by=current_user.user_id,
        )
        db.add(share)
    db.commit()
    db.refresh(share)
    users = firm_users(db, current_user)
    folders = db.scalars(select(WorkspaceFolder).where(WorkspaceFolder.firm_id == current_user.firm_id)).all()
    notes = db.scalars(select(WorkspaceNote).where(WorkspaceNote.firm_id == current_user.firm_id)).all()
    documents = db.scalars(select(Document).where(Document.firm_id == current_user.firm_id)).all()
    return share_record(share, users, folders, notes, documents)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> DashboardResponse:
    today = date.today()
    deadline_window = today + timedelta(days=60)
    firm = db.get(Firm, current_user.firm_id)
    recent_matters = db.scalars(
        select(Matter).where(Matter.firm_id == current_user.firm_id).order_by(Matter.created_at.desc()).limit(6)
    ).all()
    recent_documents = db.scalars(
        select(Document).where(Document.firm_id == current_user.firm_id).order_by(Document.created_at.desc()).limit(6)
    ).all()
    limitation_matters = db.scalars(
        select(Matter)
        .where(
            Matter.firm_id == current_user.firm_id,
            Matter.limitation_date.is_not(None),
            Matter.limitation_date >= today,
            Matter.limitation_date <= deadline_window,
        )
        .order_by(Matter.limitation_date.asc())
        .limit(10)
    ).all()
    open_tasks = db.scalars(
        select(MatterTask)
        .where(
            MatterTask.firm_id == current_user.firm_id,
            MatterTask.status != "done",
            MatterTask.due_date.is_not(None),
            MatterTask.due_date >= today,
            MatterTask.due_date <= deadline_window,
        )
        .order_by(MatterTask.due_date.asc())
        .limit(10)
    ).all()
    matter_titles = {
        row.id: row.title
        for row in db.scalars(select(Matter).where(Matter.firm_id == current_user.firm_id)).all()
    }
    deadlines = [
        DashboardDeadline(
            id=f"lim_{matter.id}",
            matter_id=matter.id,
            matter_title=matter.title,
            label="Limitation date",
            due_date=matter.limitation_date,
            source="matter",
            status="open",
        )
        for matter in limitation_matters
        if matter.limitation_date
    ] + [
        DashboardDeadline(
            id=task.id,
            matter_id=task.matter_id,
            matter_title=matter_titles.get(task.matter_id, "Matter"),
            label=task.title,
            due_date=task.due_date,
            source="task",
            status=task.status,
        )
        for task in open_tasks
        if task.due_date
    ]
    deadlines.sort(key=lambda item: item.due_date)
    stats = DashboardStats(
        matters=db.scalar(select(func.count()).select_from(Matter).where(Matter.firm_id == current_user.firm_id)) or 0,
        documents=db.scalar(select(func.count()).select_from(Document).where(Document.firm_id == current_user.firm_id)) or 0,
        active_users=db.scalar(
            select(func.count()).select_from(Membership).where(Membership.firm_id == current_user.firm_id, Membership.seat_status == "active")
        )
        or 0,
        open_tasks=db.scalar(
            select(func.count()).select_from(MatterTask).where(MatterTask.firm_id == current_user.firm_id, MatterTask.status != "done")
        )
        or 0,
        upcoming_deadlines=len(deadlines),
    )
    return DashboardResponse(
        firm=DashboardFirm(id=current_user.firm_id, name=firm.name if firm else "Vakil Yantra Firm", plan=firm.plan if firm else current_user.plan),
        user=current_user,
        stats=stats,
        recent_matters=[
            DashboardMatter(
                id=matter.id,
                title=matter.title,
                court=matter.court,
                matter_type=matter.matter_type,
                client_name=matter.client_name,
                next_action=matter.next_action,
                limitation_date=matter.limitation_date,
            )
            for matter in recent_matters
        ],
        recent_documents=[
            DashboardDocument(
                id=document.id,
                filename=document.filename,
                content_type=document.content_type,
                matter_id=document.matter_id,
                status=document.status,
                created_at=document.created_at.isoformat(),
            )
            for document in recent_documents
        ],
        upcoming_deadlines=deadlines[:10],
    )


def firm_users(db: Session, current_user: CurrentUser) -> list[WorkspaceUserOption]:
    rows = db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.firm_id == current_user.firm_id, Membership.seat_status == "active", User.status == "active")
        .order_by(User.name.asc())
    ).all()
    return [
        WorkspaceUserOption(user_id=user.id, name=user.name, email=user.email, role=membership.role)
        for membership, user in rows
    ]


def active_firm_membership(db: Session, current_user: CurrentUser, user_id: str) -> bool:
    return bool(
        db.scalar(
            select(Membership).where(
                Membership.firm_id == current_user.firm_id,
                Membership.user_id == user_id,
                Membership.seat_status == "active",
            )
        )
    )


def ensure_workspace_permission(db: Session, current_user: CurrentUser, resource_type: str, resource_id: str, minimum: str):
    shares = db.scalars(select(WorkspaceShare).where(WorkspaceShare.firm_id == current_user.firm_id)).all()
    resource = get_workspace_resource(db, current_user, resource_type, resource_id)
    owner_id = getattr(resource, "owner_user_id", None) or getattr(resource, "created_by", None)
    permission = permission_for(current_user, owner_id, shares, resource_type, resource_id)
    folder_id = getattr(resource, "folder_id", None)
    if permission == "none" and folder_id:
        folder = db.scalar(select(WorkspaceFolder).where(WorkspaceFolder.id == folder_id, WorkspaceFolder.firm_id == current_user.firm_id))
        if folder:
            permission = permission_for(current_user, folder.owner_user_id, shares, "folder", folder.id)
    if permission == "none" or (minimum == "edit" and permission not in {"owner", "edit"}):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace permission denied")
    return resource


def get_workspace_resource(db: Session, current_user: CurrentUser, resource_type: str, resource_id: str):
    model = {"folder": WorkspaceFolder, "note": WorkspaceNote, "document": Document}.get(resource_type)
    if not model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported resource type")
    resource = db.scalar(select(model).where(model.id == resource_id, model.firm_id == current_user.firm_id))
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace resource not found")
    return resource


def can_view(current_user: CurrentUser, owner_user_id: str | None, shares: list[WorkspaceShare], resource_type: str, resource_id: str) -> bool:
    return permission_for(current_user, owner_user_id, shares, resource_type, resource_id) != "none"


def permission_for(current_user: CurrentUser, owner_user_id: str | None, shares: list[WorkspaceShare], resource_type: str, resource_id: str) -> str:
    if current_user.role == ROLE_ADMIN_ADVOCATE or owner_user_id == current_user.user_id:
        return "owner"
    share = next(
        (
            item
            for item in shares
            if item.resource_type == resource_type and item.resource_id == resource_id and item.grantee_user_id == current_user.user_id
        ),
        None,
    )
    return share.permission if share else "none"


def folder_record(
    folder: WorkspaceFolder,
    current_user: CurrentUser,
    shares: list[WorkspaceShare],
    notes_count: int,
    documents_count: int,
) -> WorkspaceFolderRecord:
    return WorkspaceFolderRecord(
        id=folder.id,
        name=folder.name,
        parent_folder_id=folder.parent_folder_id,
        owner_user_id=folder.owner_user_id,
        permission=permission_for(current_user, folder.owner_user_id, shares, "folder", folder.id),
        notes_count=notes_count,
        documents_count=documents_count,
        created_at=folder.created_at.isoformat(),
    )


def note_record(note: WorkspaceNote, current_user: CurrentUser, shares: list[WorkspaceShare], inherited_permission: str | None = None) -> WorkspaceNoteRecord:
    permission = permission_for(current_user, note.owner_user_id, shares, "note", note.id)
    if permission == "none" and inherited_permission:
        permission = inherited_permission
    return WorkspaceNoteRecord(
        id=note.id,
        folder_id=note.folder_id,
        title=note.title,
        body=note.body,
        owner_user_id=note.owner_user_id,
        permission=permission,
        updated_at=note.updated_at.isoformat(),
        created_at=note.created_at.isoformat(),
    )


def document_record(
    document: Document,
    current_user: CurrentUser,
    shares: list[WorkspaceShare],
    inherited_permission: str | None = None,
) -> WorkspaceDocumentRecord:
    permission = permission_for(current_user, document.created_by, shares, "document", document.id)
    if permission == "none" and inherited_permission:
        permission = inherited_permission
    return WorkspaceDocumentRecord(
        id=document.id,
        folder_id=document.folder_id,
        matter_id=document.matter_id,
        filename=document.filename,
        content_type=document.content_type,
        status=document.status,
        owner_user_id=document.created_by,
        permission=permission,
        created_at=document.created_at.isoformat(),
    )


def share_record(
    share: WorkspaceShare,
    users: list[WorkspaceUserOption],
    folders: list[WorkspaceFolder],
    notes: list[WorkspaceNote],
    documents: list[Document],
) -> WorkspaceShareRecord:
    user = next((item for item in users if item.user_id == share.grantee_user_id), None)
    return WorkspaceShareRecord(
        id=share.id,
        resource_type=share.resource_type,
        resource_id=share.resource_id,
        resource_name=resource_name(share, folders, notes, documents),
        grantee_user_id=share.grantee_user_id,
        grantee_name=user.name if user else "Unknown user",
        grantee_email=user.email if user else "",
        permission=share.permission,
        created_at=share.created_at.isoformat(),
    )


def resource_name(share: WorkspaceShare, folders: list[WorkspaceFolder], notes: list[WorkspaceNote], documents: list[Document]) -> str:
    if share.resource_type == "folder":
        return next((folder.name for folder in folders if folder.id == share.resource_id), "Folder")
    if share.resource_type == "note":
        return next((note.title for note in notes if note.id == share.resource_id), "Note")
    return next((document.filename for document in documents if document.id == share.resource_id), "Document")
