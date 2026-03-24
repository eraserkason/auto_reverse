from datetime import datetime

from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime


class PasswordUpdateRequest(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)
