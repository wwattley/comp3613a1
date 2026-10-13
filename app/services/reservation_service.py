from datetime import datetime
from typing import Optional

from app.models.notification import Notification
from app.models.reservation import Reservation, ReservationStatus, ACTIVE_STATUSES 
from app.models.user import User
from app.repositories.listing import ListingRepository
from app.repositories.notification import NotificationRepository
from app.repositories.reservation import ReservationRepository



class ReservationService:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        listing_repo: ListingRepository,
        notification_repo: Optional[NotificationRepository] = None,
    ):
        self.reservation_repo = reservation_repo
        self.listing_repo = listing_repo
        self.notification_repo = notification_repo

    def reserve(
        self,
        listing_id: int,
        student: User,
        proof_filename: Optional[str] = None,
        proof_content_type: Optional[str] = None,
        proof_data: Optional[bytes] = None,
    ) -> Reservation:
        if student.role == "host":
            raise ValueError(
                f"Host {student.user_id} cannot reserve listings — hosts only browse and review reservations"
            )

        listing = self.listing_repo.get_by_id(listing_id)
        if listing is None:
            raise ValueError(f"Listing {listing_id} not found")

        existing_reservation = self.listing_repo.viewer_reservation(listing_id, student.user_id)
        if existing_reservation is not None and existing_reservation.status in ACTIVE_STATUSES:
            raise ValueError(f"Student {student.user_id} already has an active reservation for listing {listing_id}")

        if self.listing_repo.active_reservation_count(listing_id) >= listing.capacity:
            raise ValueError(f"Listing {listing_id} is full")

        reservation = Reservation(
            user_id=student.user_id,
            listing_id=listing_id,
            proof_filename=proof_filename,
            proof_content_type=proof_content_type,
            proof_data=proof_data,
        )
        created = self.reservation_repo.create(reservation)
        self._notify(
            user_id=listing.host_id,
            reservation_id=created.reservation_id,
            message=f"New reservation request from {student.username} for listing {listing_id} — awaiting your approval.",
        )
        return created

    def cancel(self, reservation: Reservation, student: User) -> Reservation:
        if reservation.user_id != student.user_id:
            raise ValueError(f"Student {student.user_id} cannot cancel reservation {reservation.reservation_id} because they are not the owner")

        if reservation.confirmed_at is not None:
            raise ValueError(
                f"Reservation {reservation.reservation_id} was already accepted and is locked in, "
                f"so it can no longer be cancelled"
            )

        if reservation.status not in ACTIVE_STATUSES:
            raise ValueError(f"Reservation {reservation.reservation_id} cannot be cancelled because it is not active")

        reservation.status = ReservationStatus.CANCELLED
        reservation.cancelled_at = datetime.now()
        return self.reservation_repo.create(reservation)

    def confirm(self, reservation: Reservation, student: User) -> Reservation:
        """Student accepts an approved reservation, locking it in (workflow1/2).

        Status stays APPROVED — ``confirmed_at`` is the marker that makes the
        approval final, per the ERD ("approval not final until confirmed").
        """
        if reservation.user_id != student.user_id:
            raise ValueError(
                f"Student {student.user_id} cannot accept reservation {reservation.reservation_id} "
                f"because they are not the owner"
            )

        if reservation.status != ReservationStatus.APPROVED:
            raise ValueError(
                f"Reservation {reservation.reservation_id} cannot be accepted because it is not approved"
            )

        if reservation.confirmed_at is not None:
            raise ValueError(f"Reservation {reservation.reservation_id} was already accepted")

        reservation.confirmed_at = datetime.now()
        updated = self.reservation_repo.create(reservation)

        listing = self.listing_repo.get_by_id(reservation.listing_id)
        if listing is not None:
            self._notify(
                user_id=listing.host_id,
                reservation_id=reservation.reservation_id,
                message=f"{student.username} accepted their approved reservation for "
                        f"listing {reservation.listing_id} — it's locked in.",
            )
        return updated

    def approve(self, reservation: Reservation, host: User) -> Reservation:
        """Host approves a pending reservation (workflow2.png)."""
        self._require_host_action(reservation, host, "approve")

        reservation.status = ReservationStatus.APPROVED
        updated = self.reservation_repo.create(reservation)
        self._notify(
            user_id=reservation.user_id,
            reservation_id=reservation.reservation_id,
            message=f"Your reservation for listing {reservation.listing_id} was approved! "
                    f"Accept it from the listing page to lock it in.",
        )
        return updated

    def reject(self, reservation: Reservation, host: User) -> Reservation:
        """Host rejects a pending reservation (workflow2.png)."""
        self._require_host_action(reservation, host, "reject")

        reservation.status = ReservationStatus.REJECTED
        updated = self.reservation_repo.create(reservation)
        self._notify(
            user_id=reservation.user_id,
            reservation_id=reservation.reservation_id,
            message=f"Your reservation for listing {reservation.listing_id} was rejected. You are free to reserve elsewhere.",
        )
        return updated

    def _require_host_action(self, reservation: Reservation, host: User, action: str) -> None:
        """Only the listing's host may act, and only on pending reservations."""
        listing = self.listing_repo.get_by_id(reservation.listing_id)
        if listing is None:
            raise ValueError(f"Listing {reservation.listing_id} not found")

        if listing.host_id != host.user_id:
            raise ValueError(
                f"Host {host.user_id} cannot {action} reservation {reservation.reservation_id} "
                f"because they do not own listing {listing.listing_id}"
            )

        if reservation.status != ReservationStatus.PENDING:
            raise ValueError(
                f"Reservation {reservation.reservation_id} cannot be {action}ed because it is not pending"
            )

    def _notify(self, user_id: int, reservation_id: Optional[int], message: str) -> None:
        if self.notification_repo is None:
            return
        self.notification_repo.create(
            Notification(user_id=user_id, reservation_id=reservation_id, message=message)
        )