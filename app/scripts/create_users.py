from sqlalchemy import select

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.user import User


USERS = [
    {
        "user_id": "122A8007",
        "password": "Mahi@123",
        "name": "Aditya(dev)",
    },
    {
        "user_id": "122A8026",
        "password": "Mahi@123",
        "name": "Harshal(dev)",
    },
    {
        "user_id": "122A8003",
        "password": "Mahi@123",
        "name": "Sanket(dev)",
    },
    {
        "user_id": "OWN2601",
        "password": "ChangeMe123!",
        "name": "User1",
    },
    {
        "user_id": "OWN2602",
        "password": "ChangeMe123!",
        "name": "User2",
    },
]


def create_users():
    db = SessionLocal()

    try:
        for user_data in USERS:

            existing_user = db.scalar(
                select(User).where(
                    User.user_id == user_data["user_id"]
                )
            )

            if existing_user:
                print(
                    f"{user_data['user_id']} already exists"
                )
                continue

            user = User(
                user_id=user_data["user_id"],
                password_hash=hash_password(
                    user_data["password"]
                ),
                name=user_data["name"],
                is_active=True,
            )

            db.add(user)

        db.commit()

        print("Users created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    create_users()