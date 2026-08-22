from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.routes.auth import get_current_user



router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/",
    response_model=list[NotificationResponse],
)
def get_notifications(
    db: Session = Depends(get_db),
):
    notifications = db.scalars(
        select(Notification)
        .order_by(Notification.id.desc())
        .limit(50)
    ).all()

    return notifications


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
):
    notification = db.get(
        Notification,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


@router.patch(
    "/read-all",
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
):
    notifications = db.scalars(
        select(Notification).where(
            Notification.is_read.is_(False)
        )
    ).all()

    for notification in notifications:
        notification.is_read = True

    db.commit()

    return {
        "message": "All notifications marked as read",
    }

@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
):
    notification = db.get(
        Notification,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    db.delete(notification)
    db.commit()

    return None


@router.delete(
    "/",
)
def delete_all_notifications(
    db: Session = Depends(get_db),
):
    notifications = db.scalars(
        select(Notification)
    ).all()

    for notification in notifications:
        db.delete(notification)

    db.commit()

    return {
        "message": "All notifications cleared",
    }