import random

rooms = {}

BOT_NAMES = [
    "Алексей 🕶", "Дмитрий ☕️", "Елена 🦊", "Артём 🎧", 
    "София 👑", "Максим ⚡️", "Виктория 🌸", "Игорь 🎲"
]

def create_room(chat_id, user):
    rooms[chat_id] = {
        "host_id": user.id,
        "players": [
            {
                "id": user.id,
                "name": user.full_name,
                "bot": False,
                "alive": True,
                "role": None
            }
        ],
        "started": False,
        "phase": "lobby",
        "night": {},
        "day": {}
    }

def join_room(chat_id, user):
    if chat_id not in rooms:
        return False, "❌ Игра ещё не создана!"

    room = rooms[chat_id]
    if room["started"]:
        return False, "❌ Игра уже идёт!"

    for player in room["players"]:
        if player["id"] == user.id:
            return False, "❌ Вы уже в игре!"

    room["players"].append({
        "id": user.id,
        "name": user.full_name,
        "bot": False,
        "alive": True,
        "role": None
    })
    return True, "✅ Вы успешно присоединились!"

def add_bot(chat_id):
    if chat_id not in rooms:
        return False

    room = rooms[chat_id]
    if room["started"]:
        return False

    used_names = [p["name"] for p in room["players"]]
    available_names = [n for n in BOT_NAMES if n not in used_names]
    
    bot_name = random.choice(available_names) if available_names else f"Бот {len(room['players'])}"
    bot_id = -len(room["players"]) - 100

    room["players"].append({
        "id": bot_id,
        "name": bot_name,
        "bot": True,
        "alive": True,
        "role": None
    })
    return True

def get_room(chat_id):
    return rooms.get(chat_id)