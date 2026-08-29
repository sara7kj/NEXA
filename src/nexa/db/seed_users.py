from sqlalchemy.orm import Session

from nexa.auth.permissions import Role
from nexa.auth.security import hash_password
from nexa.db.connection import engine
from nexa.db.models import User

USERS = [
    ("u-layla", "layla@falcon.example", "Layla Al-Harbi", Role.EMPLOYEE),
    ("u-omar", "omar@falcon.example", "Omar Nasser", Role.MANAGER),
    ("u-fahad", "fahad@falcon.example", "Fahad Al-Otaibi", Role.MANAGER),
    ("u-huda", "huda@falcon.example", "Huda Al-Qahtani", Role.DIRECTOR),
]

DEV_PASSWORD = "dev-password-123"


def seed_users() -> None:
    with Session(engine) as session:
        session.query(User).delete()
        for user_id, email, name, role in USERS:
            session.add(
                User(
                    id=user_id,
                    email=email,
                    password_hash=hash_password(DEV_PASSWORD),
                    full_name=name,
                    role=role.value,
                )
            )
        session.commit()

    print(f"seeded {len(USERS)} users (dev password: {DEV_PASSWORD})")


if __name__ == "__main__":
    seed_users()