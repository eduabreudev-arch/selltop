from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class UserStatus(str, Enum):
    PENDING   = "pending"    # aguardando verificação de e-mail
    ACTIVE    = "active"     # ativo e verificado
    SUSPENDED = "suspended"  # suspenso por admin

class UserRole(str, Enum):
    USER  = "user"
    ADMIN = "admin"

@dataclass
class User:
    id:                int   | None = None
    name:              str         = ""
    email:             str         = ""
    password_hash:     str         = ""
    role:              str         = UserRole.USER
    status:            str         = UserStatus.PENDING
    email_verified:    bool        = False
    created_at:        str         = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at:        str         = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login:        str | None  = None
    failed_attempts:   int         = 0
    locked_until:      str | None  = None

    # ------------------------------------------------------------------ #
    # Conversão de/para dict (para persistência e serialização)
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_row(cls, row: dict) -> "User":
        return cls(
            id               = row["id"],
            name             = row["name"],
            email            = row["email"],
            password_hash    = row["password_hash"],
            role             = row["role"],
            status           = row["status"],
            email_verified   = bool(row["email_verified"]),
            created_at       = row["created_at"],
            updated_at       = row["updated_at"],
            last_login       = row["last_login"],
            failed_attempts  = row["failed_attempts"],
            locked_until     = row["locked_until"],
        )

    def is_locked(self) -> bool:
        if not self.locked_until:
            return False
        return datetime.now(timezone.utc).isoformat() < self.locked_until

    def safe_dict(self) -> dict:
        """Retorna dados sem informações sensíveis."""
        d = self.to_dict()
        d.pop("password_hash", None)
        d.pop("failed_attempts", None)
        d.pop("locked_until", None)
        return d
