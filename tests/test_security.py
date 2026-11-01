from datetime import timedelta

import jwt
import pytest

from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret-pwd")
    assert hashed != "secret-pwd"
    assert verify_password("secret-pwd", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip() -> None:
    token = create_access_token(42, "admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_expired_token_is_rejected() -> None:
    token = create_access_token(1, "user", expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(1, "user")
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token[:-2] + "xx")
