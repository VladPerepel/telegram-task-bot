import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
import database
from handlers import router


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error(
            "❌ ОШИБКА: BOT_TOKEN не задан!\n"
            "Пожалуйста, создайте бота через @BotFather в Telegram, "
            "получите токен и укажите его в файле .env или переменной окружения BOT_TOKEN."
        )
        sys.exit(1)

    logger.info("Инициализация базы данных...")
    database.init_db()

    logger.info("Запуск TaskFlow Bot...")
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    # Delete webhook to make sure polling doesn't conflict
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот успешно запущен и ожидает сообщений!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
