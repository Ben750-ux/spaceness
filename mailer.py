import json
import os
import smtplib
from email.mime.text import MIMEText

CONFIG_FILE = "email_config.json"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def _load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(email: str, password: str) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump({"email": email, "password": password}, f)


def send_verification_code(to_email: str, code: str) -> tuple[bool, str]:
    print(f"\n[MAILER] Code de verification pour {to_email}: {code}\n")
    config = _load_config()
    sender = config.get("email", "spaceness15@gmail.com")
    password = config.get("password", "")

    if not password:
        return False, (
            "Mot de passe d'application Gmail non configuré. "
            "Va dans Paramètres → Configurer email"
        )

    subject = "Code de vérification - Spaceness"
    body = f"""Bienvenue sur Spaceness !

Votre code de vérification est : {code}

Ce code expire dans 10 minutes.

Si vous n'avez pas créé de compte, ignorez cet email.
"""

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        return True, "Email envoyé avec succès"
    except Exception as e:
        return False, f"Erreur d'envoi : {str(e)}"
