from typing import Optional
from decimal import Decimal
from sqlmodel import Field, SQLModel

class Listing(SQLModel, table=True):
    listing_id: Optional[int] = Field(default=None, primary_key=True)
    host_id: int = Field(foreign_key="user.user_id")
    title: str
    location: str
    capacity: int
    monthly_rent: Decimal 
    duration_months: int
    description: str