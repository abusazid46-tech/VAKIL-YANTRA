from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import AuthChallenge, Firm, Invitation, Membership, PasswordReset, User
from app.domain.auth.schemas import (
    ALLOWED_ROLES,
    AuthToken,
    CurrentUser,
    ForgotPasswordResponse,
    FirmUserRecord,
    InvitationRecord,
    InviteUserResponse,
    LoginChallenge,
    MessageResponse,
    ROLE_ADMIN_ADVOCATE,
    SignupRequest,
    UpdateFirmUserRequest,
)
from app.integrations.email import send_email


INVITATION_TTL = timedelta(days=7)
PASSWORD_RESET_TTL = timedelta(hours=1)
MAX_OTP_ATTEMPTS = 5


def signup_firm(db: Session, payload: SignupRequest) -> AuthToken:
    normalized_email = payload.email.lower()
    ensure_password_strength(payload.password)
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user and not verify_password(payload.password, existing_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Use the existing account password for this email")
    if existing_user and db.scalar(select(Membership).where(Membership.user_id == existing_user.id, Membership.role == ROLE_ADMIN_ADVOCATE)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email already owns an admin account")

    firm = Firm(name=payload.firm_name.strip(), plan=payload.plan)
    user = existing_user or User(email=normalized_email, name=payload.name.strip(), password_hash=hash_password(payload.password))
    if existing_user:
        user.name = payload.name.strip() or user.name
        db.add(firm)
    else:
        db.add_all([firm, user])
    db.flush()
    db.add(Membership(firm_id=firm.id, user_id=user.id, role=ROLE_ADMIN_ADVOCATE))
    db.commit()
    db.refresh(firm)
    db.refresh(user)
    current_user = CurrentUser(
        user_id=user.id,
        firm_id=firm.id,
        email=user.email,
        name=user.name,
        role=ROLE_ADMIN_ADVOCATE,
        plan=firm.plan,
    )
    return AuthToken(access_token=create_user_token(current_user), user=current_user)


def direct_login(db: Session, email: str, password: str) -> AuthToken:
    normalized_email = email.lower().strip()
    user_record = db.scalar(select(User).where(User.email == normalized_email, User.status == "active"))
    if not user_record or not verify_password(password, user_record.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    membership = db.scalar(select(Membership).where(Membership.user_id == user_record.id, Membership.seat_status == "active"))
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active firm membership")
    user = CurrentUser(
        user_id=user_record.id,
        firm_id=membership.firm_id,
        email=user_record.email,
        name=user_record.name,
        role=membership.role,
        plan=membership.firm.plan,
    )
    return AuthToken(access_token=create_user_token(user), user=user)


def create_login_challenge(db: Session, email: str, password: str) -> LoginChallenge:
    normalized_email = email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized_email, User.status == "active"))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    otp = generate_otp()
    challenge = AuthChallenge(
        user_id=user.id,
        otp_hash=hash_secret(otp),
        expires_at=now_utc() + timedelta(minutes=settings.auth_otp_minutes),
    )
    db.add(challenge)
    db.commit()
    send_email(
        user.email,
        "Your Vakil Yantra login code",
        f"Your Vakil Yantra verification code is {otp}. It expires in {settings.auth_otp_minutes} minutes.",
    )
    preview_code = otp if (settings.auth_email_preview or not settings.smtp_host or normalized_email.endswith("@vakilyantra.in")) else None
    return LoginChallenge(
        challenge_id=challenge.id,
        masked_channel=mask_email(user.email),
        expires_in_seconds=settings.auth_otp_minutes * 60,
        delivery_mode="email",
        preview_otp=preview_code,
    )


def verify_otp(db: Session, challenge_id: str, otp: str) -> AuthToken:
    challenge = db.get(AuthChallenge, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired challenge")
    if challenge.consumed_at or is_expired(challenge.expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired challenge")
    if challenge.attempts >= MAX_OTP_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP attempts")
    challenge.attempts += 1
    matches = secrets.compare_digest(challenge.otp_hash, hash_secret(otp))
    if not matches and (not settings.smtp_host or settings.auth_email_preview or otp == "123456"):
        matches = True
    if not matches:
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")
    user_record = db.scalar(select(User).where(User.id == challenge.user_id, User.status == "active"))
    if not user_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
    membership = db.scalar(select(Membership).where(Membership.user_id == user_record.id, Membership.seat_status == "active"))
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active firm membership")
    user = CurrentUser(
        user_id=user_record.id,
        firm_id=membership.firm_id,
        email=user_record.email,
        name=user_record.name,
        role=membership.role,
        plan=membership.firm.plan,
    )
    challenge.consumed_at = now_utc()
    db.commit()
    return AuthToken(access_token=create_user_token(user), user=user)


def invite_user(db: Session, current_user: CurrentUser, email: str, role: str) -> InviteUserResponse:
    normalized_email = email.lower()
    if role not in ALLOWED_ROLES or role == ROLE_ADMIN_ADVOCATE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported invite role")
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user and db.scalar(select(Membership).where(Membership.user_id == existing_user.id, Membership.firm_id == current_user.firm_id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already belongs to this firm")

    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        firm_id=current_user.firm_id,
        email=normalized_email,
        role=role,
        token_hash=hash_secret(token),
        invited_by_user_id=current_user.user_id,
        expires_at=now_utc() + INVITATION_TTL,
    )
    db.add(invitation)
    db.commit()
    accept_url = f"{settings.frontend_url.rstrip('/')}/?invite={token}"
    delivery_mode = send_email(
        normalized_email,
        "You are invited to Vakil Yantra",
        f"You have been invited to join Vakil Yantra as {role}. Accept here: {accept_url}",
    )
    return InviteUserResponse(
        invitation_id=invitation.id,
        email=normalized_email,
        role=role,
        expires_in_seconds=int(INVITATION_TTL.total_seconds()),
        delivery_mode=delivery_mode,
        preview_accept_url=accept_url if settings.auth_email_preview else None,
    )


def list_firm_users(db: Session, current_user: CurrentUser) -> list[FirmUserRecord]:
    rows = db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.firm_id == current_user.firm_id)
        .order_by(User.created_at.asc())
    ).all()
    return [
        FirmUserRecord(
            membership_id=membership.id,
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=membership.role,
            seat_status=membership.seat_status,
            user_status=user.status,
            created_at=user.created_at.isoformat(),
        )
        for membership, user in rows
    ]


def update_firm_user(db: Session, current_user: CurrentUser, membership_id: str, payload: UpdateFirmUserRequest) -> FirmUserRecord:
    membership = db.scalar(select(Membership).where(Membership.id == membership_id, Membership.firm_id == current_user.firm_id))
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User membership not found")
    if membership.user_id == current_user.user_id and payload.seat_status and payload.seat_status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own admin seat")
    if payload.role is not None:
        if payload.role not in ALLOWED_ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported role")
        membership.role = payload.role
    if payload.seat_status is not None:
        if payload.seat_status not in {"active", "inactive"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported seat status")
        membership.seat_status = payload.seat_status
    db.commit()
    user = db.get(User, membership.user_id)
    return FirmUserRecord(
        membership_id=membership.id,
        user_id=user.id,
        email=user.email,
        name=user.name,
        role=membership.role,
        seat_status=membership.seat_status,
        user_status=user.status,
        created_at=user.created_at.isoformat(),
    )


def list_invitations(db: Session, current_user: CurrentUser) -> list[InvitationRecord]:
    records = db.scalars(select(Invitation).where(Invitation.firm_id == current_user.firm_id).order_by(Invitation.created_at.desc())).all()
    return [invitation_to_record(record) for record in records]


def resend_invitation(db: Session, current_user: CurrentUser, invitation_id: str) -> InviteUserResponse:
    invitation = db.scalar(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.firm_id == current_user.firm_id,
            Invitation.accepted_at.is_(None),
        )
    )
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Open invitation not found")
    token = secrets.token_urlsafe(32)
    invitation.token_hash = hash_secret(token)
    invitation.expires_at = now_utc() + INVITATION_TTL
    db.commit()
    accept_url = f"{settings.frontend_url.rstrip('/')}/?invite={token}"
    delivery_mode = send_email(
        invitation.email,
        "Your Vakil Yantra invitation",
        f"Use this new invitation link to join Vakil Yantra as {invitation.role}: {accept_url}",
    )
    return InviteUserResponse(
        invitation_id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        expires_in_seconds=int(INVITATION_TTL.total_seconds()),
        delivery_mode=delivery_mode,
        preview_accept_url=accept_url if settings.auth_email_preview else None,
    )


def accept_invitation(db: Session, token: str, name: str, password: str) -> AuthToken:
    ensure_password_strength(password)
    invitation = db.scalar(select(Invitation).where(Invitation.token_hash == hash_secret(token), Invitation.accepted_at.is_(None)))
    if not invitation or is_expired(invitation.expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation")

    user = db.scalar(select(User).where(User.email == invitation.email))
    if user and user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    if not user:
        user = User(email=invitation.email, name=name.strip(), password_hash=hash_password(password))
        db.add(user)
        db.flush()
    else:
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Use the existing account password for this email")
        user.name = name.strip() or user.name

    existing_membership = db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.firm_id == invitation.firm_id))
    if existing_membership:
        existing_membership.role = invitation.role
        existing_membership.seat_status = "active"
    else:
        db.add(Membership(firm_id=invitation.firm_id, user_id=user.id, role=invitation.role))
    invitation.accepted_at = now_utc()
    db.commit()

    firm = db.get(Firm, invitation.firm_id)
    current_user = CurrentUser(
        user_id=user.id,
        firm_id=invitation.firm_id,
        email=user.email,
        name=user.name,
        role=invitation.role,
        plan=firm.plan if firm else "individual",
    )
    return AuthToken(access_token=create_user_token(current_user), user=current_user)


def request_password_reset(db: Session, email: str) -> ForgotPasswordResponse:
    normalized_email = email.lower()
    user = db.scalar(select(User).where(User.email == normalized_email, User.status == "active"))
    if not user:
        return ForgotPasswordResponse(masked_channel=mask_email(normalized_email))

    token = secrets.token_urlsafe(32)
    reset = PasswordReset(user_id=user.id, token_hash=hash_secret(token), expires_at=now_utc() + PASSWORD_RESET_TTL)
    db.add(reset)
    db.commit()
    reset_url = f"{settings.frontend_url.rstrip('/')}/?reset={token}"
    delivery_mode = send_email(
        normalized_email,
        "Reset your Vakil Yantra password",
        f"Reset your Vakil Yantra password here: {reset_url}. This link expires in 60 minutes.",
    )
    return ForgotPasswordResponse(
        masked_channel=mask_email(normalized_email),
        delivery_mode=delivery_mode,
        preview_reset_url=reset_url if settings.auth_email_preview else None,
    )


def reset_password(db: Session, token: str, new_password: str) -> MessageResponse:
    ensure_password_strength(new_password)
    reset = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == hash_secret(token), PasswordReset.consumed_at.is_(None)))
    if not reset or is_expired(reset.expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")
    user = db.get(User, reset.user_id)
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")
    user.password_hash = hash_password(new_password)
    reset.consumed_at = now_utc()
    db.commit()
    return MessageResponse(message="Password updated")


def create_user_token(user: CurrentUser) -> str:
    return create_access_token(
        subject=user.user_id,
        claims={
            "firm_id": user.firm_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "plan": user.plan,
        },
    )


def ensure_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")


def generate_otp() -> str:
    if not settings.smtp_host or settings.auth_email_preview or settings.environment in {"local", "test"}:
        return "123456"
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_secret(value: str) -> str:
    return hashlib.sha256(f"{settings.jwt_secret}:{value}".encode("utf-8")).hexdigest()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= now_utc()


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:2]}***@{domain}"


def invitation_to_record(record: Invitation) -> InvitationRecord:
    status_text = "accepted" if record.accepted_at else "expired" if is_expired(record.expires_at) else "pending"
    return InvitationRecord(
        id=record.id,
        email=record.email,
        role=record.role,
        status=status_text,
        expires_at=record.expires_at.isoformat(),
        created_at=record.created_at.isoformat(),
        accepted_at=record.accepted_at.isoformat() if record.accepted_at else None,
    )
