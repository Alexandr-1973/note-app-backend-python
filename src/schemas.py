from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict



class UserSchema(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)

class UserUpdateSchema(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: EmailStr
    avatar: Optional[str] = Field(default=None, max_length=300)

class UserResponse(BaseModel):
    # id: int = 1
    username: str
    email: EmailStr
    avatar: str

    class Config:
        from_attributes = True

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class NoteSchema(BaseModel):
    title: str = Field(max_length=50)
    content: str = Field(max_length=150)
    tag: str = Field(max_length=50)



class NoteResponseSchema(NoteSchema):

    id: int = 1
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
