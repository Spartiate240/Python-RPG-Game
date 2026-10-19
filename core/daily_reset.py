"""Utilitaires metier pour les resets bases sur le jour civil."""

from __future__ import annotations

from datetime import date, datetime, timedelta


class DailyResetService:
    """Fournit la date courante et detecte le passage a un nouveau jour."""

    @staticmethod
    def today() -> str:
        return date.today().isoformat()

    @classmethod
    def is_new_day(cls, last_reset: str | None) -> bool:
        if not last_reset:
            return False
        try:
            return date.fromisoformat(last_reset) < date.today()
        except ValueError:
            return True

    @staticmethod
    def time_until_reset() -> timedelta:
        tomorrow = date.today() + timedelta(days=1)
        reset_at = datetime.combine(tomorrow, datetime.min.time())
        return reset_at - datetime.now()
