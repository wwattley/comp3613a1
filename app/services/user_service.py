from datetime import datetime
from typing import Optional

from app.models.notification import Notification
from app.models.user import HOST_ACCOUNT_STATUS, User
from app.repositories.notification import NotificationRepository
from app.repositories.user import UserRepository
from app.utilities.security import encrypt_password, verify_password, create_access_token
from app.schemas.user import RegularUserCreate

class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        notification_repo: Optional[NotificationRepository] = None,
    ):
        self.user_repo = user_repo
        self.notification_repo = notification_repo

    def get_all_users(self):
        return self.user_repo.get_all_users()

    def approve_host(self, applicant: User, admin: User) -> User:
        """Admin approves a pending host account (workflow3.png)."""
        self._require_admin_decision(applicant, admin, "approve")

        applicant.status = HOST_ACCOUNT_STATUS.ACTIVE
        applicant.approved_at = datetime.today()
        updated = self.user_repo.save(applicant)
        self._notify(
            user_id=applicant.user_id,
            message=f"Your host account was approved — welcome aboard, {applicant.username}!",
        )
        return updated

    def reject_host(self, applicant: User, admin: User) -> User:
        """Admin rejects a pending host account (workflow3.png)."""
        self._require_admin_decision(applicant, admin, "reject")

        applicant.status = HOST_ACCOUNT_STATUS.REJECTED
        applicant.rejected_at = datetime.today()
        # No bell notification on reject: a rejected applicant cannot sign in to see it.
        return self.user_repo.save(applicant)

    def _require_admin_decision(self, applicant: User, admin: User, action: str) -> None:
        """Only an admin may act, and only on pending host applications."""
        if admin.role != "admin":
            raise ValueError(f"User {admin.user_id} cannot {action} host accounts")

        if applicant.role != "host":
            raise ValueError(
                f"Account {applicant.username} cannot be {action}ed "
                f"because they did not apply to be a host"
            )

        if applicant.status != HOST_ACCOUNT_STATUS.PENDING:
            raise ValueError(
                f"Account {applicant.username} cannot be {action}ed "
                f"because their application is not pending"
            )

    def _notify(self, user_id: int, message: str) -> None:
        if self.notification_repo is None:
            return
        self.notification_repo.create(Notification(user_id=user_id, message=message))
