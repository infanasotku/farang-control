import logging
import logging.config
import pathlib

import yaml

_LOGGER = None


def _get_config() -> dict:
    config_path = (pathlib.Path(__file__).parent / "config.yaml").resolve().as_posix()

    with open(config_path, "r") as config_file:
        return yaml.safe_load(config_file)


def _create_logger() -> logging.Logger:
    config = _get_config()

    logging.config.dictConfig(config)
    return logging.getLogger("uvicorn")


def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = _create_logger()
    return _LOGGER
