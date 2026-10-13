from sqlmodel import Session, select, func

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def for_user(self, user_id: int, limit: int = 20) -> list[Notification]:
        statement = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.notification_id.desc())
            .limit(limit)
        )
        return list(self.db.exec(statement).all())

    def unread_ids(self, user_id: int) -> set[int]:
        statement = (
            select(Notification.notification_id)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        )
        return set(self.db.exec(statement).all())

    def unread_count(self, user_id: int) -> int:
        statement = (
            select(func.count(Notification.notification_id))
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        )
        return self.db.exec(statement).one()

    def mark_read(self, notification_id: int, user_id: int) -> None:
        notification = self.db.get(Notification, notification_id)
        if notification is not None and notification.user_id == user_id:
            notification.is_read = True
            self.db.add(notification)
            self.db.commit()

    def mark_all_read(self, user_id: int) -> None:
        for notification in self.for_user(user_id, limit=1000):
            if not notification.is_read:
                notification.is_read = True
                self.db.add(notification)
        self.db.commit()
