"""Autenticazione per la pagina di login di Gradio."""
from __future__ import annotations

import hmac
from typing import Callable


def make_auth(username: str, password: str) -> Callable[[str, str], bool]:
    """Ritorna la callable `auth` per `launch()`: confronto a tempo costante."""
    expected_user = username.encode()
    expected_pass = password.encode()

    def check(user: str, pwd: str) -> bool:
        # entrambi i confronti sempre eseguiti, per non rivelare quale campo è errato
        user_ok = hmac.compare_digest((user or "").encode(), expected_user)
        pass_ok = hmac.compare_digest((pwd or "").encode(), expected_pass)
        return user_ok and pass_ok

    return check
