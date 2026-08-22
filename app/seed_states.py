from sqlalchemy import select

from app.database import SessionLocal
from app.models.state import State


INDIAN_STATES_AND_UTS = [
    ("Jammu and Kashmir", "01"),
    ("Himachal Pradesh", "02"),
    ("Punjab", "03"),
    ("Chandigarh", "04"),
    ("Uttarakhand", "05"),
    ("Haryana", "06"),
    ("Delhi", "07"),
    ("Rajasthan", "08"),
    ("Uttar Pradesh", "09"),
    ("Bihar", "10"),
    ("Sikkim", "11"),
    ("Arunachal Pradesh", "12"),
    ("Nagaland", "13"),
    ("Manipur", "14"),
    ("Mizoram", "15"),
    ("Tripura", "16"),
    ("Meghalaya", "17"),
    ("Assam", "18"),
    ("West Bengal", "19"),
    ("Jharkhand", "20"),
    ("Odisha", "21"),
    ("Chhattisgarh", "22"),
    ("Madhya Pradesh", "23"),
    ("Gujarat", "24"),
    ("Daman and Diu", "25"),
    ("Dadra and Nagar Haveli and Daman and Diu", "26"),
    ("Maharashtra", "27"),
    ("Andhra Pradesh", "28"),
    ("Karnataka", "29"),
    ("Goa", "30"),
    ("Lakshadweep", "31"),
    ("Kerala", "32"),
    ("Tamil Nadu", "33"),
    ("Puducherry", "34"),
    ("Andaman and Nicobar Islands", "35"),
    ("Telangana", "36"),
    ("Andhra Pradesh (New)", "37"),
    ("Ladakh", "38"),
]


def seed_states():
    db = SessionLocal()

    try:
        for name, code in INDIAN_STATES_AND_UTS:
            existing_state = db.scalar(
                select(State).where(State.code == code)
            )

            if existing_state is None:
                db.add(
                    State(
                        name=name,
                        code=code,
                    )
                )

        db.commit()
        print("States seeded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_states()