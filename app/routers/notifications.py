from fastapi import HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.notification import NotificationRepository
from . import router, templates


@router.get("/notifications/bell", response_class=HTMLResponse, name="notifications_bell_view")
async def notifications_bell_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    open: bool = Query(False),
):
    """Navbar bell fragment — loaded by htmx (workflow2.png: student notification bar).

    Read-ness is inferred by excluding unread_ids from the full list: NOTIFICATION
    has no read_at column, so "not unread" == read.

    ``open`` toggles the panel: the bell button hrefs ``?open=1`` while closed and
    the bare route while open. read-all passes it directly so the panel the student
    is looking at stays put.
    """
    repo = NotificationRepository(db)
    notifications = repo.for_user(user.user_id, limit=8)
    unread_ids = repo.unread_ids(user.user_id)
    return templates.TemplateResponse(
        request=request,
        name="notifications_bell.html",
        context={
            "user": user,
            "notifications": notifications,
            "unread_ids": unread_ids,
            "unread": repo.unread_count(user.user_id),
            "total": len(notifications),
            "open": open,
        },
    )


@router.post("/notifications/read-all", response_class=HTMLResponse, name="notifications_read_all_view")
async def notifications_read_all_view(
    request: Request,
    db: SessionDep,
    user: AuthDep,
    keep_open: bool = Query(False),
):
    """Mark everything read and return the refreshed bell (thin route).

    ``keep_open`` preserves the panel the student is looking at: htmx swaps this
    fragment in place, so returning the closed bell would collapse the dropdown
    the moment "Mark all as read" is pressed.
    """
    NotificationRepository(db).mark_all_read(user.user_id)
    return await notifications_bell_view(request, db, user, open=keep_open)
