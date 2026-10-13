from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.listing import ListingRepository
from app.services.listing_service import ListingService
from . import router, templates


@router.get("/explore", response_class=HTMLResponse, name="explore_view")
async def explore_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    location: Optional[str] = None,
    capacity: Optional[str] = None,
):  
    location_filter = location if location else None
    capacity_filter = int(capacity) if capacity else None

    repository = ListingRepository(db)
    service = ListingService(repository)

    return templates.TemplateResponse(
        request=request,
        name="explore.html",
        context={
            "sections": service.cards(location=location_filter, capacity=capacity_filter),
            "locations": service.known_locations(),
            "location": location_filter,
            "capacity": capacity_filter,
            "user": user,
        }
    )
