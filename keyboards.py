from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import List, Dict, Any


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard for the music bot."""
    keyboard = [
        [
            KeyboardButton(text="🔥 Популярная музыка"),
            KeyboardButton(text="🎲 Случайный хит"),
        ],
        [
            KeyboardButton(text="ℹ️ Помощь"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Напиши название песни или артиста...",
    )


def get_search_results_keyboard(tracks: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Builds inline buttons for each found music track."""
    buttons = []
    for idx, track in enumerate(tracks, start=1):
        track_id = track["id"]
        # Format title cleanly
        raw_title = track["title"]
        if len(raw_title) > 36:
            display_title = raw_title[:33] + "..."
        else:
            display_title = raw_title

        dur = track.get("duration_str", "")
        label = f"▶️ {idx}. {display_title} [{dur}]"

        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"play:{track_id}")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
