from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class Notification(SQLModel, table=True):
    notification_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id", index=True)
    reservation_id: Optional[int] = Field(foreign_key="reservation.reservation_id", index=True)
    message: str
    created_at: datetime = Field(default_factory=datetime.today)
    is_read: bool = Field(default=False)