import pytest
from datetime import timedelta, datetime
from app.config import settings
from app.endpoints.auth import create_access_token
from app.crud import get_password_hash, generate_short_code
from jose import jwt

def test_get_password_hash():
    password = "my_secret_password"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    assert isinstance(hash1, str)
    assert hash1 == hash2

def test_generate_short_code_without_custom_alias():
    short_code = generate_short_code()
    assert short_code.startswith("hse")
    assert len(short_code) == 9

def test_generate_short_code_with_custom_alias():
    custom_alias = "custom123"
    short_code = generate_short_code(custom_alias)
    assert short_code == custom_alias

def test_create_access_token():
    payload = {"sub": "testuser"}
    expires = timedelta(minutes=1)
    token = create_access_token(payload, expires_delta=expires)
    
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded.get("sub") == "testuser"
    assert "exp" in decoded
    exp_timestamp = decoded.get("exp")
    now_timestamp = datetime.utcnow().timestamp()
    assert exp_timestamp > now_timestamp
