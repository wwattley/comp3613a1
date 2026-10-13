from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.dependencies.auth import AuthDep, HostDep
from app.dependencies.session import SessionDep
from app.models.reservation import ReservationStatus
from app.repositories.listing import ListingRepository
from app.repositories.notification import NotificationRepository
from app.repositories.reservation import ReservationRepository
from app.repositories.user import UserRepository
from app.services.listing_service import ListingService
from app.services.reservation_service import ReservationService
from app.utilities.flash import flash
from . import router, templates

# Wireframe rules (workflow1.png): PNG / JPEG / PDF, no greater than 10 MB.
ALLOWED_PROOF_TYPES = {"image/png", "image/jpeg", "application/pdf"}
MAX_PROOF_BYTES = 10 * 1024 * 1024


def _reservation_service(db) -> ReservationService:
    return ReservationService(
        ReservationRepository(db),
        ListingRepository(db),
        NotificationRepository(db),
    )


@router.get("/listings/{listing_id}/reserve", response_class=HTMLResponse, name="reservation_form_view")
async def reservation_form_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    listing_id: int,
):
    """Reservation Form screen (workflow1.png, bottom-middle)."""
    service = ListingService(ListingRepository(db), UserRepository(db))
    details = service.details(listing_id=listing_id, viewer=user)
    if details is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Hosts view details only — the form is for students (workflow2 role split).
    if not details.can_reserve:
        flash(request, "Hosts can't reserve listings — browse and review instead.", "warning")
        return RedirectResponse(
            url=request.url_for("listing_details_view", listing_id=listing_id),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request=request,
        name="reservation_form.html",
        context={"details": details, "user": user},
    )


@router.post("/listings/{listing_id}/reserve", response_class=HTMLResponse, name="reservation_submit_view")
async def reservation_submit_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    listing_id: int,
    proof: UploadFile = File(...),
):
    """Submit action — creates the pending Reservation (thin route).

    Request-shape checks (file type / size) live here; the domain rules
    (full unit, duplicate active reservation) live in the service.
    """
    back = request.url_for("reservation_form_view", listing_id=listing_id)

    if proof.content_type not in ALLOWED_PROOF_TYPES:
        flash(request, "Proof of enrollment must be a PNG, JPEG or PDF file.", "danger")
        return RedirectResponse(url=back, status_code=status.HTTP_303_SEE_OTHER)

    data = await proof.read()
    if len(data) > MAX_PROOF_BYTES:
        flash(request, "Proof of enrollment must be no greater than 10 MB.", "danger")
        return RedirectResponse(url=back, status_code=status.HTTP_303_SEE_OTHER)

    try:
        _reservation_service(db).reserve(
            listing_id=listing_id,
            student=user,
            proof_filename=proof.filename,
            proof_content_type=proof.content_type,
            proof_data=data,
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
        return RedirectResponse(url=back, status_code=status.HTTP_303_SEE_OTHER)

    flash(request, "Reservation submitted — pending host approval.", "success")
    return RedirectResponse(
        url=request.url_for("listing_details_view", listing_id=listing_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/reservations/{reservation_id}/cancel", response_class=HTMLResponse, name="reservation_cancel_view")
async def reservation_cancel_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    reservation_id: int,
):
    """Cancel action — frees the slot (thin route)."""
    reservation_repo = ReservationRepository(db)
    reservation = reservation_repo.get_by_id(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    try:
        _reservation_service(db).cancel(reservation, user)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, "Reservation cancelled — the slot is free again.", "success")

    return RedirectResponse(
        url=request.url_for("listing_details_view", listing_id=reservation.listing_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/reservations/{reservation_id}/approve", response_class=HTMLResponse, name="reservation_approve_view")
async def reservation_approve_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    reservation_id: int,
):
    """Approve action — marks the reservation as approved (thin route)."""
    reservation_repo = ReservationRepository(db)
    reservation = reservation_repo.get_by_id(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    try:
        _reservation_service(db).approve(reservation, user)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, "Reservation approved — the student will be notified.", "success")

    return RedirectResponse(
        url=request.url_for("host_approvals_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/reservations/{reservation_id}/reject", response_class=HTMLResponse, name="reservation_reject_view")
async def reservation_reject_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    reservation_id: int,
):
    """Reject action — marks the reservation as rejected (thin route)."""
    reservation_repo = ReservationRepository(db)
    reservation = reservation_repo.get_by_id(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    try:
        _reservation_service(db).reject(reservation, user)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, "Reservation rejected — the student will be notified.", "success")

    return RedirectResponse(
        url=request.url_for("host_approvals_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/reservations/{reservation_id}/confirm", response_class=HTMLResponse, name="reservation_confirm_view")
async def reservation_confirm_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    reservation_id: int,
):
    """Accept action — the student locks in an approved reservation (thin route)."""
    reservation_repo = ReservationRepository(db)
    reservation = reservation_repo.get_by_id(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    try:
        _reservation_service(db).confirm(reservation, user)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, "Reservation accepted — it's locked in.", "success")

    return RedirectResponse(
        url=request.url_for("listing_details_view", listing_id=reservation.listing_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/host/approvals", response_class=HTMLResponse, name="host_approvals_view")
async def host_approvals_view(
    request: Request,
    db: SessionDep,
    user: HostDep,
):
    """Pending Reservation Approvals screen (workflow2.png, host dashboard)."""
    reservations = ReservationRepository(db).for_host(
        user.user_id, status=ReservationStatus.PENDING
    )
    notifications = NotificationRepository(db).for_user(user.user_id, limit=15)
    return templates.TemplateResponse(
        request=request,
        name="host_approvals.html",
        context={"user": user, "approvals": reservations, "notifications": notifications},
    )


@router.get("/reservations/{reservation_id}/proof", name="reservation_proof_view")
async def reservation_proof_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    reservation_id: int,
):
    """Serve the stored proof-of-enrollment file (workflow2.png: 'Host Redirected to file').

    Only the student who uploaded it or the listing's host may open it.
    """
    reservation = ReservationRepository(db).get_by_id(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    listing = ListingRepository(db).get_by_id(reservation.listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    is_owner = reservation.user_id == user.user_id
    is_host = listing.host_id == user.user_id
    if not (is_owner or is_host):
        raise HTTPException(
            status_code=401,
            detail="You are not authorized to view this file",
        )

    if not reservation.proof_data:
        raise HTTPException(status_code=404, detail="No proof of enrollment was uploaded")

    filename = reservation.proof_filename or "proof"
    return Response(
        content=reservation.proof_data,
        media_type=reservation.proof_content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
