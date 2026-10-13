from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

from sqlalchemy import Index, text
from enum import Enum

class ReservationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class ACTIVE_STATUSES(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"


class Reservation(SQLModel, table=True):
    __table_args__ = (
        Index(
            "uq_reservation_active_user_listing",
            "user_id",
            "listing_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'APPROVED')"),
            sqlite_where=text("status IN ('PENDING', 'APPROVED')")
        ),
    )

    reservation_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id", index=True)  # the student
    listing_id: int = Field(foreign_key="listing.listing_id", index=True)
    reserved_at: datetime = Field(default_factory=datetime.today) 
    status: ReservationStatus = Field(default=ReservationStatus.PENDING)
    proof_filename: Optional[str] = None
    proof_content_type: Optional[str] = None
    proof_data: Optional[bytes] = None
    cancelled_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None  # approval not final until confirmed