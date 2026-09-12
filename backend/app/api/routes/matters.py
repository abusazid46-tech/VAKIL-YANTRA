from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant_db, require_roles
from app.domain.auth.schemas import CurrentUser, ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE, ROLE_CLERK
from app.domain.matters.schemas import Matter, MatterCreate, MatterDetail, MatterNote, MatterNoteCreate, MatterTask, MatterTaskCreate, MatterTaskUpdate, MatterUpdate
from app.domain.matters.service import add_note, add_task, create_matter, get_matter_detail, list_matters, update_matter, update_task

router = APIRouter()


@router.get("", response_model=list[Matter])
def index(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> list[Matter]:
    return list_matters(db, current_user)


@router.post("", response_model=Matter, status_code=201)
def create(
    payload: MatterCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE)),
    db: Session = Depends(get_tenant_db),
) -> Matter:
    return create_matter(db, current_user, payload)


@router.get("/{matter_id}", response_model=MatterDetail)
def detail(
    matter_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> MatterDetail:
    return get_matter_detail(db, current_user, matter_id)


@router.patch("/{matter_id}", response_model=Matter)
def patch(
    matter_id: str,
    payload: MatterUpdate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE)),
    db: Session = Depends(get_tenant_db),
) -> Matter:
    return update_matter(db, current_user, matter_id, payload)


@router.post("/{matter_id}/notes", response_model=MatterNote, status_code=201)
def create_note(
    matter_id: str,
    payload: MatterNoteCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE, ROLE_CLERK)),
    db: Session = Depends(get_tenant_db),
) -> MatterNote:
    return add_note(db, current_user, matter_id, payload)


@router.post("/{matter_id}/tasks", response_model=MatterTask, status_code=201)
def create_task(
    matter_id: str,
    payload: MatterTaskCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE, ROLE_CLERK)),
    db: Session = Depends(get_tenant_db),
) -> MatterTask:
    return add_task(db, current_user, matter_id, payload)


@router.patch("/{matter_id}/tasks/{task_id}", response_model=MatterTask)
def patch_task(
    matter_id: str,
    task_id: str,
    payload: MatterTaskUpdate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE, ROLE_ASSOCIATE, ROLE_CLERK)),
    db: Session = Depends(get_tenant_db),
) -> MatterTask:
    return update_task(db, current_user, matter_id, task_id, payload)
