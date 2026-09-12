from fastapi import APIRouter
from app.db.session import get_database_status

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vakil-yantra-api", **get_database_status()}
