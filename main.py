import os
import logging
from typing import Any

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, CallbackContext, ExtBot

from poker_planning import (
    _start_round,
    _vote,
    _reveal_round,
)


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

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

async def send_reveal_keyboard(chat_id : int, context: ContextTypes.DEFAULT_TYPE):
    text = "Завершить раунд можно с помощью кнопки ниже."
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=build_reveal_keyboard())

async def send_start_keyboard(chat_id : int, context: ContextTypes.DEFAULT_TYPE):
    text = "Начать новый раунд можно с помощью кнопки ниже."
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=build_start_keyboard())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type in ("group", "supergroup"):
        text = (
            "Привет! Этот чат используется как комната для покер‑планирования.\n\n"
            "Чтобы запустить раунд, нажми соответствующую кнопку ниже."
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


async def start_round(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    reply = _start_round(chat_id)
    await context.bot.send_message(chat_id=chat_id, text=reply.text, reply_markup=reply.markup)


async def reveal_round(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    message = _reveal_round(chat_id)
    await context.bot.send_message(chat_id=chat_id, text=message)


async def vote(context: ContextTypes.DEFAULT_TYPE, data: str, update: Update):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.full_name
    value = int(data)
    message = _vote(chat_id, user_id, username, value)
    await context.bot.send_message(chat_id=chat_id, text=message)

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    data = query.data or ""

    if data == "start_round":
        await start_round(chat_id, context)
        await send_reveal_keyboard(chat_id, context)
        return

    if data == "reveal":
        await reveal_round(chat_id, context)
        await send_start_keyboard(chat_id, context)
        return

    # остальное трактуем как голосование, callback_data содержит число
    if data.isdigit():
        await vote(context, data, update)
        return


if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found in .env file")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(on_callback))

    application.run_polling()