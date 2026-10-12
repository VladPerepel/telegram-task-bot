from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import database
from keyboards import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_tasks_list_inline_keyboard,
)

router = Router()


class TaskStates(StatesGroup):
    waiting_for_title = State()


# --- START & HELP ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    first_name = message.from_user.first_name if message.from_user else "друг"
    text = (
        f"👋 Привет, {first_name}!\n\n"
        "Я **TaskFlow Bot** — твой персональный менеджер задач и привычек.\n\n"
        "✨ **Что я умею:**\n"
        "• Сохранять твои задачи и цели\n"
        "• Отмечать выполненные дела в один клик\n"
        "• Вести статистику твоей продуктивности\n\n"
        "Выбери действие в меню ниже или нажми **➕ Новая задача**!"
    )
    await message.answer(
        text, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )


@router.message(F.text == "ℹ️ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "💡 **Как пользоваться ботом:**\n\n"
        "• **📋 Мои задачи** — просмотр активных дел с быстрыми кнопками завершения и удаления.\n"
        "• **➕ Новая задача** — добавить дело в список.\n"
        "• **📊 Статистика** — процент выполненных задач и сводка.\n"
        "• **📜 Выполненные** — последние завершённые задачи.\n\n"
        "**Команды в чате:**\n"
        "/tasks — список задач\n"
        "/add — быстро добавить задачу\n"
        "/stats — статистика"
    )
    await message.answer(
        text, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )


# --- CANCEL FSM ---

@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.", reply_markup=get_main_keyboard()
    )


# --- ADD TASK ---

@router.message(F.text == "➕ Новая задача")
@router.message(Command("add"))
async def add_task_start(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_title)
    await message.answer(
        "✍️ Напиши название задачи или цели:\n\n_(Или нажми «❌ Отмена»)_",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard(),
    )


@router.callback_query(F.data == "btn_add_task")
async def cb_add_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_title)
    await callback.message.answer(
        "✍️ Введи текст новой задачи:",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(TaskStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext):
    title = message.text.strip() if message.text else ""
    if not title:
        await message.answer("Текст задачи не может быть пустым. Попробуй снова:")
        return

    user_id = message.from_user.id
    task_id = database.add_task(user_id=user_id, title=title)
    await state.clear()

    await message.answer(
        f"✅ Задача #{task_id} сохранена:\n**{title}**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )


# --- LIST TASKS ---

def render_tasks_text(tasks: list) -> str:
    if not tasks:
        return "🎉 **Все задачи выполнены!**\n\nСписок пуст. Нажми **➕ Новая задача**, чтобы записать дела."
    lines = ["📋 **Твои активные задачи:**\n"]
    for idx, t in enumerate(tasks, start=1):
        lines.append(f"**{idx}.** {t['title']}")
    lines.append("\n_Нажимай кнопки ниже: [✅ #...] чтобы завершить, [🗑 #...] чтобы удалить._")
    return "\n".join(lines)


@router.message(F.text == "📋 Мои задачи")
@router.message(Command("tasks"))
async def show_tasks(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    tasks = database.get_active_tasks(user_id)
    text = render_tasks_text(tasks)
    markup = get_tasks_list_inline_keyboard(tasks) if tasks else None
    await message.answer(text, parse_mode="Markdown", reply_markup=markup)


# --- CALLBACKS (DONE / DELETE / REFRESH) ---

@router.callback_query(F.data.startswith("done:"))
async def cb_complete_task(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    success = database.complete_task(task_id, user_id)

    if success:
        await callback.answer("🎉 Задача выполнена!", show_alert=False)
    else:
        await callback.answer("Задача не найдена или уже завершена.")

    # Update current message
    tasks = database.get_active_tasks(user_id)
    text = render_tasks_text(tasks)
    markup = get_tasks_list_inline_keyboard(tasks) if tasks else None

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass


@router.callback_query(F.data.startswith("del:"))
async def cb_delete_task(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    success = database.delete_task(task_id, user_id)

    if success:
        await callback.answer("🗑 Задача удалена.")
    else:
        await callback.answer("Задача не найдена.")

    tasks = database.get_active_tasks(user_id)
    text = render_tasks_text(tasks)
    markup = get_tasks_list_inline_keyboard(tasks) if tasks else None

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass


@router.callback_query(F.data == "refresh_tasks")
async def cb_refresh_tasks(callback: CallbackQuery):
    user_id = callback.from_user.id
    tasks = database.get_active_tasks(user_id)
    text = render_tasks_text(tasks)
    markup = get_tasks_list_inline_keyboard(tasks) if tasks else None

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        await callback.answer("Обновлено!")
    except Exception:
        await callback.answer("Без изменений.")


# --- STATS ---

@router.message(F.text == "📊 Статистика")
@router.message(Command("stats"))
async def show_stats(message: Message):
    user_id = message.from_user.id
    stats = database.get_user_stats(user_id)

    total = stats["total"]
    active = stats["active"]
    completed = stats["completed"]
    rate = stats["completion_rate"]

    progress_bar_length = 10
    filled = int(round(progress_bar_length * (rate / 100))) if total > 0 else 0
    bar = "🟩" * filled + "⬜" * (progress_bar_length - filled)

    text = (
        "📊 **Твоя статистика продуктивности:**\n\n"
        f"• Всего задач: **{total}**\n"
        f"• Активных: **{active}**\n"
        f"• Завершённых: **{completed}**\n\n"
        f"Прогресс: **{rate}%**\n"
        f"{bar}\n\n"
        "Так держать! 💪"
    )
    await message.answer(text, parse_mode="Markdown")


# --- COMPLETED HISTORY ---

@router.message(F.text == "📜 Выполненные")
async def show_completed_history(message: Message):
    user_id = message.from_user.id
    completed_tasks = database.get_completed_tasks(user_id, limit=10)

    if not completed_tasks:
        await message.answer("У тебя пока нет завершённых задач. Время что-нибудь сделать! 🚀")
        return

    lines = ["📜 **Последние выполненные задачи:**\n"]
    for t in completed_tasks:
        date = t.get("completed_at", "")[:10]
        lines.append(f"✓ {t['title']} _({date})_")

    await message.answer("\n".join(lines), parse_mode="Markdown")
