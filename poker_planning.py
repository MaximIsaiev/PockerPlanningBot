from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple, List
import random
import string


FIBONACCI_CARDS: List[int] = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


@dataclass
class Round:
    votes: Dict[int, int] = field(default_factory=dict)
    is_finished: bool = False


@dataclass
class Room:
    code: str
    leader_id: int
    members: Set[int] = field(default_factory=set)
    active_round: Optional[Round] = None
    is_closed: bool = False


rooms_by_code: Dict[str, Room] = {}
user_to_room: Dict[int, str] = {}


def generate_room_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if code not in rooms_by_code:
            return code


def validate_card_value(value: int) -> bool:
    return value in FIBONACCI_CARDS


def calculate_average(votes: Dict[int, int]) -> float:
    if not votes:
        return 0.0
    return sum(votes.values()) / len(votes)


def _get_room_for_leader(leader_id: int) -> Optional[Room]:
    code = user_to_room.get(leader_id)
    if not code:
        return None
    room = rooms_by_code.get(code)
    if room and room.leader_id == leader_id:
        return room
    return None


def _get_room_for_user(user_id: int) -> Optional[Room]:
    code = user_to_room.get(user_id)
    if not code:
        return None
    return rooms_by_code.get(code)


def create_room(leader_id: int) -> Tuple[Optional[Room], str]:
    existing_room = _get_room_for_leader(leader_id)
    if existing_room and not existing_room.is_closed:
        return existing_room, (
            f"Вы уже являетесь лидером комнаты с кодом {existing_room.code}.\n"
            f"Отправьте этот код участникам, чтобы они присоединились командой /join {existing_room.code}."
        )

    if leader_id in user_to_room and not existing_room:
        return None, (
            "Вы уже состоите в комнате как участник.\n"
            "Сначала выйдите из текущей комнаты или попросите лидера закрыть её."
        )

    code = generate_room_code()
    room = Room(code=code, leader_id=leader_id)
    rooms_by_code[code] = room
    user_to_room[leader_id] = code

    message = (
        f"Комната создана. Ваш код: {code}\n"
        "Отправьте этот код участникам, чтобы они присоединились командой /join <код>.\n"
        "Когда все участники присоединятся, начните раунд командой /start_round."
    )
    return room, message


def join_room(user_id: int, code: str) -> str:
    code = code.strip().upper()
    room = rooms_by_code.get(code)

    if not room:
        return "Комната с таким кодом не найдена."

    if room.is_closed:
        return "Эта комната уже закрыта. Попросите лидера создать новую."

    if user_id == room.leader_id:
        return "Вы являетесь лидером этой комнаты и не можете присоединиться как участник."

    current_room = _get_room_for_user(user_id)
    if current_room and current_room.code != code:
        return (
            "Вы уже состоите в другой комнате.\n"
            "Сначала выйдите из неё или попросите лидера закрыть её."
        )

    if user_id in room.members:
        return "Вы уже присоединились к этой комнате."

    room.members.add(user_id)
    user_to_room[user_id] = code

    return (
        f"Вы присоединились к комнате {code}.\n"
        "Ожидайте, пока лидер запустит раунд покер-планирования командой /start_round."
    )


def start_round(leader_id: int) -> str:
    room = _get_room_for_leader(leader_id)
    if not room:
        return "Вы не являетесь лидером ни одной активной комнаты."

    if room.is_closed:
        return "Комната уже закрыта. Создайте новую комнату командой /create."

    if not room.members:
        return "В комнате нет участников. Попросите коллег присоединиться командой /join <код>."

    room.active_round = Round()

    cards_str = ", ".join(str(v) for v in FIBONACCI_CARDS)
    return (
        "Новый раунд покер-планирования начат.\n"
        f"Участники, выберите карту командой /vote <значение>.\n"
        f"Доступные значения: {cards_str}."
    )


def vote(user_id: int, card_value: int) -> str:
    room = _get_room_for_user(user_id)
    if not room or room.is_closed:
        return "Вы не состоите ни в одной активной комнате."

    if user_id == room.leader_id:
        return "Лидер комнаты не участвует в голосовании."

    if user_id not in room.members:
        return "Вы не являетесь участником комнаты."

    if not room.active_round or room.active_round.is_finished:
        return "Сейчас нет активного раунда. Ожидайте, пока лидер запустит новый раунд командой /start_round."

    if not validate_card_value(card_value):
        cards_str = ", ".join(str(v) for v in FIBONACCI_CARDS)
        return (
            f"Некорректное значение карты. Допустимые значения: {cards_str}.\n"
            "Пример: /vote 5"
        )

    room.active_round.votes[user_id] = card_value

    return "Ваш голос принят."


def finish_round_if_completed(code: str, user_names: Dict[int, str]) -> Optional[str]:
    room = rooms_by_code.get(code)
    if not room or not room.active_round or room.active_round.is_finished:
        return None

    if len(room.active_round.votes) < len(room.members):
        return None

    room.active_round.is_finished = True

    votes = room.active_round.votes
    avg = calculate_average(votes)

    lines = ["Раунд завершён. Результаты:"]
    for uid, value in votes.items():
        name = user_names.get(uid, str(uid))
        lines.append(f"- {name}: {value}")

    lines.append(f"\nСреднее значение: {avg:.2f}")

    return "\n".join(lines)


def close_room(leader_id: int) -> str:
    room = _get_room_for_leader(leader_id)
    if not room:
        return "Вы не являетесь лидером ни одной активной комнаты."

    if room.is_closed:
        return "Комната уже закрыта."

    room.is_closed = True

    # очистить привязки пользователей к комнате
    for uid in list(room.members) + [room.leader_id]:
        if user_to_room.get(uid) == room.code:
            user_to_room.pop(uid, None)

    return "Комната закрыта. Для новой игры создайте новую комнату командой /create."

