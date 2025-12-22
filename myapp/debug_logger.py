import logging


def setup_debug_logging():
    logger = logging.getLogger("fastapi")
    logger.setLevel(logging.DEBUG)

    # Файловый handler
    fh = logging.FileHandler("fastapi_debug.log")
    fh.setLevel(logging.DEBUG)

    # Консольный handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
