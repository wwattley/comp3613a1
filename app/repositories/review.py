from sqlmodel import Session, select

from app.models.reservation import Reservation, ReservationStatus
from app.models.review import Review
from app.models.user import User


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, review: Review) -> Review:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def for_listing(self, listing_id: int, limit: int = 50) -> list[tuple[Review, User]]:
        """Reviews left on a listing, newest first.

        Phase 3 rule enforced on read as well as write: only an `approved`
        reservation may produce a review, so anything hanging off a pending,
        rejected or cancelled reservation is not shown. Returns
        (review, student) pairs so the listing page can name the reviewer
        without an N+1 lookup.
        """
        statement = (
            select(Review, User)
            .join(Reservation, Reservation.reservation_id == Review.reservation_id)
            .join(User, User.user_id == Reservation.user_id)
            .where(
                Reservation.listing_id == listing_id,
                Reservation.status == ReservationStatus.APPROVED,
            )
            .order_by(Review.created_at.desc(), Review.review_id.desc())
            .limit(limit)
        )
        return list(self.db.exec(statement).all())
