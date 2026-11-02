

import argparse
import shlex
import sys
from typing import List, Optional

import valutatrade_hub.core.usecase as usecases
from valutatrade_hub.core.session import Session

from valutatrade_hub.core.utils.exceptions import (
    RegisterError, LoginError, PortfolioError,
    BuyError, SellError, RateError,
)


def _fmt_money(v: float) -> str:
    return f"{v:,.2f}"


def _fmt_amount(v: float) -> str:
    return f"{v:.4f}"


def cmd_register(args: argparse.Namespace) -> int:
    try:
        user = usecases.register(args.username, args.password)
        print(f"Пользователь '{user.username}' зарегистрирован "
              f"(id={user.user_id})")
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

    print(f"Портфель пользователя '{result['username']}' "
          f"(база: {result['base']}):")
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
        # print(args.amount)
        amount = float(args.amount)
        print(type(amount), amount)
    except (TypeError, ValueError):
        print("Ошибка: 'amount' должен быть положительным числом")
        return 1

    try:
        result = usecases.buy(args.currency, amount)
    except BuyError as e:
        print(f"Ошибка: {e}")
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
    except SellError as e:
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

    updated = result["updated_at"].replace("T", " ") if result["updated_at"] else "—"
    print(f"Курс {result['from']}→{result['to']}: {result['rate']:.8f} "
          f"(обновлено: {updated})")
    if result["reverse_rate"] is not None:
        print(f"Обратный курс {result['to']}→{result['from']}: "
              f"{result['reverse_rate']:.8f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wallet-cli",
        description="CLI для управления портфелем",
    )

    sub = parser.add_subparsers(dest="command", required=False)

    p_reg = sub.add_parser("register", help="Регистрация пользователя")
    p_reg.add_argument("--username", required=True)
    p_reg.add_argument("--password", required=True)
    p_reg.set_defaults(func=cmd_register)

    p_login = sub.add_parser("login", help="Вход в систему")
    p_login.add_argument("--username", required=True)
    p_login.add_argument("--password", required=True)
    p_login.set_defaults(func=cmd_login)

    p_show = sub.add_parser("show-portfolio", help="Показать портфель")
    p_show.add_argument("--base", default="USD")
    p_show.set_defaults(func=cmd_show_portfolio)

    p_buy = sub.add_parser("buy", help="Купить валюту")
    p_buy.add_argument("--currency", required=True)
    p_buy.add_argument("--amount", required=True)
    p_buy.set_defaults(func=cmd_buy)

    p_sell = sub.add_parser("sell", help="Продать валюту")
    p_sell.add_argument("--currency", required=True)
    p_sell.add_argument("--amount", required=True)
    p_sell.set_defaults(func=cmd_sell)

    p_rate = sub.add_parser("get-rate", help="Получить курс валюты")
    p_rate.add_argument("--from", dest="from_code", required=True)
    p_rate.add_argument("--to", dest="to_code", required=True)
    p_rate.set_defaults(func=cmd_get_rate)

    return parser


def interactive() -> None:
    """Интерактивный режим работы CLI."""
    print("Интерактивный режим. Введите 'help' для списка команд, 'exit' для выхода.")
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
            print("Доступные команды: register, login, logout, show-portfolio, buy, sell, get-rate, exit, logout")
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
            else:
                print("Неизвестная команда. Введите 'help'.")
        except SystemExit:
            pass
        except Exception as e:
            print(f"Ошибка: {e}")


def run(argv: Optional[List[str]] = None) -> int:
    """Запускает cli с переданными аргументами."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Если команда не передана, то запуск интерактивного режима
    if not args.command:
        interactive()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(run())