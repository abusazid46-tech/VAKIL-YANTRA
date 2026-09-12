from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Firm(Base):
    __tablename__ = "firms"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("firm"))
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    plan: Mapped[str] = mapped_column(String(40), default="individual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    memberships: Mapped[list["Membership"]] = relationship(back_populates="firm")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("usr"))
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("firm_id", "user_id", name="uq_memberships_firm_user"),)

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("mem"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(48), nullable=False)
    seat_status: Mapped[str] = mapped_column(String(32), default="active")

    firm: Mapped[Firm] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class AuthChallenge(Base):
    __tablename__ = "auth_challenges"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("otp"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    otp_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    delivery_channel: Mapped[str] = mapped_column(String(32), default="email")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (UniqueConstraint("firm_id", "email", "accepted_at", name="uq_open_invitation_email"),)

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("inv"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(48), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    invited_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("rst"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Matter(Base):
    __tablename__ = "matters"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("mat"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    court: Mapped[str] = mapped_column(String(180), nullable=False)
    matter_type: Mapped[str] = mapped_column(String(120), nullable=False)
    client_name: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    next_action: Mapped[str | None] = mapped_column(String(300))
    limitation_date: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MatterNote(Base):
    __tablename__ = "matter_notes"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("note"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MatterTask(Base):
    __tablename__ = "matter_tasks"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("task"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="open")
    assigned_to_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WorkspaceFolder(Base):
    __tablename__ = "workspace_folders"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("fld"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    parent_folder_id: Mapped[str | None] = mapped_column(ForeignKey("workspace_folders.id", ondelete="CASCADE"), index=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WorkspaceNote(Base):
    __tablename__ = "workspace_notes"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("wnote"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id: Mapped[str | None] = mapped_column(ForeignKey("workspace_folders.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WorkspaceShare(Base):
    __tablename__ = "workspace_shares"
    __table_args__ = (UniqueConstraint("firm_id", "resource_type", "resource_id", "grantee_user_id", name="uq_workspace_share_target"),)

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("shr"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    grantee_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("doc"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    matter_id: Mapped[str | None] = mapped_column(ForeignKey("matters.id", ondelete="SET NULL"), index=True)
    folder_id: Mapped[str | None] = mapped_column(ForeignKey("workspace_folders.id", ondelete="SET NULL"), index=True)
    filename: Mapped[str] = mapped_column(String(260), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="awaiting_upload")
    storage_key: Mapped[str | None] = mapped_column(String(500))
    checksum: Mapped[str | None] = mapped_column(String(128))
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LegalSource(Base):
    __tablename__ = "legal_sources"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    title: Mapped[str] = mapped_column(String(260), nullable=False)
    source_type: Mapped[str] = mapped_column(String(60), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    public_url: Mapped[str] = mapped_column(String(600), nullable=False)
    effective_status: Mapped[str] = mapped_column(String(40), default="current")


class AiRun(Base):
    __tablename__ = "ai_runs"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("airun"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    run_type: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), default="stub-v1")
    output_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(48), primary_key=True, default=lambda: new_id("aud"))
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
