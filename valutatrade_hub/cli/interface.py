import argparse
import shlex
import sys
from typing import List, Optional

from valutatrade_hub.core import usecase as usecases
from valutatrade_hub.core.currencies import list_supported_codes
from valutatrade_hub.core.utils.exceptions import (
    RegisterError, LoginError, PortfolioError, BuyError, SellError, RateError,
    InsufficientFundsError, CurrencyNotFoundError, ApiRequestError,
)
from valutatrade_hub.core.session import Session


def _fmt_money(v: float) -> str:
    return f"{v:,.2f}"


def _fmt_amount(v: float) -> str:
    return f"{v:.4f}"


def cmd_register(args: argparse.Namespace) -> int:
    try:
        user = usecases.register(args.username, args.password)
        print(f"Пользователь '{user.username}' зарегистрирован (id={user.user_id})")
        return 0
    except RegisterError as e:
        print(f"Ошибка: {e}")
        return 1


def cmd_login(args: argparse.Namespace) -> int:
    try:
        user = usecases.login(args.username, args.password)
        print(f"Вы вошли как '{user.username}'")
        return 0
    except LoginError as e:
        print(f"Ошибка: {e}")
        return 1


def cmd_show_portfolio(args: argparse.Namespace) -> int:
    try:
        result = usecases.show_portfolio(args.base or "USD")
    except PortfolioError as e:
        print(f"Ошибка: {e}")
        return 1

    print(f"Портфель пользователя '{result['username']}' (база: {result['base']}):")
    if not result["wallets"]:
        print("  (кошельков нет)")
        print("-" * 33)
        print(f"ИТОГО: 0.00 {result['base']}")
        return 0
    for w in result["wallets"]:
        value = w["value_in_base"]
        value_str = _fmt_money(value) if value is not None else "—"
        print(f"- {w['currency']}: {_fmt_amount(w['balance'])}  "
              f"→ {value_str} {result['base']}")
    print("-" * 33)
    print(f"ИТОГО: {_fmt_money(result['total'])} {result['base']}")
    return 0


def cmd_buy(args: argparse.Namespace) -> int:
    try:
        amount = float(args.amount)
    except (TypeError, ValueError):
        print("Ошибка: 'amount' должен быть положительным числом")
        return 1
    try:
        result = usecases.buy(args.currency, amount)
    except BuyError as e:
        print(f"Ошибка: {e}")
        return 1
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}")
        print(f"Поддерживаемые коды: {', '.join(list_supported_codes())}")
        return 1

    print(f"Покупка выполнена: {_fmt_amount(result['amount'])} "
          f"{result['currency']} по курсу {_fmt_money(result['rate'])} USD/{result['currency']}")
    print("Изменения в портфеле:")
    print(f"- {result['currency']}: было {_fmt_amount(result['old_balance'])} "
          f"→ стало {_fmt_amount(result['new_balance'])}")
    print(f"Оценочная стоимость покупки: {_fmt_money(result['cost_usd'])} USD")
    return 0


def cmd_sell(args: argparse.Namespace) -> int:
    try:
        amount = float(args.amount)
    except (TypeError, ValueError):
        print("Ошибка: 'amount' должен быть положительным числом")
        return 1
    try:
        result = usecases.sell(args.currency, amount)
    except (SellError, InsufficientFundsError, CurrencyNotFoundError) as e:
        print(f"Ошибка: {e}")
        return 1

    print(f"Продажа выполнена: {_fmt_amount(result['amount'])} "
          f"{result['currency']} по курсу {_fmt_money(result['rate'])} USD/{result['currency']}")
    print("Изменения в портфеле:")
    print(f"- {result['currency']}: было {_fmt_amount(result['old_balance'])} "
          f"→ стало {_fmt_amount(result['new_balance'])}")
    print(f"Оценочная выручка: {_fmt_money(result['proceeds_usd'])} USD")
    return 0


def cmd_get_rate(args: argparse.Namespace) -> int:
    try:
        result = usecases.get_rate_info(args.from_code, args.to_code)
    except RateError as e:
        print(f"Ошибка: {e}")
        return 1
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}")
        print("Воспользуйтесь help get-rate или проверьте поддерживаемые коды.")
        return 1
    except ApiRequestError as e:
        print(f"Ошибка: {e}")
        print("Повторите попытку позже или проверьте подключение к сети.")
        return 1

    updated = result["updated_at"].replace("T", " ") if result["updated_at"] else "—"
    print(f"Курс {result['from']}→{result['to']}: {result['rate']:.8f} "
          f"(обновлено: {updated})")
    if result["reverse_rate"] is not None:
        print(f"Обратный курс {result['to']}→{result['from']}: "
              f"{result['reverse_rate']:.8f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wallet-cli", description="CLI для управления портфелем"
    )
    sub = parser.add_subparsers(dest="command", required=False)

    p = sub.add_parser("register", help="Регистрация")
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("login", help="Вход")
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("show-portfolio", help="Портфель")
    p.add_argument("--base", default="USD")
    p.set_defaults(func=cmd_show_portfolio)

    p = sub.add_parser("buy", help="Купить")
    p.add_argument("--currency", required=True)
    p.add_argument("--amount", required=True)
    p.set_defaults(func=cmd_buy)

    p = sub.add_parser("sell", help="Продать")
    p.add_argument("--currency", required=True)
    p.add_argument("--amount", required=True)
    p.set_defaults(func=cmd_sell)

    p = sub.add_parser("get-rate", help="Курс")
    p.add_argument("--from", dest="from_code", required=True)
    p.add_argument("--to", dest="to_code", required=True)
    p.set_defaults(func=cmd_get_rate)

    return parser


def interactive() -> None:
    print("Интерактивный режим. 'help' — команды, 'exit' — выход.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        if line.lower() == "help":
            print("Команды: register, login, logout, show-portfolio, buy, sell, get-rate, exit")
            continue
        if line.lower() == "logout":
            Session.logout()
            print("Вы вышли из системы.")
            continue

        try:
            argv = shlex.split(line)
        except ValueError as e:
            print(f"Ошибка разбора: {e}")
            continue

        try:
            parser = build_parser()
            args = parser.parse_args(argv)
            if args.command:
                args.func(args)
        except SystemExit:
            pass
        except Exception as e:
            print(f"Ошибка: {e}")


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        interactive()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(run())