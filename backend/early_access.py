from collections import deque
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from threading import Lock
import time

LOCAL_PART_PATTERN = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+\Z")
DOMAIN_LABEL_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
SIGNUP_RATE_LIMIT = 10
SIGNUP_RATE_WINDOW_SECONDS = 60
MAX_TRACKED_CLIENTS = 1000
_signup_attempts: dict[str, deque[float]] = {}
_signup_attempts_lock = Lock()


class DuplicateSubscriberError(Exception):
    pass


def signup_request_is_limited(client_address: str | None) -> bool:
    key = client_address or "unknown"
    now = time.monotonic()
    with _signup_attempts_lock:
        for address, attempts in tuple(_signup_attempts.items()):
            while attempts and now - attempts[0] >= SIGNUP_RATE_WINDOW_SECONDS:
                attempts.popleft()
            if not attempts:
                del _signup_attempts[address]

        attempts = _signup_attempts.get(key)
        if attempts is None:
            if len(_signup_attempts) >= MAX_TRACKED_CLIENTS:
                del _signup_attempts[next(iter(_signup_attempts))]
            attempts = deque()
            _signup_attempts[key] = attempts

        if len(attempts) >= SIGNUP_RATE_LIMIT:
            return True
        attempts.append(now)
        return False


def normalize_email(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Enter a valid email address.")

    candidate = value.strip()
    if not candidate or len(candidate) > 254 or candidate.count("@") != 1:
        raise ValueError("Enter a valid email address.")

    local_part, domain = candidate.rsplit("@", 1)
    if (
        not local_part
        or len(local_part) > 64
        or local_part.startswith(".")
        or local_part.endswith(".")
        or ".." in local_part
        or not LOCAL_PART_PATTERN.fullmatch(local_part)
        or not domain
        or domain.endswith(".")
    ):
        raise ValueError("Enter a valid email address.")

    try:
        ascii_domain = domain.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("Enter a valid email address.") from exc

    labels = ascii_domain.split(".")
    if (
        len(ascii_domain) > 253
        or len(labels) < 2
        or any(not DOMAIN_LABEL_PATTERN.fullmatch(label) for label in labels)
        or not re.search(r"[a-z]", labels[-1])
    ):
        raise ValueError("Enter a valid email address.")

    normalized = f"{local_part.lower()}@{ascii_domain}"
    if len(normalized) > 254:
        raise ValueError("Enter a valid email address.")
    return normalized


def subscribe_email(email: str, database_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(path, timeout=5)) as connection:
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS early_access_subscribers (
                    email TEXT PRIMARY KEY COLLATE NOCASE NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT INTO early_access_subscribers (email, created_at) VALUES (?, ?)",
                (email, datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise DuplicateSubscriberError from exc
