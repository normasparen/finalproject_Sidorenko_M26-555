import os

from valutatrade_hub.core.models.user import User

SESSION_FILE = ".session"


class Session:
    _current_user: User | None = None

    @classmethod
    def login(cls, user: User) -> None:
        cls._current_user = user
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                f.write(str(user.user_id))
        except OSError:
            pass

    @classmethod
    def get_current_user(cls) -> User | None:
        if cls._current_user is not None:
            return cls._current_user

        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, encoding="utf-8") as f:
                    uid = int(f.read().strip())
                from valutatrade_hub.infra.database import db
                for u in db.load_users():
                    if u["user_id"] == uid:
                        cls._current_user = User.from_dict(u)
                        return cls._current_user
            except (ValueError, OSError):
                pass
        return None

    @classmethod
    def logout(cls) -> None:
        cls._current_user = None
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except OSError:
                pass