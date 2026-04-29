import re
import logging
from datetime import datetime, timezone, timedelta

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from models.user import User, UserStatus, UserRole
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

MAX_FAILED   = 5          # tentativas antes de bloquear
LOCK_MINUTES = 15         # tempo de bloqueio após falhas

class AuthError(Exception):
    pass

class AuthService:
    def __init__(self, repo: UserRepository, email_svc: EmailService,
                 secret_key: str, token_max_age: int, base_url: str):
        self._repo      = repo
        self._email     = email_svc
        self._serializer = URLSafeTimedSerializer(secret_key)
        self._max_age   = token_max_age
        self._base_url  = base_url.rstrip("/")

    # ------------------------------------------------------------------ #
    # Validações
    # ------------------------------------------------------------------ #
    @staticmethod
    def _validate_password(password: str) -> list[str]:
        errors = []
        if len(password) < 8:
            errors.append("Mínimo 8 caracteres.")
        if not re.search(r"[A-Z]", password):
            errors.append("Pelo menos uma letra maiúscula.")
        if not re.search(r"[0-9]", password):
            errors.append("Pelo menos um número.")
        if not re.search(r"[^A-Za-z0-9]", password):
            errors.append("Pelo menos um caractere especial.")
        return errors

    @staticmethod
    def _validate_email(email: str) -> bool:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

    # ------------------------------------------------------------------ #
    # Registro
    # ------------------------------------------------------------------ #
    def register(self, name: str, email: str, password: str) -> User:
        name  = name.strip()
        email = email.strip().lower()

        if not name or len(name) < 2:
            raise AuthError("Nome deve ter pelo menos 2 caracteres.")
        if not self._validate_email(email):
            raise AuthError("E-mail inválido.")
        if self._repo.email_exists(email):
            raise AuthError("E-mail já cadastrado.")

        errors = self._validate_password(password)
        if errors:
            raise AuthError(" ".join(errors))

        user = User(
            name          = name,
            email         = email,
            password_hash = generate_password_hash(password),
            role          = UserRole.USER,
            status        = UserStatus.PENDING,
            email_verified= False,
        )
        user = self._repo.create(user)
        self._send_verification(user)
        return user

    # ------------------------------------------------------------------ #
    # Login
    # ------------------------------------------------------------------ #
    def login(self, email: str, password: str) -> User:
        email = email.strip().lower()
        user  = self._repo.find_by_email(email)

        if not user:
            raise AuthError("E-mail ou senha incorretos.")

        if user.is_locked():
            raise AuthError(f"Conta bloqueada por excesso de tentativas. Tente novamente em breve.")

        if not check_password_hash(user.password_hash, password):
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_FAILED:
                locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCK_MINUTES)
                user.locked_until = locked_until.isoformat()
                logger.warning(f"Conta {email} bloqueada por {LOCK_MINUTES} min.")
            self._repo.update(user)
            remaining = MAX_FAILED - user.failed_attempts
            if remaining > 0:
                raise AuthError(f"Senha incorreta. {remaining} tentativa(s) restante(s).")
            raise AuthError("Conta bloqueada por excesso de tentativas.")

        if user.status == UserStatus.SUSPENDED:
            raise AuthError("Conta suspensa. Entre em contato com o suporte.")

        if not user.email_verified:
            raise AuthError("E-mail não verificado. Verifique sua caixa de entrada.")

        # Login bem-sucedido
        user.failed_attempts = 0
        user.locked_until    = None
        user.last_login      = datetime.now(timezone.utc).isoformat()
        self._repo.update(user)
        return user

    # ------------------------------------------------------------------ #
    # Verificação de e-mail
    # ------------------------------------------------------------------ #
    def _send_verification(self, user: User) -> None:
        token = self._serializer.dumps(user.email, salt="email-verify")
        link  = f"{self._base_url}/auth/verify-email/{token}"
        self._email.send_verification(user.email, user.name, link)

    def verify_email(self, token: str) -> User:
        try:
            email = self._serializer.loads(token, salt="email-verify", max_age=self._max_age)
        except SignatureExpired:
            raise AuthError("Link expirado. Solicite um novo.")
        except BadSignature:
            raise AuthError("Link inválido.")

        user = self._repo.find_by_email(email)
        if not user:
            raise AuthError("Usuário não encontrado.")
        if user.email_verified:
            return user  # já verificado — ok

        user.email_verified = True
        user.status         = UserStatus.ACTIVE
        self._repo.update(user)
        return user

    def resend_verification(self, email: str) -> None:
        user = self._repo.find_by_email(email.strip().lower())
        if not user:
            return  # silencioso para não vazar se e-mail existe
        if user.email_verified:
            return
        self._send_verification(user)

    # ------------------------------------------------------------------ #
    # Esqueci minha senha
    # ------------------------------------------------------------------ #
    def request_password_reset(self, email: str) -> None:
        user = self._repo.find_by_email(email.strip().lower())
        if not user or not user.email_verified:
            return  # silencioso
        token = self._serializer.dumps(user.email, salt="pw-reset")
        link  = f"{self._base_url}/auth/reset-password/{token}"
        self._email.send_password_reset(user.email, user.name, link)

    def reset_password(self, token: str, new_password: str) -> User:
        try:
            email = self._serializer.loads(token, salt="pw-reset", max_age=self._max_age)
        except SignatureExpired:
            raise AuthError("Link expirado. Solicite um novo.")
        except BadSignature:
            raise AuthError("Link inválido.")

        user = self._repo.find_by_email(email)
        if not user:
            raise AuthError("Usuário não encontrado.")

        errors = self._validate_password(new_password)
        if errors:
            raise AuthError(" ".join(errors))

        user.password_hash   = generate_password_hash(new_password)
        user.failed_attempts = 0
        user.locked_until    = None
        self._repo.update(user)
        return user

    # ------------------------------------------------------------------ #
    # Atualização de perfil / senha logado
    # ------------------------------------------------------------------ #
    def update_profile(self, user_id: int, name: str) -> User:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise AuthError("Usuário não encontrado.")
        name = name.strip()
        if len(name) < 2:
            raise AuthError("Nome deve ter pelo menos 2 caracteres.")
        user.name = name
        self._repo.update(user)
        return user

    def change_password(self, user_id: int, current_pw: str, new_pw: str) -> None:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise AuthError("Usuário não encontrado.")
        if not check_password_hash(user.password_hash, current_pw):
            raise AuthError("Senha atual incorreta.")
        errors = self._validate_password(new_pw)
        if errors:
            raise AuthError(" ".join(errors))
        user.password_hash = generate_password_hash(new_pw)
        self._repo.update(user)

    def delete_account(self, user_id: int, password: str) -> None:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise AuthError("Usuário não encontrado.")
        if not check_password_hash(user.password_hash, password):
            raise AuthError("Senha incorreta.")
        self._repo.delete(user_id)

    # ------------------------------------------------------------------ #
    # Admin
    # ------------------------------------------------------------------ #
    def admin_list_users(self) -> list[User]:
        return self._repo.list_all()

    def admin_change_status(self, user_id: int, status: str) -> User:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise AuthError("Usuário não encontrado.")
        if status not in [s.value for s in UserStatus]:
            raise AuthError("Status inválido.")
        user.status = status
        self._repo.update(user)
        return user

    def delete_account_admin(self, user_id: int) -> None:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise AuthError("Usuário não encontrado.")
        self._repo.delete(user_id)

    def admin_change_role(self, user_id: int, role: str) -> User:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise AuthError("Usuário não encontrado.")
        if role not in [r.value for r in UserRole]:
            raise AuthError("Role inválida.")
        user.role = role
        self._repo.update(user)
        return user
