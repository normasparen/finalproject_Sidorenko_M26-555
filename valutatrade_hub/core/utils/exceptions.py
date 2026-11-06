class BuyError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(self.detail)

class SellError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(self.detail)

class RegisterError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(self.detail)

class LoginError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(self.detail)

class RateError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(self.detail)

class PortfolioError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(self.detail)


class CurrencyNotFoundError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(self.detail)


class InsufficientFundsError(Exception):
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        super().__init__(f"Недостаточно средств:"
                         f" доступно {available} {code}, требуется {required} {code}")


class ApiRequestError(Exception):
    def __init__(self, error: str):
        super().__init__(f"Ошибка при обращении к API: {error}")