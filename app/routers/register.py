from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request, status, File, Form, HTTPException, UploadFile
from app.dependencies import SessionDep
from app.schemas.auth import SignupRequest
from app.services.auth_service import AuthService
from app.repositories.user import UserRepository
from app.utilities.flash import flash
from . import router, templates

# Workflow 3 signup rules: face photo PNG/JPEG, credentials PDF, each ≤ 10 MB
# (mirrors workflow 2's proof-of-enrollment rules).
ALLOWED_FACE_TYPES = {"image/png", "image/jpeg"}
ALLOWED_CREDENTIAL_TYPES = {"application/pdf"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


# View route (loads the page)
@router.get("/register", response_class=HTMLResponse)
async def register_view(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="register.html",
    )

# Action route (performs an action)
@router.post('/register', response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def signup_user(request:Request, db:SessionDep, 
    username: str = Form(),
    email: str = Form(),
    password: str = Form(),
    phone: str | None = Form(None),
    university: str | None = Form(None),
    role: str = Form("regular_user"),
    face: UploadFile | None = File(None),
    credentials: UploadFile | None = File(None),
):
    # Never trust the posted role: anything but "host" registers a student.
    role = "host" if role == "host" else "regular_user"
    back = request.url_for("register_view")

    # Request-shape checks for host applicants; the PENDING status is applied
    # in the service (thin route — no SQL here).
    face_upload = credentials_upload = None
    if role == "host":
        if face is None or credentials is None:
            flash(request, "Host applications need both a face photo and a credentials PDF.", "danger")
            return RedirectResponse(url=back, status_code=status.HTTP_303_SEE_OTHER)
        if face.content_type not in ALLOWED_FACE_TYPES:
            flash(request, "Face photo must be a PNG or JPEG file.", "danger")
            return RedirectResponse(url=back, status_code=status.HTTP_303_SEE_OTHER)
        if credentials.content_type not in ALLOWED_CREDENTIAL_TYPES:
            flash(request, "Credentials must be a PDF file.", "danger")
            return RedirectResponse(url=back, status_code=status.HTTP_303_SEE_OTHER)

        face_data = await face.read()
        credentials_data = await credentials.read()
        if len(face_data) > MAX_UPLOAD_BYTES or len(credentials_data) > MAX_UPLOAD_BYTES:
            flash(request, "Uploads must be no greater than 10 MB each.", "danger")
            return RedirectResponse(url=back, status_code=status.HTTP_303_SEE_OTHER)

        face_upload = (face.filename, face.content_type, face_data)
        credentials_upload = (credentials.filename, credentials.content_type, credentials_data)

    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    try:
        user = auth_service.register_user(
            username,
            email,
            password,
            phone,
            university,
            role=role,
            face_filename=face_upload[0] if face_upload else None,
            face_content_type=face_upload[1] if face_upload else None,
            face_data=face_upload[2] if face_upload else None,
            credentials_filename=credentials_upload[0] if credentials_upload else None,
            credentials_content_type=credentials_upload[1] if credentials_upload else None,
            credentials_data=credentials_upload[2] if credentials_upload else None,
        )
        if role == "host":
            flash(request, "Application submitted! An admin will review it — you can sign in once approved.")
        else:
            flash(request, "Registration completed! Sign in now!")
        return RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        flash(request, "Username or email already exists", "danger")
        return RedirectResponse(url=request.url_for("register_view"), status_code=status.HTTP_303_SEE_OTHER)
