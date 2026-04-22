# IAM App — Controle de Usuários com Flask

Sistema completo de Identity & Access Management (IAM) construído com Flask,
SQLite e arquitetura em camadas.

---

## Funcionalidades

- Cadastro com validação de senha forte
- Verificação de e-mail com link por token
- Login com proteção contra força bruta (bloqueio após 5 tentativas)
- Esqueci minha senha (link de reset com expiração de 1 hora)
- Reenvio de e-mail de verificação
- Atualização de nome e senha (autenticado)
- Exclusão de conta com confirmação por senha
- Painel admin: listar, alterar role, alterar status e excluir usuários
- Roles: `user` e `admin`
- Status: `pending`, `active`, `suspended`

---

## Estrutura

```
iam_app/
├── app.py                        # Factory e entry point
├── config.py                     # Configurações por ambiente
├── requirements.txt
├── models/
│   └── user.py                   # Entidade User
├── repositories/
│   └── user_repository.py        # Acesso ao banco (SQLite)
├── services/
│   ├── auth_service.py           # Toda a lógica IAM
│   └── email_service.py          # Envio de e-mails
├── controllers/
│   └── auth_controller.py        # Rotas (Blueprint Flask)
├── middleware/
│   └── auth_middleware.py        # Decorators de proteção
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── profile.html
    ├── forgot_password.html
    ├── reset_password.html
    ├── resend_verification.html
    ├── admin_users.html
    └── error.html
```

---

## Como rodar

### 1. Instalar dependências
```bash
pip install flask itsdangerous werkzeug
```

### 2. Rodar em modo desenvolvimento
```bash
python app.py
```
Acesse: http://localhost:5000

Em modo dev, os e-mails são impressos no console — não é necessário configurar SMTP.

### 3. Configurar e-mail real (opcional)
Crie um arquivo `.env` ou exporte as variáveis:
```bash
export MAIL_SERVER=smtp.gmail.com
export MAIL_PORT=587
export MAIL_USERNAME=seu@gmail.com
export MAIL_PASSWORD=sua_senha_de_app
export MAIL_FROM=seu@gmail.com
export SECRET_KEY=uma-chave-secreta-longa
export BASE_URL=http://seu-dominio.com
```

---

## Arquitetura

```
Controller (Blueprint)
    └── AuthService          ← toda a lógica de negócio
            ├── UserRepository   ← acesso ao banco
            └── EmailService     ← envio de e-mails
```

- **Models**: entidades puras (dataclasses), sem dependência de framework
- **Repository**: isolamento total do banco — troca SQLite por Postgres sem tocar no resto
- **Service**: orquestra regras de negócio, tokens, hashing
- **Controller**: apenas recebe request, chama service, retorna response
- **Middleware**: decorators reutilizáveis para proteção de rotas

---

## Segurança implementada

| Conceito              | Implementação                                      |
|-----------------------|----------------------------------------------------|
| Hash de senhas        | `werkzeug.security` (PBKDF2 + salt)               |
| Tokens de e-mail      | `itsdangerous.URLSafeTimedSerializer` (HMAC)      |
| Expiração de token    | 1 hora (configurável)                              |
| Brute-force           | Bloqueio por 15 min após 5 tentativas              |
| CSRF básico           | SameSite=Lax nos cookies de sessão                 |
| Enumeração de e-mail  | Respostas silenciosas em forgot/resend             |
| Cookie seguro         | HttpOnly + Secure em produção                      |
| Validação de senha    | 8+ chars, maiúscula, número, especial              |
