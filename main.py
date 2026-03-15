import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

from poker_planning import (
    start_round,
    vote,
    reveal_round,
)


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def _ensure_group_chat(update: Update) -> bool:
    return update.effective_chat.type in ("group", "supergroup")

def build_start_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("Начать раунд", callback_data="start_round"),
        ]
    ]

    return InlineKeyboardMarkup(buttons)


def build_reveal_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("Показать результаты", callback_data="reveal"),
        ]
    ]

    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type in ("group", "supergroup"):
        text = (
            "Привет! Этот чат используется как комната для покер‑планирования.\n\n"
            "Чтобы запустить раунд, нажми соответсвующую кнопку ниже."
        )
        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=build_start_keyboard(),
        )
    else:
        text = (
            "Привет! Я бот для покер‑планирования.\n\n"
            "Чтобы начать, добавьте меня в групповой чат вашей команды и "
            "в этом чате отправьте команду /start."
        )
        await context.bot.send_message(chat_id=chat.id, text=text)


async def start_round_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _ensure_group_chat(update):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Команда /start_round доступна только в групповых чатах.",
        )
        return

    chat_id = update.effective_chat.id
    reply = start_round(chat_id)
    await context.bot.send_message(chat_id=chat_id, text=reply.text, reply_markup=reply.markup)

    text = "Завершить раунд можно с помощью кнопки ниже."
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=build_reveal_keyboard())


async def reveal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _ensure_group_chat(update):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Команда /reveal доступна только в групповых чатах.",
        )
        return

    chat_id = update.effective_chat.id
    message = reveal_round(chat_id)
    await context.bot.send_message(chat_id=chat_id, text=message)

    text = "Начать новый раунд можно с помощью кнопки ниже."
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=build_start_keyboard())


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not _ensure_group_chat(update):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Кнопки доступны только в групповых чатах.",
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = query.data or ""

    if data == "start_round":
        reply = start_round(chat_id)
        await context.bot.send_message(chat_id=chat_id, text=reply.text, reply_markup=reply.markup)
        return

    if data == "reveal":
        message = reveal_round(chat_id)
        await context.bot.send_message(chat_id=chat_id, text=message)
        return

    # остальное трактуем как голосование, callback_data содержит число
    if data.isdigit():
        value = int(data)
        username = update.effective_user.full_name
        message = vote(chat_id, user_id, username, value)
        await context.bot.send_message(chat_id=chat_id, text=message)
        return


if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found in .env file")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start_round", start_round_cmd))
    application.add_handler(CommandHandler("reveal", reveal_cmd))
    application.add_handler(CallbackQueryHandler(on_callback))

    application.run_polling()