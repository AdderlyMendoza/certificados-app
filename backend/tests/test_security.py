"""Tests de hashing y JWT."""
from __future__ import annotations

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing_roundtrip() -> None:
    hashed = hash_password("Secret123!")
    assert hashed != "Secret123!"
    assert verify_password("Secret123!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_decodes_with_correct_type() -> None:
    token = create_access_token(42)
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_token_type_mismatch_raises() -> None:
    token = create_refresh_token(1)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, expected_type="access")
