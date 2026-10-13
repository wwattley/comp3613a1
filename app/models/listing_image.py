from typing import Optional
from sqlmodel import Field, SQLModel


class ListingImage(SQLModel, table=True):
    image_id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.listing_id", index=True)
    image_url: str
    caption: str = ""
