from sqlalchemy import select

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.user import User


USERS = [
    {
        "user_id": "Gourav_yadav",
        "password": "Gouravy@77",
        "name": "Gourav Yadav",
    },
    {
        "user_id": "Ishwar_yadav",
        "password": "ishyb@77",
        "name": "Ishwar Yadav",
    },
    {
        "user_id": "Monu_yadav",
        "password": "Monuydv#00",
        "name": "Monu Yadav",
    },
    {
        "user_id": "Deepak_yadav",
        "password": "Deepy#11",
        "name": "Deepak Yadav",
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