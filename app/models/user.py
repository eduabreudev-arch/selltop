from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class UserStatus(str, Enum):
    PENDING   = "pending"
    ACTIVE    = "active"
    SUSPENDED = "suspended"

class UserRole(str, Enum):
    USER  = "user"
    ADMIN = "admin"

@dataclass
class User:
    id:                           int | None = None
    name:                         str        = ""
    email:                        str        = ""
    password_hash:                str        = ""
    role:                         str        = UserRole.USER
    status:                       str        = UserStatus.PENDING
    email_verified:               bool       = False
    created_at:                   str        = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at:                   str        = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login:                   str | None = None
    failed_attempts:              int        = 0
    locked_until:                 str | None = None
    verification_code:            str | None = None
    verification_code_expires_at: str | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_row(cls, row: dict) -> "User":
        return cls(
            id                           = row["id"],
            name                         = row["name"],
            email                        = row["email"],
            password_hash                = row["password_hash"],
            role                         = row["role"],
            status                       = row["status"],
            email_verified               = bool(row["email_verified"]),
            created_at                   = row["created_at"],
            updated_at                   = row["updated_at"],
            last_login                   = row["last_login"],
            failed_attempts              = row["failed_attempts"],
            locked_until                 = row["locked_until"],
            verification_code            = row.get("verification_code"),
            verification_code_expires_at = row.get("verification_code_expires_at"),
        )

    def is_locked(self) -> bool:
        if not self.locked_until:
            return False
        return datetime.now(timezone.utc).isoformat() < self.locked_until

    def safe_dict(self) -> dict:
        d = self.to_dict()
        d.pop("password_hash", None)
        d.pop("failed_attempts", None)
        d.pop("locked_until", None)
        d.pop("verification_code", None)
        d.pop("verification_code_expires_at", None)
        return d


from sqlalchemy import MetaData, Table, Column, Integer, Text

metadata = MetaData()

users_table = Table("users", metadata,
    Column("id",                           Integer, primary_key=True, autoincrement=True),
    Column("name",                         Text,    nullable=False),
    Column("email",                        Text,    nullable=False, unique=True),
    Column("password_hash",                Text,    nullable=False),
    Column("role",                         Text,    nullable=False, server_default="user"),
    Column("status",                       Text,    nullable=False, server_default="pending"),
    Column("email_verified",               Integer, nullable=False, server_default="0"),
    Column("created_at",                   Text,    nullable=False),
    Column("updated_at",                   Text,    nullable=False),
    Column("last_login",                   Text),
    Column("failed_attempts",              Integer, nullable=False, server_default="0"),
    Column("locked_until",                 Text),
    Column("verification_code",            Text),
    Column("verification_code_expires_at", Text),
)