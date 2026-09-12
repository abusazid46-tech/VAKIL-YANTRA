from datetime import date
from pydantic import BaseModel, Field


class MatterCreate(BaseModel):
    title: str = Field(min_length=3)
    court: str
    matter_type: str
    client_name: str
    next_action: str | None = None
    limitation_date: date | None = None


class MatterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    court: str | None = None
    matter_type: str | None = None
    client_name: str | None = None
    status: str | None = None
    next_action: str | None = None
    limitation_date: date | None = None


class Matter(BaseModel):
    id: str
    firm_id: str
    title: str
    court: str
    matter_type: str
    client_name: str
    status: str = "active"
    next_action: str | None = None
    limitation_date: date | None = None


class MatterNoteCreate(BaseModel):
    body: str = Field(min_length=2)


class MatterNote(BaseModel):
    id: str
    matter_id: str
    body: str
    created_by: str
    created_at: str


class MatterTaskCreate(BaseModel):
    title: str = Field(min_length=2)
    due_date: date | None = None
    assigned_to_user_id: str | None = None


class MatterTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2)
    due_date: date | None = None
    assigned_to_user_id: str | None = None
    status: str | None = None


class MatterTask(BaseModel):
    id: str
    matter_id: str
    title: str
    due_date: date | None
    status: str
    assigned_to_user_id: str | None
    created_by: str
    created_at: str


class MatterDetail(Matter):
    notes: list[MatterNote]
    tasks: list[MatterTask]
    documents_count: int
