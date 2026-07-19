"""
webapp/auth.py
Проверка Telegram WebApp initData (HMAC-SHA256 по BOT_TOKEN).
Док: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_init_data(init_data: str, bot_token: str, max_age_sec: int = 86400) -> dict | None:
    """
    Возвращает распарсенного пользователя {'id':..., 'first_name':..., ...}
    если подпись валидна и данные не протухли, иначе None.
    """
    if not init_data:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        return None

    # Защита от повторного использования старого initData
    auth_date = pairs.get("auth_date")
    if max_age_sec and auth_date and auth_date.isdigit():
        if time.time() - int(auth_date) > max_age_sec:
            return None

    try:
        user = json.loads(pairs.get("user", ""))
    except (ValueError, TypeError):
        return None
    if not isinstance(user, dict) or "id" not in user:
        return None
    return user
