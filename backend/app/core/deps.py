from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db, set_tenant_context
from app.domain.auth.schemas import CurrentUser, ROLE_ADMIN_ADVOCATE

bearer = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return CurrentUser(
        user_id=payload["sub"],
        firm_id=payload["firm_id"],
        email=payload["email"],
        name=payload["name"],
        role=payload["role"],
        plan=payload["plan"],
    )


def get_tenant_db(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Session:
    set_tenant_context(db, current_user.firm_id)
    return db


def require_roles(*roles: str):
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permission")
        return current_user

    return dependency


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != ROLE_ADMIN_ADVOCATE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin advocate role required")
    return current_user
