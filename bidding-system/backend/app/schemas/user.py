from datetime import datetime
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "partner"  # admin | partner


class UserUpdate(BaseModel):
    role: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_admin: bool
    created_at: datetime
