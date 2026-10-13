from datetime import datetime

from app.models.user import HOST_ACCOUNT_STATUS
from app.repositories.user import UserRepository
from app.schemas.user import HostCreate, RegularUserCreate
from app.utilities.security import encrypt_password, verify_password, create_access_token
from typing import Optional


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(plaintext_password=password, encrypted_password=user.password):
            return None
        access_token = create_access_token(data={"sub": f"{user.user_id}", "role": user.role})
        return access_token

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        university: Optional[str] = None,
        role: str = "regular_user",
        face_filename: Optional[str] = None,
        face_content_type: Optional[str] = None,
        face_data: Optional[bytes] = None,
        credentials_filename: Optional[str] = None,
        credentials_content_type: Optional[str] = None,
        credentials_data: Optional[bytes] = None,
    ):
        encrypted = encrypt_password(password)
        if role == "host":
            # Workflow 3: host signups start PENDING — the one place PENDING is
            # assigned (the model default is ACTIVE so seeded users can log in).
            new_user = HostCreate(
                username=username,
                email=email,
                password=encrypted,
                phone=phone,
                university=university,
                status=HOST_ACCOUNT_STATUS.PENDING,
                applied_at=datetime.today(),
                face_filename=face_filename,
                face_content_type=face_content_type,
                face_data=face_data,
                credentials_filename=credentials_filename,
                credentials_content_type=credentials_content_type,
                credentials_data=credentials_data,
            )
        else:
            new_user = RegularUserCreate(
                username=username,
                email=email,
                password=encrypted,
                phone=phone,
                university=university,
            )
        return self.user_repo.create(new_user)
