from typing import Optional

from sqlmodel import Session, select

from app.models.listing import Listing
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User


class ReservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, reservation: Reservation) -> Reservation:
        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)
        return reservation

    def get_by_id(self, reservation_id: int) -> Optional[Reservation]:
        return self.db.get(Reservation, reservation_id)

    def for_host(
        self,
        host_id: int,
        status: Optional[ReservationStatus] = None,
    ) -> list[tuple]:
        """Reservations on this host's listings, newest first.

        Returns (reservation, listing, student) triples so the approvals
        screen can show Listing #, Name and Uni without N+1 lookups.
        """
        statement = (
            select(Reservation, Listing, User)
            .join(Listing, Listing.listing_id == Reservation.listing_id)
            .join(User, User.user_id == Reservation.user_id)
            .where(Listing.host_id == host_id)
            .order_by(Reservation.reserved_at.desc(), Reservation.reservation_id.desc())
        )
        if status is not None:
            statement = statement.where(Reservation.status == status)
        return list(self.db.exec(statement).all())
