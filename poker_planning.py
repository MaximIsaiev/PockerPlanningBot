from dataclasses import dataclass, field
from typing import Dict, Optional, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

FIBONACCI_CARDS: List[int] = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


@dataclass
class Round:
    votes: Dict[int, int] = field(default_factory=dict)
    is_finished: bool = False
    participants: Dict[int, str] = field(default_factory=dict)


@dataclass
class Room:
    chat_id: int
    active_round: Optional[Round] = None


@dataclass
class KeyboardMarkupReply:
    text: str
    markup: Optional[InlineKeyboardMarkup] = None


rooms_by_chat: Dict[int, Room] = {}


def get_fibonacci_cards() -> List[int]:
    return list(FIBONACCI_CARDS)


def validate_card_value(value: int) -> bool:
    return value in FIBONACCI_CARDS


def calculate_average(votes: Dict[int, int]) -> float:
    if not votes:
        return 0.0
    return sum(votes.values()) / len(votes)


def get_or_create_room(chat_id: int) -> Room:
    room = rooms_by_chat.get(chat_id)
    if room:
        return room

    room = Room(chat_id=chat_id)
    rooms_by_chat[chat_id] = room
    return room


def start_round(chat_id: int) -> KeyboardMarkupReply:
    room = get_or_create_room(chat_id)

    if room.active_round:
        return KeyboardMarkupReply("Чтобы начать новый раунд, сначала завершите текущий.")

    room.active_round = Round()

    keyboard = [
        [InlineKeyboardButton(str(card), callback_data=str(card))]
        for card in FIBONACCI_CARDS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    reply_text = (
        "Новый раунд покер‑планирования начат.\n"
        "Выберите карту, нажав одну из кнопок ниже."
    )

    return KeyboardMarkupReply(text=reply_text, markup=reply_markup)


def vote(chat_id: int, user_id: int, username: str, card_value: int) -> str:
    room = rooms_by_chat.get(chat_id)

    if not room.active_round:
        return "Сейчас нет активного раунда. Попросите лидера запустить новый раунд."

    if room.active_round.is_finished:
        return "Текущий раунд уже завершён. Начните новый раунд перед голосованием."

    if not validate_card_value(card_value):
        cards_str = ", ".join(str(v) for v in FIBONACCI_CARDS)
        return f"Некорректное значение карты. Допустимые значения: {cards_str}."

    room.active_round.votes[user_id] = card_value
    room.active_round.participants[user_id] = username

    return f"Голос участника {username} принят."


def reveal_round(chat_id: int) -> str:
    room = rooms_by_chat.get(chat_id)
    if not room or not room.active_round:
        return "Сейчас нет активного раунда для показа результатов."

    if room.active_round.is_finished:
        return "Текущий раунд уже завершён. Запустите новый, чтобы продолжить оценку."

    votes = room.active_round.votes
    if not votes:
        return "Никто ещё не проголосовал в этом раунде."

    room.active_round.is_finished = True

    avg = calculate_average(votes)

    lines = ["Раунд завершён. Результаты:"]
    for uid, value in votes.items():
        name = room.active_round.participants.get(uid, str(uid))
        lines.append(f"- {name}: {value}")

    lines.append(f"\nСреднее значение: {avg:.2f}")

    return "\n".join(lines)
