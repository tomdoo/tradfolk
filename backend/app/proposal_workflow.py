import base64
import hashlib
import hmac
import json
import logging
import os
import time
from html import escape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"
VALIDATION_TOKEN_SALT = "proposal-user-validation"
ACTIVATION_TOKEN_SALT = "proposal-admin-activation"
VALIDATION_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
ACTIVATION_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


class TokenError(RuntimeError):
    pass


class TokenExpiredError(TokenError):
    pass


class TokenInvalidError(TokenError):
    pass


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _secret_key_bytes() -> bytes:
    return _get_env("SECRET_KEY", "change-me").encode("utf-8")


def _base64_encode(raw_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(raw_bytes).decode("ascii").rstrip("=")


def _base64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign_payload(payload: dict[str, Any], salt: str) -> str:
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload_part = _base64_encode(payload_bytes)
    digest = hmac.new(
        _secret_key_bytes(),
        f"{salt}.{payload_part}".encode(),
        hashlib.sha256,
    ).digest()
    return f"{payload_part}.{_base64_encode(digest)}"


def _load_signed_payload(token: str, salt: str, max_age_seconds: int) -> dict[str, Any]:
    try:
        payload_part, signature_part = token.rsplit(".", 1)
    except ValueError as error:
        raise TokenInvalidError("Malformed token") from error

    expected_digest = hmac.new(
        _secret_key_bytes(),
        f"{salt}.{payload_part}".encode(),
        hashlib.sha256,
    ).digest()
    try:
        received_digest = _base64_decode(signature_part)
    except Exception as error:
        raise TokenInvalidError("Malformed token signature") from error

    if not hmac.compare_digest(expected_digest, received_digest):
        raise TokenInvalidError("Invalid token signature")

    try:
        payload = json.loads(_base64_decode(payload_part).decode("utf-8"))
    except Exception as error:
        raise TokenInvalidError("Malformed token payload") from error

    issued_at = int(payload.get("issued_at", 0))
    if issued_at <= 0:
        raise TokenInvalidError("Missing issued_at")

    if time.time() - issued_at > max_age_seconds:
        raise TokenExpiredError("Token expired")

    return payload


def get_public_base_url() -> str:
    return _get_env("BASE_URL") or _get_env("API_URL") or "https://tradfolk.local"


def get_api_base_url() -> str:
    return _get_env("API_URL") or _get_env("BASE_URL") or "https://api.tradfolk.local"


def sign_validation_token(proposal_id: str) -> str:
    return _sign_payload(
        {"proposal_id": proposal_id, "issued_at": int(time.time())},
        VALIDATION_TOKEN_SALT,
    )


def sign_activation_token(proposal_id: str) -> str:
    return _sign_payload(
        {"proposal_id": proposal_id, "issued_at": int(time.time())},
        ACTIVATION_TOKEN_SALT,
    )


def load_validation_token(token: str) -> str:
    payload = _load_signed_payload(token, VALIDATION_TOKEN_SALT, VALIDATION_TOKEN_MAX_AGE_SECONDS)
    proposal_id = payload.get("proposal_id")
    if not proposal_id:
        raise TokenInvalidError("Missing proposal_id")
    return str(proposal_id)


def load_activation_token(token: str) -> str:
    payload = _load_signed_payload(token, ACTIVATION_TOKEN_SALT, ACTIVATION_TOKEN_MAX_AGE_SECONDS)
    proposal_id = payload.get("proposal_id")
    if not proposal_id:
        raise TokenInvalidError("Missing proposal_id")
    return str(proposal_id)


def html_feedback_page(
    title: str,
    message: str,
    link_href: str | None = None,
    link_label: str | None = None,
) -> str:
    safe_title = escape(title)
    safe_message = escape(message)
    button_html = ""
    if link_href and link_label:
        button_html = (
            f'<p style="margin-top:24px;">'
            f'<a href="{escape(link_href)}" '
            f'style="display:inline-block;padding:12px 18px;border-radius:12px;'
            f'background:#241b33;color:#fff6e8;text-decoration:none;font-weight:700;">'
            f"{escape(link_label)}"
            f"</a></p>"
        )

    return (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8' />"
        f"<title>{safe_title}</title>"
        "<meta name='viewport' content='width=device-width, initial-scale=1' />"
        "<style>body{margin:0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;"
        "background:#fff6e8;color:#241b33;display:grid;place-items:center;min-height:100vh;"
        "padding:24px;}main{max-width:560px;background:#fffdf8;border:1px solid rgba(36,27,51,.12);"
        "border-radius:20px;padding:28px;box-shadow:0 20px 40px -24px rgba(36,27,51,.25);}"
        "h1{margin:0 0 12px;font-size:28px;line-height:1.2;}"
        "p{margin:0;font-size:16px;line-height:1.6;color:#7c7189;}"
        "</style>"
        "</head><body><main>"
        f"<h1>{safe_title}</h1><p>{safe_message}</p>{button_html}"
        "</main></body></html>"
    )


def verify_turnstile_token(token: str, remote_ip: str | None = None) -> None:
    secret_key = _get_env("TURNSTILE_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("TURNSTILE_SECRET_KEY is missing")

    payload: dict[str, Any] = {"secret": secret_key, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    request = Request(
        TURNSTILE_VERIFY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError("Unable to verify Turnstile token") from error

    if not result.get("success"):
        errors = result.get("error-codes") or []
        raise RuntimeError(
            "Turnstile verification failed" + (f": {', '.join(errors)}" if errors else "")
        )


def send_brevo_email(
    recipient_email: str,
    recipient_name: str,
    subject: str,
    html_content: str,
    text_content: str,
) -> None:
    api_key = _get_env("BREVO_API_KEY")
    if not api_key:
        raise RuntimeError("BREVO_API_KEY is missing")

    sender_email = _get_env("BREVO_SENDER_EMAIL") or "noreply@tradfolk.local"
    sender_name = _get_env("BREVO_SENDER_NAME") or "Trad ou Folk ?"

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": recipient_email, "name": recipient_name}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }

    request = Request(
        BREVO_EMAIL_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": api_key,
            "accept": "application/json",
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            response.read()
    except HTTPError as error:
        error_body = ""
        try:
            error_body = error.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = ""

        raise RuntimeError(
            f"Unable to send Brevo email (HTTP {error.code})"
            + (f": {error_body}" if error_body else "")
        ) from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError("Unable to send Brevo email") from error


def build_validation_email(
    proposal_id: str,
    proposal_label: str,
    proposal_image_url: str | None,
    user_name: str,
    validation_url: str,
) -> tuple[str, str, str]:
    image_block = ""
    image_text = ""
    if proposal_image_url:
        safe_image_url = escape(proposal_image_url)
        safe_label = escape(proposal_label)
        image_block = (
            '<p style="margin:14px 0 10px;">Apercu de l\'image :</p>'
            f'<p><img src="{safe_image_url}" alt="Image pour {safe_label}" '
            'style="display:block;max-width:100%;width:auto;height:auto;'
            'max-height:360px;border-radius:10px;border:1px solid rgba(36,27,51,.12);" /></p>'
        )
        image_text = f"Image: {proposal_image_url}\n"

    subject = "Valide ta proposition Trad ou Folk ?"
    html_content = (
        f"<p>Salut {escape(user_name)},</p>"
        f"<p>Tu as proposé <strong>{escape(proposal_label)}</strong>.</p>"
        f"{image_block}"
        "<p>Pour confirmer que cette adresse email est correcte, clique sur ce lien :</p>"
        f'<p><a href="{escape(validation_url)}">Valider ma proposition</a></p>'
        "<p>Une fois validée, la proposition passera en modération.</p>"
    )
    text_content = (
        f"Salut {user_name},\n\n"
        f"Tu as proposé: {proposal_label}\n"
        f"{image_text}"
        f"Valide ton email ici: {validation_url}\n\n"
        "Une fois validée, la proposition passera en modération."
    )
    return subject, html_content, text_content


def build_admin_activation_email(
    proposal_id: str,
    proposal_label: str,
    proposal_image_url: str | None,
    user_name: str,
    user_email: str,
    activation_url: str,
) -> tuple[str, str, str]:
    image_text = "Image: (aucune image fournie)\n"
    if proposal_image_url:
        safe_image_url = escape(proposal_image_url)
        safe_label = escape(proposal_label)
        image_block = (
            '<p style="margin:14px 0 10px;">Image proposee :</p>'
            f'<p><img src="{safe_image_url}" alt="Image pour {safe_label}" '
            'style="display:block;max-width:100%;width:auto;height:auto;'
            'max-height:360px;border-radius:10px;border:1px solid rgba(36,27,51,.12);" /></p>'
        )
        image_text = f"Image: {proposal_image_url}\n"
    else:
        image_block = (
            '<p style="margin:14px 0 0;padding:10px 12px;border-radius:10px;'
            'background:#fce8ce;color:#7c7189;font-size:14px;">'
            "Aucune image fournie par l'utilisateur."
            "</p>"
        )

    subject = "Nouvelle proposition à activer"
    html_content = (
        f"<p>Une proposition a été validée par son auteur.</p>"
        f"<p><strong>{escape(proposal_label)}</strong><br />"
        f"Auteur: {escape(user_name)} ({escape(user_email)})</p>"
        f"{image_block}"
        f'<p><a href="{escape(activation_url)}">Activer la proposition</a></p>'
    )
    text_content = (
        "Une proposition a été validée par son auteur.\n\n"
        f"Proposition: {proposal_label}\n"
        f"Auteur: {user_name} ({user_email})\n"
        f"{image_text}"
        f"Activer: {activation_url}"
    )
    return subject, html_content, text_content
