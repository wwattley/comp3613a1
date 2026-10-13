from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.models.listing import Listing
from app.models.listing_image import ListingImage
from app.models.reservation import Reservation, ReservationStatus, ACTIVE_STATUSES
from app.models.review import Review
from app.models.user import User
from app.repositories.listing import ListingRepository
from app.repositories.review import ReviewRepository
from app.repositories.user import UserRepository


@dataclass
class ReviewCard:
    """View shape for one review on the listing details screen."""

    comment: str
    author: str
    created_at: datetime

    @classmethod
    def from_row(cls, review: Review, author: User) -> "ReviewCard":
        return cls(
            comment=review.comment or "",
            author=author.username,
            created_at=review.created_at,
        )


@dataclass
class ListingCard:
    """View shape for an explore card (wireframe: image, name, location, rent)."""

    listing_id: int
    title: str
    location: str
    monthly_rent: str
    description: str
    capacity: int
    images: list[ListingImage] = field(default_factory=list)

    @classmethod
    def from_listing(cls, listing: Listing, images: list[ListingImage]) -> "ListingCard":
        return cls(
            listing_id=listing.listing_id,
            title=listing.title,
            location=listing.location,
            monthly_rent=f"{listing.monthly_rent:.2f}",
            description=listing.description,
            capacity=listing.capacity,
            images=images,
        )


@dataclass
class ListingDetails:
    """View shape for the listing details screen (workflow1.png bottom row)."""

    listing: Listing
    images: list[ListingImage]
    host: Optional[User]
    monthly_rent: str
    slots_taken: int
    capacity: int
    is_full: bool
    viewer_reservation: Optional[Reservation]
    can_reserve: bool
    reviews: list[ReviewCard] = field(default_factory=list)

    @property
    def reservation_label(self) -> Optional[str]:
        """Badge text for the viewer's active reservation.

        Driven by the row's real status rather than a fixed string: PENDING
        reads as awaiting the host, APPROVED flips to 'Reserved — Approved'
        and becomes 'Confirmed' once the student accepts.
        """
        if self.viewer_reservation is None:
            return None
        if self.viewer_reservation.status == ReservationStatus.APPROVED:
            if self.viewer_reservation.confirmed_at:
                return "Reserved — Confirmed"
            return "Reserved — Approved"
        return "Reserved — Pending Approval"

    @property
    def reservation_tone(self) -> Optional[str]:
        """Bootstrap badge class matching ``reservation_label``."""
        if self.viewer_reservation is None:
            return None
        if self.viewer_reservation.status == ReservationStatus.APPROVED:
            return "text-bg-success"
        return "text-bg-warning"

    @property
    def can_accept_reservation(self) -> bool:
        """Show Accept only while an approval is still unconfirmed."""
        reservation = self.viewer_reservation
        return (
            reservation is not None
            and reservation.status == ReservationStatus.APPROVED
            and reservation.confirmed_at is None
        )

    @property
    def can_cancel_reservation(self) -> bool:
        """Cancel stays available until the student accepts — accepting locks it in."""
        reservation = self.viewer_reservation
        return reservation is not None and reservation.confirmed_at is None

    @property
    def review_count(self) -> int:
        return len(self.reviews)


class ListingService:
    def __init__(
        self,
        listing_repo: ListingRepository,
        user_repo: Optional[UserRepository] = None,
        review_repo: Optional[ReviewRepository] = None,
    ):
        self.listing_repo = listing_repo
        self.user_repo = user_repo
        self.review_repo = review_repo

    # —— Browse/Search Listings (workflow 1, part 1) ——

    def browse(
        self,
        location: Optional[str] = None,
        capacity: Optional[int] = None,
    ) -> list[Listing]:
        """Application layer for Browse/Search Listings: filters the
        repository by location / capacity."""
        return self.listing_repo.search(location=location, capacity=capacity)

    def known_locations(self) -> list[str]:
        """Distinct locations, for the explore filter dropdown."""
        return sorted({listing.location for listing in self.listing_repo.search()})

    def cards(
        self,
        location: Optional[str] = None,
        capacity: Optional[int] = None,
    ) -> list[tuple[str, list[ListingCard]]]:
        """Cards grouped by location — one 'Units in <location>' section each."""
        listings = self.browse(location=location, capacity=capacity)
        images = self.listing_repo.images_for([listing.listing_id for listing in listings])

        grouped: dict[str, list[ListingCard]] = {}
        for listing in listings:
            grouped.setdefault(listing.location, []).append(
                ListingCard.from_listing(listing, images.get(listing.listing_id, []))
            )
        return sorted(grouped.items())

    # —— View Listing Details (workflow 1, part 2) ——

    def details(self, listing_id: int, viewer: User) -> Optional[ListingDetails]:
        """Load one listing for the details screen, with the availability
        rule applied (Phase 3: a slot is held while pending or approved;
        the unit reads as full when active reservations reach capacity)."""
        listing = self.listing_repo.get_by_id(listing_id)
        if listing is None:
            return None

        images = self.listing_repo.images_for([listing_id]).get(listing_id, [])
        slots_taken = self.listing_repo.active_reservation_count(listing_id)

        host = None
        if self.user_repo is not None:
            host = self.user_repo.get_by_id(listing.host_id)

        latest = self.listing_repo.viewer_reservation(listing_id, viewer.user_id)
        active_reservation = (
            latest if latest is not None and latest.status in ACTIVE_STATUSES else None
        )

        # Reviews are only ever read, never written here — the demo seeds them.
        reviews: list[ReviewCard] = []
        if self.review_repo is not None:
            reviews = [
                ReviewCard.from_row(review, author)
                for review, author in self.review_repo.for_listing(listing_id)
            ]

        return ListingDetails(
            listing=listing,
            images=images,
            host=host,
            monthly_rent=f"{listing.monthly_rent:.2f}",
            slots_taken=slots_taken,
            capacity=listing.capacity,
            is_full=slots_taken >= listing.capacity,
            viewer_reservation=active_reservation,
            # A host browses and views details, but never reserves (workflow2 role split).
            can_reserve=viewer.role != "host",
            reviews=reviews,
        )
