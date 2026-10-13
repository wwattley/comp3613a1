from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi import status

from app.dependencies.auth import AuthDep
from . import router


@router.get("/app", response_class=RedirectResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
):
    """Student home lands on Explore — the wireframe's front door
    (workflow1.png: browse/search is where a student starts)."""
    return RedirectResponse(
        url=request.url_for("explore_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
