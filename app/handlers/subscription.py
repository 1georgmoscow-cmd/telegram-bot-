import time
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, cache_ttl: int = 120):
        """
        cache_ttl — время жизни кэша в секундах
        """
        self.cache_ttl = cache_ttl
        self._cache: dict[tuple[str, int], tuple[bool, float]] = {}

    async def is_subscribed(self, bot: Bot, channel_id: str, user_id: int) -> bool:
        """
        Проверка подписки с кэшем и защитой от ошибок Telegram API
        """

        key = (channel_id, user_id)
        now = time.time()

        # 🔥 1. Проверка кэша
        cached = self._cache.get(key)
        if cached:
            subscribed, expires_at = cached
            if now < expires_at:
                return subscribed

        # 🔥 2. Запрос к Telegram API
        try:
            member = await bot.get_chat_member(
                chat_id=channel_id,
                user_id=user_id
            )

            subscribed = member.status in (
                "member",
                "administrator",
                "creator"
            )

        except Exception as e:
            # ⚠️ Важно: НЕ роняем бота
            logger.warning(f"[subscription check failed] {e}")
            subscribed = False

        # 🔥 3. Кэшируем результат
        self._cache[key] = (
            subscribed,
            now + self.cache_ttl
        )

        return subscribed

    def clear_cache(self):
        """
        Очистка кэша (если понадобится вручную)
        """
        self._cache.clear()
