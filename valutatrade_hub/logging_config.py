import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str = "logs/actions.log", level=logging.INFO):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        '%(levelname)s %(asctime)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )

    # ротация
    handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=3)
    handler.setFormatter(formatter)

    logger = logging.getLogger("valutatrade")
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


logger = setup_logging()