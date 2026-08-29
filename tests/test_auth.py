import pytest
from fastapi import HTTPException

from app.controllers.api.utils.auth import validate_operator_api_key
from app.infra.config.auth import AuthSettings


def test_operator_authentication_rejects_unconfigured_key():
    with pytest.raises(HTTPException) as exc_info:
        validate_operator_api_key(None, AuthSettings(edge_api_key="edge"))

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Operator API is not configured"


def test_operator_authentication_rejects_missing_key():
    settings = AuthSettings(edge_api_key="edge", operator_api_key="operator")

    with pytest.raises(HTTPException) as exc_info:
        validate_operator_api_key(None, settings)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Operator API key is missing"


def test_operator_authentication_rejects_invalid_key():
    settings = AuthSettings(edge_api_key="edge", operator_api_key="operator")

    with pytest.raises(HTTPException) as exc_info:
        validate_operator_api_key("wrong", settings)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid operator API key"


def test_operator_authentication_accepts_valid_key():
    settings = AuthSettings(edge_api_key="edge", operator_api_key="operator")

    assert validate_operator_api_key("operator", settings) is None
