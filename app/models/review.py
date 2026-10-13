from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class Review(SQLModel, table=True):
    review_id: Optional[int] = Field(default=None, primary_key=True)
    reservation_id: int = Field(foreign_key="reservation.reservation_id", index=True)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.today)