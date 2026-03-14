from mock import MagicMock
from pytest import fixture


@fixture()
def uow() -> MagicMock:
    uow = MagicMock()

    manager = MagicMock()
    manager.__aenter__.return_value = manager
    manager.__aexit__.return_value = None

    uow.begin.return_value = manager
    return uow
