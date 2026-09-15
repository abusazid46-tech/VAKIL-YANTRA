from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.domain.auth.schemas import (
    AcceptInvitationRequest,
    AuthToken,
    CurrentUser,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    FirmUserRecord,
    InvitationRecord,
    InviteUserRequest,
    InviteUserResponse,
    LoginChallenge,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SignupRequest,
    UpdateFirmUserRequest,
    VerifyOtpRequest,
)
from app.domain.auth.service import (
    accept_invitation,
    create_login_challenge,
    direct_login,
    invite_user,
    list_firm_users,
    list_invitations,
    request_password_reset,
    reset_password,
    resend_invitation,
    signup_firm,
    update_firm_user,
    verify_otp,
)

router = APIRouter()


@router.post("/signup", response_model=AuthToken, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthToken:
    return signup_firm(db, payload)


@router.post("/direct-login", response_model=AuthToken)
def direct_authenticate(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthToken:
    return direct_login(db, payload.email, payload.password)


@router.post("/login", response_model=LoginChallenge)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginChallenge:
    return create_login_challenge(db, payload.email, payload.password)


@router.post("/verify-otp", response_model=AuthToken)
def verify(payload: VerifyOtpRequest, db: Session = Depends(get_db)) -> AuthToken:
    return verify_otp(db, payload.challenge_id, payload.otp)


@router.post("/invitations", response_model=InviteUserResponse, status_code=201)
def invite(
    payload: InviteUserRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> InviteUserResponse:
    return invite_user(db, current_user, payload.email, payload.role)


@router.get("/users", response_model=list[FirmUserRecord])
def users(current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)) -> list[FirmUserRecord]:
    return list_firm_users(db, current_user)


@router.patch("/users/{membership_id}", response_model=FirmUserRecord)
def update_user(
    membership_id: str,
    payload: UpdateFirmUserRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> FirmUserRecord:
    return update_firm_user(db, current_user, membership_id, payload)


@router.get("/invitations", response_model=list[InvitationRecord])
def invitations(current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)) -> list[InvitationRecord]:
    return list_invitations(db, current_user)


@router.post("/invitations/{invitation_id}/resend", response_model=InviteUserResponse)
def resend(
    invitation_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> InviteUserResponse:
    return resend_invitation(db, current_user, invitation_id)


@router.post("/invitations/accept", response_model=AuthToken)
def accept(payload: AcceptInvitationRequest, db: Session = Depends(get_db)) -> AuthToken:
    return accept_invitation(db, payload.token, payload.name, payload.password)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    return request_password_reset(db, payload.email)


@router.post("/reset-password", response_model=MessageResponse)
def complete_password_reset(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    return reset_password(db, payload.token, payload.new_password)


@router.get("/me", response_model=CurrentUser)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user
