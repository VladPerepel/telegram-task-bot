import os
import random
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.enums import ChatAction

import music_service
from keyboards import get_main_keyboard, get_search_results_keyboard

logger = logging.getLogger(__name__)
router = Router()

RANDOM_ARTISTS = [
    "Eminem", "Miyagi", "The Weeknd", "Queen", "Linkin Park",
    "Imagine Dragons", "Daft Punk", "Billie Eilish", "Nirvana",
    "Michael Jackson", "Coldplay", "Macan", "Artik & Asti", "Hans Zimmer"
]


# --- START & HELP ---

@router.message(CommandStart())
async def cmd_start(message: Message):
    first_name = message.from_user.first_name if message.from_user else "друг"
    text = (
        f"🎧 Привет, {first_name}!\n\n"
        "Я **MusicFlow Bot** — твой персональный поиск музыки в Telegram!\n\n"
        "🔎 **Как искать музыку:**\n"
        "Просто отправь мне название любой песни или имя исполнителя "
        "(например: `Miyagi`, `Eminem`, `Numb`, `Queen`).\n\n"
        "Нажимай кнопку под результатом, и я мгновенно пришлю аудиозапись! 🎶"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@router.message(F.text == "ℹ️ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "💡 **Инструкция по использованию:**\n\n"
        "1. Напиши в чат название трека или автора (например: `Believer` или `Macan`).\n"
        "2. Бот выдаст список найденных треков с их длительностью.\n"
        "3. Нажми на кнопку нужного трека — бот загрузит MP3 прямо в чат с плеером Telegram!\n\n"
        "Каждый трек можно слушать онлайн, пересылать друзьям или сохранять в кэш Telegram."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())


# --- QUICK SUGGESTIONS ---

@router.message(F.text == "🔥 Популярная музыка")
async def cmd_popular(message: Message):
    await search_and_respond(message, "Top Hits 2024")


@router.message(F.text == "🎲 Случайный хит")
async def cmd_random_hit(message: Message):
    artist = random.choice(RANDOM_ARTISTS)
    await search_and_respond(message, artist)


# --- GENERAL TEXT SEARCH ---

async def search_and_respond(message: Message, query: str):
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    status_msg = await message.answer(f"🔍 Ищу треки по запросу: *{query}*...", parse_mode="Markdown")

    tracks = await music_service.search_tracks(query, limit=6)

    if not tracks:
        await status_msg.edit_text(
            f"😔 К сожалению, по запросу *{query}* ничего не найдено.\n"
            "Попробуй изменить название или имя исполнителя.",
            parse_mode="Markdown"
        )
        return

    lines = [f"🎵 **Результаты поиска:** *{query}*\n"]
    for idx, t in enumerate(tracks, start=1):
        lines.append(f"**{idx}.** {t['title']} `[{t['duration_str']}]`")
    lines.append("\n_Нажми на кнопку ниже, чтобы получить трек:_")

    reply_markup = get_search_results_keyboard(tracks)
    await status_msg.edit_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)


@router.message(F.text)
async def handle_text_search(message: Message):
    query = message.text.strip()
    if not query:
        return
    await search_and_respond(message, query)


# --- CALLBACK QUERY: DOWNLOAD & SEND TRACK ---

@router.callback_query(F.data.startswith("play:"))
async def cb_play_track(callback: CallbackQuery):
    track_id = callback.data.split(":")[1]
    await callback.answer("⏳ Скачиваю и подготавливаю трек...", show_alert=False)

    chat_id = callback.message.chat.id
    await callback.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)

    progress_msg = await callback.message.reply("⚡️ Загрузка аудио... Пожалуйста, подожди несколько секунд.")

    try:
        track_info = await music_service.download_track(track_id)
        if not track_info or not os.path.exists(track_info["file_path"]):
            await progress_msg.edit_text("❌ Не удалось загрузить данный трек. Попробуй выбрать другой вариант из списка.")
            return

        file_path = track_info["file_path"]
        title = track_info["title"]
        performer = track_info["performer"]
        duration = track_info["duration"]

        audio_file = FSInputFile(file_path, filename=f"{title}.mp3")

        await callback.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        await callback.message.answer_audio(
            audio=audio_file,
            title=title,
            performer=performer,
            duration=duration,
            caption="🎶 Приятного прослушивания!"
        )

        await progress_msg.delete()

        # Clean up downloaded file to prevent filling disk
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error removing temporary file {file_path}: {e}")

    except Exception as exc:
        logger.error(f"Error sending audio: {exc}")
        await progress_msg.edit_text("⚠️ Ошибка при обработке аудио. Попробуй еще раз позже.")
