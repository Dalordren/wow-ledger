from app.security import hash_password, verify_password

RAW_PASSWORD = "Thisisatestpassword"


def test_password_is_hashed():
    hashed = hash_password(RAW_PASSWORD)
    assert hashed != RAW_PASSWORD
    assert hashed.startswith("$argon2")


def test_password_verification():
    hashed = hash_password(RAW_PASSWORD)
    assert verify_password(RAW_PASSWORD, hashed) is True


def test_wrong_password_fails_verification():
    hashed = hash_password(RAW_PASSWORD)
    assert verify_password("thisisnotraw_password", hashed) is False


def test_raw_password_hashed_twice_returns_different_hashes():
    hashed = hash_password(RAW_PASSWORD)
    second_hashed_password = hash_password(RAW_PASSWORD)
    assert hashed != second_hashed_password
