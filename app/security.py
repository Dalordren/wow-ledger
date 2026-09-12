from pwdlib import PasswordHash

PASSWORD_HASHED = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return PASSWORD_HASHED.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return PASSWORD_HASHED.verify(plain_password, hashed_password)
