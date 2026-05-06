from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import Settings
from app.models import ContactRequest


SENDGRID_MAIL_SEND_URL = "https://api.sendgrid.com/v3/mail/send"

CONTACT_TYPE_LABELS = {
    "wrong-info": "誤った情報のご指摘",
    "improvement": "改善のご要望",
    "other": "その他、運営へのお問い合わせ",
}


class EmailNotConfiguredError(RuntimeError):
    pass


class EmailSendError(RuntimeError):
    pass


def send_contact_email(settings: Settings, payload: ContactRequest) -> None:
    if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
        raise EmailNotConfiguredError("SendGrid settings are not configured")

    body = json.dumps(build_sendgrid_payload(settings, payload), ensure_ascii=False).encode("utf-8")
    request = Request(
        SENDGRID_MAIL_SEND_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            if response.status != 202:
                raise EmailSendError(f"SendGrid returned HTTP {response.status}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise EmailSendError(f"SendGrid returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise EmailSendError(str(exc)) from exc
    except OSError as exc:
        raise EmailSendError(str(exc)) from exc


def build_sendgrid_payload(settings: Settings, payload: ContactRequest) -> dict[str, object]:
    subject = f"[ウシガー] {CONTACT_TYPE_LABELS[payload.type]}"
    return {
        "personalizations": [
            {
                "to": [{"email": settings.contact_recipient_email}],
                "subject": subject,
            }
        ],
        "from": {
            "email": settings.sendgrid_from_email,
            "name": settings.sendgrid_from_name,
        },
        "reply_to": {"email": payload.email, "name": payload.name},
        "content": [
            {
                "type": "text/plain",
                "value": build_contact_body(payload),
            }
        ],
    }


def build_contact_body(payload: ContactRequest) -> str:
    organization = payload.organization.strip() if payload.organization else "未入力"
    return "\n".join(
        [
            "ウシガーへの問い合わせが送信されました。",
            "",
            f"お名前: {payload.name}",
            f"ご所属: {organization}",
            f"ご連絡先のメールアドレス: {payload.email}",
            f"お問い合わせの種類: {CONTACT_TYPE_LABELS[payload.type]}",
            "",
            "お問い合わせの詳細:",
            payload.detail,
        ]
    )
