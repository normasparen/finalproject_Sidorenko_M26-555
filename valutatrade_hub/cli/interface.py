import argparse
import shlex

from valutatrade_hub.core import usecase as usecases
from valutatrade_hub.core.currencies import list_supported_codes
from valutatrade_hub.core.session import Session
from valutatrade_hub.core.storage import is_fresh
from valutatrade_hub.core.utils.exceptions import (
    ApiRequestError,
    BuyError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    LoginError,
    PortfolioError,
    RateError,
    RegisterError,
    SellError,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.scheduler import RatesScheduler
from valutatrade_hub.parser_service.storage import ParserStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


# Форматирование
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

_scheduler_instance = None  # глобальная переменная для хранения планировщика

def cmd_parser(args: argparse.Namespace) -> int:
    global _scheduler_instance

    # Если уже запущен, то остановить
    if args.stop:
        if _scheduler_instance:
            _scheduler_instance.stop()
            _scheduler_instance = None
            print("Parser Service остановлен.")
        else:
            print("Parser Service не запущен.")
        return 0

    # Если уже запущен - предупредить
    if _scheduler_instance:
        print(f"Parser Service уже работает (интервал: {_scheduler_instance.interval}s).")
        return 0

    interval = max(10, args.interval)
    _scheduler_instance = RatesScheduler(interval_seconds=interval)
    _scheduler_instance.start()
    print(f"Parser Service запущен в фоне (интервал: {interval}s).")
    print("Остановить: parser --stop")
    return 0

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
        value_str = _fmt_money(value) if value is not None else "-"
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
    except InsufficientFundsError as e:
        print(f"Ошибка: {e}")
        return 1

    print(f"Покупка выполнена: {_fmt_amount(result['amount'])} "
          f"{result['currency']} по курсу {_fmt_money(result['rate'])} USD/{result['currency']}")
    print("Изменения в портфеле:")
    print(f"- {result['currency']}: было {_fmt_amount(result['old_balance'])} "
          f"→ стало {_fmt_amount(result['new_balance'])}")
    if "old_usd" in result and "new_usd" in result:
        print(f"- USD: было {_fmt_money(result['old_usd'])} "
              f"→ стало {_fmt_money(result['new_usd'])}")
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
    if "old_usd" in result and "new_usd" in result:
        print(f"- USD: было {_fmt_money(result['old_usd'])} "
              f"→ стало {_fmt_money(result['new_usd'])}")
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

    updated = result["updated_at"].replace("T", " ") if result["updated_at"] else "-"
    print(f"Курс {result['from']}→{result['to']}: {result['rate']:.8f} "
          f"(обновлено: {updated})")
    if result["reverse_rate"] is not None:
        print(f"Обратный курс {result['to']}→{result['from']}: "
              f"{result['reverse_rate']:.8f}")
    return 0


def cmd_update_rates(args: argparse.Namespace) -> int:
    updater = RatesUpdater()
    result = updater.run_update()

    if result["status"] == "ok":
        print(f"Update successful. Total rates updated: {result['rates_count']}. "
              f"Last refresh: {result['last_refresh']}")
        return 0
    elif result["status"] == "partial":
        print(f"Update completed with some errors: {result['error']}")
        print(f"Total rates updated: {result['rates_count']}. "
              f"Last refresh: {result['last_refresh']}")
        return 0
    else:
        print(f"Update failed: {result['error']}")
        print("Check logs/parser.log for details.")
        return 1

def cmd_show_rates(args: argparse.Namespace) -> int:
    cfg = ParserConfig()
    storage = ParserStorage(cfg.RATES_FILE_PATH, cfg.HISTORY_FILE_PATH)
    snapshot = storage.get_rates_snapshot()

    if "pairs" in snapshot:
        pairs = snapshot["pairs"]
    else:
        pairs = {k: v for k, v in snapshot.items() if k != "last_refresh"}

    last_refresh = snapshot.get("last_refresh") or "—"

    if not pairs:
        print("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")
        return 1

    # Фильтруем только валидные записи
    items = []
    for k, v in pairs.items():
        if not isinstance(v, dict):
            continue  # пропускаем старые «голые числа»
        if "rate" not in v:
            continue
        items.append((k, v))

    if not items:
        print("Кэш содержит только некорректные записи. Выполните 'update-rates'.")
        return 1

    if args.currency:
        code = args.currency.upper()
        items = [(k, v) for k, v in items if k.startswith(f"{code}_") or k.endswith(f"_{code}")]
        if not items:
            print(f"Курс для '{code}' не найден в кеше.")
            return 1

    if args.base:
        base = args.base.upper()
        items = [(k, v) for k, v in items if k.endswith(f"_{base}")]
        if not items:
            print(f"Курсы для базы '{base}' не найдены.")
            return 1

    if args.top:
        items.sort(key=lambda kv: float(kv[1]["rate"]), reverse=True)
        items = items[:args.top]

    print(f"Rates from cache (updated at {last_refresh}):")
    for pair, data in items:
        rate = data["rate"]
        source = data.get("source") or "—"
        print(f"- {pair}: {float(rate):.8f}  (source: {source})")
    return 0

# Аргументы
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wallet-cli",
        description="CLI для управления портфелем",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    p = sub.add_parser("register", help="Регистрация пользователя")
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)
    p.set_defaults(func=cmd_register)

    p = sub.add_parser("login", help="Вход в систему")
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("show-portfolio", help="Показать портфель")
    p.add_argument("--base", default="USD")
    p.set_defaults(func=cmd_show_portfolio)

    p = sub.add_parser("buy", help="Купить валюту")
    p.add_argument("--currency", required=True)
    p.add_argument("--amount", required=True)
    p.set_defaults(func=cmd_buy)

    p = sub.add_parser("sell", help="Продать валюту")
    p.add_argument("--currency", required=True)
    p.add_argument("--amount", required=True)
    p.set_defaults(func=cmd_sell)

    p = sub.add_parser("get-rate", help="Получить курс валюты")
    p.add_argument("--from", dest="from_code", required=True)
    p.add_argument("--to", dest="to_code", required=True)
    p.set_defaults(func=cmd_get_rate)

    p = sub.add_parser("parser", help="Запустить Parser Service в фоне")
    p.add_argument("--interval", type=int, default=120,
                   help="Интервал обновления в секундах (по умолчанию 120)")
    p.add_argument("--stop", action="store_true", help="Остановить Parser Service")
    p.set_defaults(func=cmd_parser)

    p = sub.add_parser("update-rates", help="Обновить курсы через CoinGecko + ExchangeRate-API")
    p.set_defaults(func=cmd_update_rates)

    p = sub.add_parser("show-rates", help="Показать кеш курсов")
    p.add_argument("--currency", help="Фильтр по коду валюты (BTC, EUR)")
    p.add_argument("--top", type=int, help="Топ N самых дорогих")
    p.add_argument("--base", help="Базовая валюта (USD, EUR)")
    p.set_defaults(func=cmd_show_rates)

    return parser


