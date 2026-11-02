from typing import Optional

from valutatrade_hub.core.models import User, Portfolio


class Session:
    current_user: Optional[User] = None
    current_portfolio: Optional[Portfolio] = None

    @classmethod
    def reset(cls) -> None:
        cls.current_user = None
        cls.current_portfolio = None

    @classmethod
    def logout(cls):
        cls.current_user = None
        cls.current_portfolio = None


