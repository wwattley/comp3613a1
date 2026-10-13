from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request, status, Form
from app.dependencies import SessionDep
from app.models.user import HOST_ACCOUNT_STATUS
from . import router, templates
from app.services.auth_service import AuthService
from app.repositories.user import UserRepository
from app.utilities.flash import flash
from app.utilities.security import access_token_cookie_kwargs


@router.get("/login", response_class=HTMLResponse)
async def login_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
    )


@router.post("/login", response_class=HTMLResponse)
async def login_action_ajax(
    db: SessionDep,
    request: Request,
    username: str = Form(),
    password: str = Form(),
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    access_token = auth_service.authenticate_user(username, password)
    if not access_token:
        flash(request, "Incorrect username or password", "danger")
        return RedirectResponse(
            url=request.url_for("login_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = user_repo.get_by_username(username)

    # Workflow 3: a host account must be approved before it can sign in.
    # Students and admins are unaffected (their status stays ACTIVE by default).
    if user is not None and user.role == "host" and user.status != HOST_ACCOUNT_STATUS.ACTIVE:
        if user.status == HOST_ACCOUNT_STATUS.REJECTED:
            flash(
                request,
                "Your host application was rejected. Contact support if you believe this is a mistake.",
                "danger",
            )
        else:
            flash(
                request,
                "Your host account is awaiting admin approval — you can sign in once it's approved.",
                "warning",
            )
        return RedirectResponse(
            url=request.url_for("login_view"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    dest = "admin_home_view" if user and user.role == "admin" else "user_home_view"
    response = RedirectResponse(
        url=request.url_for(dest),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        **access_token_cookie_kwargs(),
    )
    return response
