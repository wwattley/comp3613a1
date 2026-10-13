from typing import Optional

from sqlmodel import Session, select, func

from app.models.listing import Listing
from app.models.reservation import Reservation, ReservationStatus


class ListingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, listing_id: int) -> Optional[Listing]:
        return self.db.get(Listing, listing_id)

    def search(
        self,
        location: Optional[str] = None,
        capacity: Optional[int] = None,
    ) -> list[Listing]:
        statement = select(Listing)
        if location is not None:
            statement = statement.where(Listing.location == location)
        if capacity is not None:
            statement = statement.where(Listing.capacity == capacity)

        return list(self.db.exec(statement).all())

    def images_for(self, listing_ids: list[int]) -> dict[int, list]:
        """Glue: group each listing's photos for the explore cards."""
        if not listing_ids:
            return {}
        from app.models.listing_image import ListingImage

        rows = self.db.exec(
            select(ListingImage).where(ListingImage.listing_id.in_(listing_ids))
        ).all()
        grouped: dict[int, list] = {}
        for image in rows:
            grouped.setdefault(image.listing_id, []).append(image)
        return grouped

    def active_reservation_count(self, listing_id: int) -> int:
        statement = (
            select(func.count(Reservation.reservation_id))
            .where(
                Reservation.listing_id == listing_id,
                Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.APPROVED])
            )
        )
        return self.db.exec(statement).one()

    def viewer_reservation(self, listing_id: int, user_id: int) -> Optional[Reservation]:
        statement = (
            select(Reservation)
            .where(
                Reservation.listing_id == listing_id,
                Reservation.user_id == user_id,
            )
            .order_by(Reservation.reserved_at.desc(), Reservation.reservation_id.desc())
        )
        return self.db.exec(statement).first()