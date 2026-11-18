import hashlib
import hmac
import json
import secrets
from pathlib import Path
from typing import Any


CREDENTIALS_FILE = Path(__file__).with_name("teachers.json")
PASSWORD_HASH_ITERATIONS = 310_000
PASSWORD_SALT_BYTES = 16


class TeacherCredentialConfigError(Exception):
    pass


def create_password_record(password: str) -> dict[str, str]:
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return {"salt": salt.hex(), "password_hash": password_hash.hex()}


def _read_teacher_records() -> list[dict[str, Any]]:
    try:
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise TeacherCredentialConfigError(
            "Teacher accounts are not configured. Run "
            "`python src/manage_teachers.py <username>` to add one."
        ) from error
    except json.JSONDecodeError as error:
        raise TeacherCredentialConfigError(
            f"Teacher credentials file is not valid JSON: {CREDENTIALS_FILE}"
        ) from error

    if not isinstance(data, dict) or not isinstance(data.get("teachers"), list):
        raise TeacherCredentialConfigError(
            f"Teacher credentials file must contain a 'teachers' list: {CREDENTIALS_FILE}"
        )

    records = data["teachers"]
    for record in records:
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("username"), str)
            or not isinstance(record.get("salt"), str)
            or not isinstance(record.get("password_hash"), str)
        ):
            raise TeacherCredentialConfigError(
                f"Invalid teacher credential record in {CREDENTIALS_FILE}"
            )

        try:
            salt = bytes.fromhex(record["salt"])
            password_hash = bytes.fromhex(record["password_hash"])
        except ValueError as error:
            raise TeacherCredentialConfigError(
                f"Invalid password hash encoding in {CREDENTIALS_FILE}"
            ) from error

        if len(salt) != PASSWORD_SALT_BYTES or len(password_hash) != 32:
            raise TeacherCredentialConfigError(
                f"Invalid password hash length in {CREDENTIALS_FILE}"
            )

    return records


def verify_teacher_credentials(username: str, password: str) -> bool:
    for record in _read_teacher_records():
        if record["username"] != username:
            continue

        salt = bytes.fromhex(record["salt"])
        expected_hash = record["password_hash"]
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PASSWORD_HASH_ITERATIONS,
        ).hex()
        return hmac.compare_digest(actual_hash, expected_hash)

    return False
