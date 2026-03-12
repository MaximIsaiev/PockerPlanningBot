import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

from poker_planning import (
    start_round,
    vote,
    reveal_round,
    close_room,
)


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        text = (
            "Этот чат будет использован как комната для покер-планирования.\n\n"
            "Основные команды:\n"
            "/start_round — лидер запускает раунд.\n"
            "/vote <значение> — участники голосуют (ряд Фибоначчи до 100).\n"
            "/reveal — лидер показывает результаты текущего раунда.\n"
            "/close — лидер закрывает комнату в этом чате."
        )
    else:
        text = (
            "Привет! Я бот для покер-планирования.\n\n"
            "Чтобы использовать меня, добавьте бота в групповой чат команды и "
            "в этом чате выполните команду /start.\n"
            "После этого используйте команды /start_round, /vote, /reveal и /close."
        )

    await context.bot.send_message(chat_id=chat.id, text=text)


def _ensure_group_chat(update: Update) -> bool:
    chat_type = update.effective_chat.type
    return chat_type in ("group", "supergroup")


async def start_round_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _ensure_group_chat(update):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Команда /start_round доступна только в групповых чатах.",
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    keyboard = start_round(chat_id, user_id)
    await update.message.reply_text(keyboard.text, reply_markup=keyboard.markup)


async def vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Всегда вызывайте answer() для callback (так сказал deepseek)

    if not _ensure_group_chat(update):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Голосовать можно только в групповых чатах.",
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    message = vote(chat_id, user_id, username, int(query.data))
    await context.bot.send_message(chat_id=chat_id, text=message)


async def reveal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _ensure_group_chat(update):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Команда /reveal доступна только в групповых чатах.",
        )
        return

    chat_id = update.effective_chat.id

    user_names: dict[int, str] = {
        update.effective_user.id: update.effective_user.full_name
    }

    message = reveal_round(chat_id, user_names)
    await context.bot.send_message(chat_id=chat_id, text=message)


async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _ensure_group_chat(update):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Команда /close доступна только в групповых чатах.",
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message = close_room(chat_id, user_id)
    await context.bot.send_message(chat_id=chat_id, text=message)


if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found in .env file")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_round", start_round_cmd))
    application.add_handler(CommandHandler("reveal", reveal_cmd))
    application.add_handler(CommandHandler("close", close_cmd))
    application.add_handler(CallbackQueryHandler(vote_callback))

    application.run_polling()