"""Envoi d'emails transactionnels via Resend (https://resend.com)"""
import httpx

from config import settings

API_URL = "https://api.resend.com/emails"


class MailError(RuntimeError):
    pass


def _code_email_html(title: str, code: str, note: str) -> str:
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:auto;padding:24px;background:#fff;border-radius:12px;border:1px solid #e2e8f0">
      <div style="text-align:center">
        <span style="display:inline-block;background:#009fe3;color:#fff;font-weight:800;font-size:22px;padding:12px 18px;border-radius:12px">S</span>
      </div>
      <h2 style="color:#0f172a;text-align:center;margin:20px 0 8px">{title}</h2>
      <p style="color:#475569;font-size:14px;text-align:center;line-height:21px">
        Voici votre code. Il est valable <strong>10 minutes</strong>.
      </p>
      <div style="text-align:center;margin:22px 0">
        <span style="display:inline-block;background:#e0f2fe;color:#009fe3;font-size:30px;font-weight:800;letter-spacing:8px;padding:14px 22px;border-radius:10px">{code}</span>
      </div>
      <p style="color:#94a3b8;font-size:12px;text-align:center">{note}</p>
    </div>
    """


async def _send(to_email: str, subject: str, html: str, text: str) -> None:
    """Envoie un email. Monte une exception en cas d'échec."""
    if not settings.resend_api_key:
        raise MailError("RESEND_API_KEY non configure")
    payload = {
        "from": settings.resend_from,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            API_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json=payload,
        )
        resp.raise_for_status()


async def send_reset_code(to_email: str, code: str) -> None:
    await _send(
        to_email,
        f"Votre code de réinitialisation : {code}",
        _code_email_html(
            "Réinitialisation du mot de passe",
            code,
            "Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.",
        ),
        f"Votre code de réinitialisation Spaceness : {code}\nIl est valable 10 minutes.",
    )


async def send_verification_code(to_email: str, code: str) -> None:
    await _send(
        to_email,
        f"Votre code de vérification : {code}",
        _code_email_html(
            "Vérification de votre email",
            code,
            "Si vous n'avez pas créé de compte Spaceness, ignorez cet email.",
        ),
        f"Votre code de vérification Spaceness : {code}\nIl est valable 10 minutes.",
    )
