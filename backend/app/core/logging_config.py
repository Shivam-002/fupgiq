import logging


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # httpx logs every request at INFO
    logging.getLogger("httpx").setLevel(logging.WARNING)
