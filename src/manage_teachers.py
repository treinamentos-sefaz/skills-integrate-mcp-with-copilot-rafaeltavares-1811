import argparse
import json
import os
from getpass import getpass

from auth import CREDENTIALS_FILE, create_password_record


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or reset a teacher login.")
    parser.add_argument("username", help="Teacher username")
    args = parser.parse_args()
    username = args.username.strip()
    if not username:
        parser.error("username cannot be empty")

    password = getpass("Password (at least 12 characters): ")
    if len(password) < 12:
        parser.error("password must be at least 12 characters")
    if password != getpass("Confirm password: "):
        parser.error("passwords do not match")

    if CREDENTIALS_FILE.exists():
        try:
            data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            parser.error(f"invalid JSON in {CREDENTIALS_FILE}: {error}")
        if not isinstance(data, dict) or not isinstance(data.get("teachers"), list):
            parser.error(f"{CREDENTIALS_FILE} must contain a 'teachers' list")
        teachers = data["teachers"]
    else:
        teachers = []

    if any(not isinstance(teacher, dict) for teacher in teachers):
        parser.error(f"invalid teacher record in {CREDENTIALS_FILE}")

    record = {"username": username, **create_password_record(password)}
    for index, teacher in enumerate(teachers):
        if teacher.get("username") == username:
            teachers[index] = record
            break
    else:
        teachers.append(record)

    CREDENTIALS_FILE.write_text(
        json.dumps({"teachers": teachers}, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        os.chmod(CREDENTIALS_FILE, 0o600)
    except OSError:
        parser.error(f"could not restrict permissions on {CREDENTIALS_FILE}")
    print(f"Teacher account saved to {CREDENTIALS_FILE}")


if __name__ == "__main__":
    main()
