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
    leader_id: int
    active_round: Optional[Round] = None
    is_closed: bool = False

@dataclass
class KeyboardMarkupReply:
    text: str
    markup: Optional[InlineKeyboardMarkup] = None



rooms_by_chat: Dict[int, Room] = {}


def validate_card_value(value: int) -> bool:
    return value in FIBONACCI_CARDS


def calculate_average(votes: Dict[int, int]) -> float:
    if not votes:
        return 0.0
    return sum(votes.values()) / len(votes)


def get_or_create_room(chat_id: int, initiator_id: int) -> Room:
    room = rooms_by_chat.get(chat_id)
    if room and not room.is_closed:
        return room

    room = Room(chat_id=chat_id, leader_id=initiator_id)
    rooms_by_chat[chat_id] = room
    return room


def start_round(chat_id: int, user_id: int) -> KeyboardMarkupReply:
    room = get_or_create_room(chat_id, user_id)

    if room.is_closed:
        return KeyboardMarkupReply("Комната в этом чате уже закрыта.")

    if room.leader_id != user_id:
        return KeyboardMarkupReply("Только лидер этой комнаты может запускать раунд.")

    room.active_round = Round()

    keyboard = []
    for card in FIBONACCI_CARDS:
        keyboard.append([InlineKeyboardButton(str(card), callback_data=card)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    cards_str = ", ".join(str(v) for v in FIBONACCI_CARDS)
    reply_text = ("Новый раунд покер-планирования начат.\n"
        f"Участники, выберите карту командой /vote <значение>.\n"
        f"Доступные значения: {cards_str}.")

    return KeyboardMarkupReply(text=reply_text, markup=reply_markup)


def vote(chat_id: int, user_id: int, username: str, card_value: int) -> str:
    room = rooms_by_chat.get(chat_id)
    if not room or room.is_closed:
        return "В этом чате сейчас нет активной комнаты для покер-планирования."

    # if user_id == room.leader_id:
    #     return "Лидер комнаты не участвует в голосовании."

    if not room.active_round:
        return "Сейчас нет активного раунда. Ожидайте, пока лидер запустит новый раунд командой /start_round."

    if room.active_round.is_finished:
        return "Текущий раунд уже завершён. Начните новый раунд командой /start_round."

    if not validate_card_value(card_value):
        cards_str = ", ".join(str(v) for v in FIBONACCI_CARDS)
        return (
            f"Некорректное значение карты. Допустимые значения: {cards_str}.\n"
            "Пример: /vote 5"
        )

    room.active_round.votes[user_id] = card_value
    room.active_round.participants[user_id] = username

    return f"Участник: {username} проголосовал(а)."


def reveal_round(chat_id: int) -> str:
    room = rooms_by_chat.get(chat_id)
    if not room or not room.active_round:
        return "Сейчас нет активного раунда для показа результатов."

    if room.active_round.is_finished:
        return "Текущий раунд уже завершён. Начните новый раунд командой /start_round."

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


def close_room(chat_id: int, user_id: int) -> str:
    room = rooms_by_chat.get(chat_id)
    if not room:
        return "В этом чате ещё не было создано комнаты для покер-планирования."

    if room.leader_id != user_id:
        return "Только лидер этой комнаты может её закрыть."

    if room.is_closed:
        return "Комната уже закрыта."

    room.is_closed = True
    room.active_round = None

    return "Комната для покер-планирования в этом чате закрыта. Для новой игры начните новый раунд командой /start_round."

