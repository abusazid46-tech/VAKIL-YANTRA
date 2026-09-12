from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Document as DocumentModel
from app.db.models import Matter as MatterModel
from app.db.models import MatterNote as MatterNoteModel
from app.db.models import MatterTask as MatterTaskModel
from app.domain.auth.schemas import CurrentUser
from app.domain.matters.schemas import (
    Matter,
    MatterCreate,
    MatterDetail,
    MatterNote,
    MatterNoteCreate,
    MatterTask,
    MatterTaskCreate,
    MatterTaskUpdate,
    MatterUpdate,
)


def list_matters(db: Session, user: CurrentUser) -> list[Matter]:
    records = db.scalars(select(MatterModel).where(MatterModel.firm_id == user.firm_id).order_by(MatterModel.created_at.desc()))
    return [to_schema(record) for record in records]


def create_matter(db: Session, user: CurrentUser, payload: MatterCreate) -> Matter:
    matter = MatterModel(firm_id=user.firm_id, created_by=user.user_id, **payload.model_dump())
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return to_schema(matter)


def get_matter_detail(db: Session, user: CurrentUser, matter_id: str) -> MatterDetail:
    matter = get_matter_record(db, user, matter_id)
    notes = db.scalars(
        select(MatterNoteModel)
        .where(MatterNoteModel.firm_id == user.firm_id, MatterNoteModel.matter_id == matter_id)
        .order_by(MatterNoteModel.created_at.desc())
    ).all()
    tasks = db.scalars(
        select(MatterTaskModel)
        .where(MatterTaskModel.firm_id == user.firm_id, MatterTaskModel.matter_id == matter_id)
        .order_by(MatterTaskModel.due_date.asc().nulls_last(), MatterTaskModel.created_at.desc())
    ).all()
    documents_count = db.scalar(
        select(func.count()).select_from(DocumentModel).where(DocumentModel.firm_id == user.firm_id, DocumentModel.matter_id == matter_id)
    )
    base = to_schema(matter).model_dump()
    return MatterDetail(
        **base,
        notes=[note_to_schema(note) for note in notes],
        tasks=[task_to_schema(task) for task in tasks],
        documents_count=documents_count or 0,
    )


def update_matter(db: Session, user: CurrentUser, matter_id: str, payload: MatterUpdate) -> Matter:
    matter = get_matter_record(db, user, matter_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(matter, key, value)
    db.commit()
    db.refresh(matter)
    return to_schema(matter)


def add_note(db: Session, user: CurrentUser, matter_id: str, payload: MatterNoteCreate) -> MatterNote:
    get_matter_record(db, user, matter_id)
    note = MatterNoteModel(firm_id=user.firm_id, matter_id=matter_id, body=payload.body, created_by=user.user_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note_to_schema(note)


def add_task(db: Session, user: CurrentUser, matter_id: str, payload: MatterTaskCreate) -> MatterTask:
    get_matter_record(db, user, matter_id)
    task = MatterTaskModel(
        firm_id=user.firm_id,
        matter_id=matter_id,
        title=payload.title,
        due_date=payload.due_date,
        assigned_to_user_id=payload.assigned_to_user_id,
        created_by=user.user_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_to_schema(task)


def update_task(db: Session, user: CurrentUser, matter_id: str, task_id: str, payload: MatterTaskUpdate) -> MatterTask:
    get_matter_record(db, user, matter_id)
    task = db.scalar(
        select(MatterTaskModel).where(
            MatterTaskModel.id == task_id,
            MatterTaskModel.firm_id == user.firm_id,
            MatterTaskModel.matter_id == matter_id,
        )
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task_to_schema(task)


def get_matter_record(db: Session, user: CurrentUser, matter_id: str) -> MatterModel:
    matter = db.scalar(select(MatterModel).where(MatterModel.id == matter_id, MatterModel.firm_id == user.firm_id))
    if not matter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")
    return matter


def to_schema(record: MatterModel) -> Matter:
    return Matter(
        id=record.id,
        firm_id=record.firm_id,
        title=record.title,
        court=record.court,
        matter_type=record.matter_type,
        client_name=record.client_name,
        status=record.status,
        next_action=record.next_action,
        limitation_date=record.limitation_date,
    )


def note_to_schema(record: MatterNoteModel) -> MatterNote:
    return MatterNote(
        id=record.id,
        matter_id=record.matter_id,
        body=record.body,
        created_by=record.created_by,
        created_at=record.created_at.isoformat(),
    )


def task_to_schema(record: MatterTaskModel) -> MatterTask:
    return MatterTask(
        id=record.id,
        matter_id=record.matter_id,
        title=record.title,
        due_date=record.due_date,
        status=record.status,
        assigned_to_user_id=record.assigned_to_user_id,
        created_by=record.created_by,
        created_at=record.created_at.isoformat(),
    )
