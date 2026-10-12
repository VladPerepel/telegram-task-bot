from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import List, Dict, Any


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Returns the persistent main menu keyboard."""
    keyboard = [
        [
            KeyboardButton(text="📋 Мои задачи"),
            KeyboardButton(text="➕ Новая задача"),
        ],
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="📜 Выполненные"),
        ],
        [
            KeyboardButton(text="ℹ️ Помощь"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Returns a keyboard with a single Cancel button for FSM dialogs."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def get_task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Inline buttons to complete or delete an individual task."""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Завершить", callback_data=f"done:{task_id}"
            ),
            InlineKeyboardButton(
                text="🗑 Удалить", callback_data=f"del:{task_id}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tasks_list_inline_keyboard(tasks: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Builds inline action buttons for a list of active tasks."""
    rows = []
    for idx, task in enumerate(tasks, start=1):
        task_id = task["id"]
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✅ #{idx}", callback_data=f"done:{task_id}"
                ),
                InlineKeyboardButton(
                    text=f"🗑 #{idx}", callback_data=f"del:{task_id}"
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Добавить ещё задачу", callback_data="btn_add_task"
            ),
            InlineKeyboardButton(
                text="🔄 Обновить список", callback_data="refresh_tasks"
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
