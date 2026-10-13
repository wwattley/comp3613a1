from fastapi import HTTPException
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.listing import ListingRepository
from app.repositories.review import ReviewRepository
from app.repositories.user import UserRepository
from app.services.listing_service import ListingService
from . import router, templates


@router.get("/listings/{listing_id}", response_class=HTMLResponse, name="listing_details_view")
async def listing_details_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    listing_id: int,
):
    listing_repository = ListingRepository(db)
    user_repository = UserRepository(db)
    service = ListingService(
        listing_repository,
        user_repository,
        ReviewRepository(db),
    )

    details = service.details(listing_id=listing_id, viewer = user)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")

    return templates.TemplateResponse(
        request=request,
        name="listing_details.html",
        context={
            "details": details,
            "user": user,
        }
    )