# Интерактивный режим
def interactive() -> None:
    bootstrap_rates_if_needed()
    print("Интерактивный режим. 'help' - команды, 'exit' - выход.")
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
            print("Доступные команды: register, login, logout, show-portfolio, "
                  "buy, sell, get-rate, parser, update-rates, show-rates, exit, logout")
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

def bootstrap_rates_if_needed() -> None:
    """Обновляет курсы, если кэш пуст или устарел."""
    from valutatrade_hub.parser_service.config import ParserConfig
    from valutatrade_hub.parser_service.storage import ParserStorage
    from valutatrade_hub.parser_service.updater import RatesUpdater


    cfg = ParserConfig()
    storage = ParserStorage(cfg.RATES_FILE_PATH, cfg.HISTORY_FILE_PATH)
    snapshot = storage.get_rates_snapshot()

    pairs = snapshot.get("pairs", snapshot)
    pairs = {k: v for k, v in pairs.items() if k != "last_refresh"}

    # Если кэш пуст или все записи устарели — обновляем
    fresh_count = sum(
        1 for v in pairs.values()
        if isinstance(v, dict) and is_fresh(v.get("updated_at", ""))
    )
    if fresh_count == 0:
        print("Курсы устарели или отсутствуют. Обновляем..")
        result = RatesUpdater(cfg).run_update()
        if result["status"] in ("ok", "partial"):
            print(f"Обновлено курсов: {result['rates_count']}")
        else:
            print(f"Не удалось обновить курсы: {result.get('error')}")
            print("Запустите 'update-rates' вручную.")

# run
def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        interactive()
        return 0
    return args.func(args)
