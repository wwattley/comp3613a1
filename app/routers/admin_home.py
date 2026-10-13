from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep, IsUserLoggedIn, get_current_user, is_admin
from app.repositories.notification import NotificationRepository
from app.utilities.flash import flash
from . import router, templates

from app.services.user_service import UserService
from app.repositories.user import UserRepository

def _user_service(db) -> UserService:
    return UserService(UserRepository(db), NotificationRepository(db))

@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db:SessionDep
):
    return templates.TemplateResponse(
        request=request, 
        name="admin.html",
        context={
            "user": user,
            # Dashboard shows only undecided applicants (workflow3.png).
            "applicants": UserRepository(db).pending_hosts(),
        }
    )


@router.get("/admin/history", response_class=HTMLResponse, name="admin_history_view")
async def admin_history_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    """Read-only list of past host-account decisions (workflow3.png, History)."""
    return templates.TemplateResponse(
        request=request,
        name="admin_history.html",
        context={
            "user": user,
            "decided": UserRepository(db).decided_hosts(),
        }
    )


@router.get("/admin/applicants/{user_id}/face", name="admin_face_view")
async def admin_face_view(
    db: SessionDep,
    user: AdminDep,
    user_id: int,
):
    """Serve the applicant's face photo to the reviewing admin only."""
    applicant = UserRepository(db).get_by_id(user_id)
    if applicant is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if not applicant.face_data:
        raise HTTPException(status_code=404, detail="No face photo was uploaded")

    filename = applicant.face_filename or "face"
    return Response(
        content=applicant.face_data,
        media_type=applicant.face_content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/admin/applicants/{user_id}/credentials", name="admin_credentials_view")
async def admin_credentials_view(
    db: SessionDep,
    user: AdminDep,
    user_id: int,
):
    """Serve the applicant's credentials PDF to the reviewing admin only."""
    applicant = UserRepository(db).get_by_id(user_id)
    if applicant is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if not applicant.credentials_data:
        raise HTTPException(status_code=404, detail="No credentials file was uploaded")

    filename = applicant.credentials_filename or "credentials.pdf"
    return Response(
        content=applicant.credentials_data,
        media_type=applicant.credentials_content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

@router.post("/admin/{user_id}/approve", response_class=HTMLResponse)
async def approve_host_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    user_id: int
):
    user_repo = UserRepository(db)
    applicant = user_repo.get_by_id(user_id)
    if applicant is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        _user_service(db).approve_host(applicant, user)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, f"Host {applicant.username} approved. They can now log in.", "success")

    return RedirectResponse(
        url=request.url_for("admin_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/admin/{user_id}/reject", response_class=HTMLResponse)
async def reject_host_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    user_id: int
):
    user_repo = UserRepository(db)
    applicant = user_repo.get_by_id(user_id)
    if applicant is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        _user_service(db).reject_host(applicant, user)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, f"Host {applicant.username} rejected successfully.", "success")

    return RedirectResponse(
        url=request.url_for("admin_home_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
