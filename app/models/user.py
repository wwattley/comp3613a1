from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import EmailStr

from enum import Enum
from datetime import datetime

class HOST_ACCOUNT_STATUS(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"


class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    phone: Optional[str] = None
    password: str
    role:str = ""
    # workflow2.png card shows "Uni:" — the student's university.
    university: Optional[str] = None
    # workflow3.png card shows "Face:" — the host's face image.
    face_filename: Optional[str] = None
    face_content_type: Optional[str] = None
    face_data: Optional[bytes] = None
    # workflow3.png card shows "Credentials:" — the host's credentials.
    credentials_filename: Optional[str] = None
    credentials_content_type: Optional[str] = None
    credentials_data: Optional[bytes] = None
    #workflow3.png card shows "Status:" — the host's account status.
    status: Optional[HOST_ACCOUNT_STATUS] = Field(default=HOST_ACCOUNT_STATUS.ACTIVE)
    applied_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None



class User(UserBase, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)