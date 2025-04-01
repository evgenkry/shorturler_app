from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List

class LinkBase(BaseModel):
    original_url: HttpUrl
    expires_at: Optional[datetime] = None

class LinkCreate(LinkBase):
    custom_alias: Optional[str] = None

class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    expires_at: Optional[datetime] = None

class LinkResponse(BaseModel):
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class LinkStats(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    redirect_count: int
    last_accessed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class LinkSearch(BaseModel):
    original_url: HttpUrl

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
