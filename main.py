import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from poker_planning import (
    create_room,
    join_room,
    start_round,
    vote,
    close_room,
    user_to_room,
    finish_round_if_completed,
)


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привет! Я бот для покер-планирования.\n\n"
        "Основные команды:\n"
        "/create — создать комнату и стать её лидером.\n"
        "/join <код> — присоединиться к комнате по коду лидера.\n\n"
        "Лидер запускает раунды командой /start_round, участники голосуют /vote <значение>,\n"
        "а по завершении лидер может закрыть комнату командой /close."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def create_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    room, message = create_room(user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Использование: /join <код комнаты>.",
        )
        return

    code = context.args[0]
    message = join_room(user_id, code)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def start_round_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = start_round(user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def vote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Использование: /vote <значение>.",
        )
        return

    try:
        value = int(context.args[0])
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Значение должно быть числом. Пример: /vote 5",
        )
        return

    message = vote(user_id, value)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    # если голос принят, проверяем, завершён ли раунд
    code = user_to_room.get(user_id)
    if not code:
        return

    # собираем имена пользователей для красивого вывода
    chat = update.effective_chat
    user_names: dict[int, str] = {}

    # в простом варианте используем только имя текущего пользователя,
    # а остальных выводим по ID — улучшить можно позже через хранение имён
    user_names[user_id] = update.effective_user.full_name

    results_text = finish_round_if_completed(code, user_names)
    if results_text:
        await context.bot.send_message(chat_id=chat.id, text=results_text)


async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = close_room(user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found in .env file")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_cmd))
    application.add_handler(CommandHandler("join", join_cmd))
    application.add_handler(CommandHandler("start_round", start_round_cmd))
    application.add_handler(CommandHandler("vote", vote_cmd))
    application.add_handler(CommandHandler("close", close_cmd))

    application.run_polling()