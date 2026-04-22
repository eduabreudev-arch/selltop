import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, config):
        self.server   = config.get("MAIL_SERVER")
        self.port     = config.get("MAIL_PORT", 587)
        self.use_tls  = config.get("MAIL_USE_TLS", True)
        self.username = config.get("MAIL_USERNAME", "")
        self.password = config.get("MAIL_PASSWORD", "")
        self.from_    = config.get("MAIL_FROM", "noreply@app.com")
        self.debug    = config.get("MAIL_DEBUG", False)

    def send(self, to: str, subject: str, html: str) -> bool:
        if self.debug or not self.username:
            # Em dev, imprime no console em vez de enviar
            logger.info(f"\n{'='*60}\nE-MAIL (modo dev)\nPara: {to}\nAssunto: {subject}\n{html}\n{'='*60}")
            return True
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = self.from_
            msg["To"]      = to
            msg.attach(MIMEText(html, "html", "utf-8"))
            with smtplib.SMTP(self.server, self.port) as smtp:
                if self.use_tls:
                    smtp.starttls()
                smtp.login(self.username, self.password)
                smtp.sendmail(self.from_, to, msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail: {e}")
            return False

    # ------------------------------------------------------------------ #
    # Templates de e-mail
    # ------------------------------------------------------------------ #
    def send_verification(self, to: str, name: str, link: str) -> bool:
        html = f"""
        <div style="font-family:sans-serif;max-width:500px;margin:auto;padding:32px">
          <h2 style="color:#1a1a18">Confirme seu e-mail</h2>
          <p>Olá, <strong>{name}</strong>!</p>
          <p>Clique no botão abaixo para verificar seu endereço de e-mail:</p>
          <a href="{link}" style="display:inline-block;background:#1a1a18;color:#fff;
             padding:12px 24px;border-radius:8px;text-decoration:none;margin:16px 0">
            Verificar e-mail
          </a>
          <p style="color:#888;font-size:12px">Este link expira em 1 hora.<br>
          Se você não criou uma conta, ignore este e-mail.</p>
        </div>"""
        return self.send(to, "Verifique seu e-mail", html)

    def send_password_reset(self, to: str, name: str, link: str) -> bool:
        html = f"""
        <div style="font-family:sans-serif;max-width:500px;margin:auto;padding:32px">
          <h2 style="color:#1a1a18">Redefinir senha</h2>
          <p>Olá, <strong>{name}</strong>!</p>
          <p>Recebemos uma solicitação para redefinir sua senha:</p>
          <a href="{link}" style="display:inline-block;background:#1a1a18;color:#fff;
             padding:12px 24px;border-radius:8px;text-decoration:none;margin:16px 0">
            Redefinir senha
          </a>
          <p style="color:#888;font-size:12px">Este link expira em 1 hora.<br>
          Se você não solicitou a redefinição, ignore este e-mail.</p>
        </div>"""
        return self.send(to, "Redefinição de senha", html)
