import os
import shutil
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
import music_service
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
            "Пожалуйста, укажите токен в файле .env или переменной окружения BOT_TOKEN."
        )
        sys.exit(1)

    # Clean previous temporary downloads if any
    downloads_dir = music_service.DOWNLOADS_DIR
    if os.path.exists(downloads_dir):
        for f in os.listdir(downloads_dir):
            fp = os.path.join(downloads_dir, f)
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
            except Exception:
                pass

    logger.info("Запуск MusicFlow Bot...")
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    # Clear pending webhook updates
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Музыкальный бот успешно запущен и ожидает поисковых запросов!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Музыкальный бот остановлен.")
