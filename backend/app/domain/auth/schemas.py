from pydantic import BaseModel

try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # type: ignore[misc,assignment]


ROLE_ADMIN_ADVOCATE = "admin_advocate"
ROLE_ADVOCATE = "advocate"
ROLE_ASSOCIATE = "associate"
ROLE_CLERK = "clerk"
ROLE_CLIENT = "client"
ALLOWED_ROLES = {ROLE_ADMIN_ADVOCATE, ROLE_ADVOCATE}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginChallenge(BaseModel):
    challenge_id: str
    masked_channel: str
    expires_in_seconds: int = 300
    delivery_mode: str = "email"
    preview_otp: str | None = None


class VerifyOtpRequest(BaseModel):
    challenge_id: str
    otp: str


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "CurrentUser"


class CurrentUser(BaseModel):
    user_id: str
    firm_id: str
    email: EmailStr
    name: str
    role: str
    plan: str


class SignupRequest(BaseModel):
    firm_name: str
    name: str
    email: EmailStr
    password: str
    plan: str = "individual"


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: str


class InviteUserResponse(BaseModel):
    invitation_id: str
    email: EmailStr
    role: str
    expires_in_seconds: int
    delivery_mode: str
    preview_accept_url: str | None = None


class InvitationRecord(BaseModel):
    id: str
    email: EmailStr
    role: str
    status: str
    expires_at: str
    created_at: str
    accepted_at: str | None = None


class FirmUserRecord(BaseModel):
    membership_id: str
    user_id: str
    email: EmailStr
    name: str
    role: str
    seat_status: str
    user_status: str
    created_at: str


class UpdateFirmUserRequest(BaseModel):
    role: str | None = None
    seat_status: str | None = None


class AcceptInvitationRequest(BaseModel):
    token: str
    name: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    accepted: bool = True
    masked_channel: str | None = None
    delivery_mode: str | None = None
    preview_reset_url: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


AuthToken.model_rebuild()
