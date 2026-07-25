import random

# Пул уникальных реплик для ботов, чтобы они говорили разное и не повторялись
BOT_PHRASES = [
    "Мне кажется, ночью кто-то слишком подозрительно себя вел... Нужно присмотреться к тихим игрокам.",
    "Серьезно, прошлой ночью было жарковато. У меня есть пара кандидатур на проверку.",
    "Я всю ночь настраивал системы и следил за логами. Тут явно замешан кто-то из новичков.",
    "Спокойно, граждане! Главное — не паниковать и рассуждать логически.",
    "Кто-то явно пытается отвести от себя подозрения. Давайте вспомним, кто голосовал против прошлым днем.",
    "Мои датчики зафиксировали странную активность возле секторов мирных жителей.",
    "Я бы не доверял тем, кто сидит молча весь раунд и ничего не предлагает.",
    "Если мы сейчас ошибемся, синдикат захватит полный контроль над сетью!",
    "Интересный расклад... Давайте проанализируем, кому была выгодна прошлая смерть.",
    "Среди нас точно есть шпион. Я чувствую это по сетевому трафику."
]

def generate_bot_name(existing_players):
    names = [
        "CyberNinja", "NeonHacker", "GlitchZero", "ByteGhost", 
        "DataPhantom", "VortexAI", "SystemX", "NullPointer", 
        "RootAdmin", "CoreMatrix", "EchoBot", "CipherUnit"
    ]
    existing_names = [p["name"] for p in existing_players]
    available_names = [n for n in names if n not in existing_names]
    
    if not available_names:
        return f"Bot_{len(existing_players) + 1}"
    
    return random.choice(available_names)


def start_game(room):
    players = room["players"]
    num_players = len(players)
    
    # Распределение ролей в зависимости от количества игроков
    # 3-4 игрока: 1 мафия, 1 доктор, 1 комиссар, остальные мирные
    # 5+ игроков: пропорционально
    roles = ["Мафия", "Доктор", "Комиссар"]
    
    while len(roles) < num_players:
        roles.append("Мирный житель")
        
    random.shuffle(roles)
    
    for i, player in enumerate(players):
        player["role"] = roles[i]
        player["alive"] = True


def get_role_card(role: str) -> str:
    cards = {
        "Мафия": (
            "🔪 <b>ВАША РОЛЬ: МАФИЯ (СИНДИКАТ)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Ваша цель — устранить всех мирных граждан и захватить контроль над сетью. Каждую ночь вы выбираете жертву. Не выдавайте себя днем!</i>"
        ),
        "Доктор": (
            "🩺 <b>ВАША РОЛЬ: ДОКТОРА (МЕДИК)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Ваша цель — защищать участников системы. Каждую ночь вы можете выбрать одного игрока (включая себя), чтобы спасти его от ликвидации.</i>"
        ),
        "Комиссар": (
            "🕵️‍♂️ <b>ВАША РОЛЬ: КОМИССАР (ОПЕРАТИВНИК)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Ваша задача — искать агентов синдиката. Каждую ночь вы можете проверить статус любого игрока и узнать, мафия он или мирный.</i>"
        ),
        "Мирный житель": (
            "🌾 <b>ВАША РОЛЬ: МИРНЫЙ ЖИТЕЛЬ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Вы обычный оператор сети. Ваша главная сила — обсуждения, логика и дневной трибунал. Вычислите и изгоните всю мафию!</i>"
        )
    }
    return cards.get(role, "🎮 Ваша роль засекречена.")


def save_kill(room, target_id):
    room["night"]["kill"] = target_id


def save_heal(room, target_id):
    room["night"]["heal"] = target_id


def save_check(room, target_id):
    room["night"]["check"] = target_id


def bot_night_action(room):
    # Автоматический выбор мафии-бота
    alive_players = [p for p in room["players"] if p["alive"]]
    non_mafia = [p for p in alive_players if p["role"] != "Мафия"]
    if non_mafia:
        target = random.choice(non_mafia)
        room["night"]["kill"] = target["id"]


def finish_night(room):
    night = room["night"]
    killed_id = night["kill"]
    healed_id = night["heal"]
    
    dead_player = None
    
    if killed_id and killed_id != healed_id:
        for player in room["players"]:
            if player["id"] == killed_id and player["alive"]:
                player["alive"] = False
                dead_player = player
                break
                
    winner = check_winner(room)
    return dead_player, winner


def save_vote(room, voter_id, target_id):
    room["day"]["votes"][voter_id] = target_id


def bot_vote(room):
    alive_players = [p for p in room["players"] if p["alive"]]
    alive_bots = [p for p in alive_players if p.get("bot")]
    
    for bot in alive_bots:
        # Боты выбирают случайную живую жертву для дневного голосования (исключая себя)
        possible_targets = [p for p in alive_players if p["id"] != bot["id"]]
        if possible_targets:
            target = random.choice(possible_targets)
            room["day"]["votes"][bot["id"]] = target["id"]


def end_day(room):
    votes = room["day"]["votes"]
    if not votes:
        room["day"]["votes"] = {}
        return None, {}
        
    vote_counts = {}
    for voter_id, target_id in votes.items():
        vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
        
    # Сбрасываем голоса для следующего дня
    room["day"]["votes"] = {}
    
    if not vote_counts:
        return None, {}
        
    max_votes = max(vote_counts.values())
    top_targets = [t_id for t_id, count in vote_counts.items() if count == max_votes]
    
    # Если за лидера голосов больше одного (ничья), никто не выбывает
    if len(top_targets) > 1:
        return None, vote_counts
        
    kicked_id = top_targets[0]
    kicked_player = None
    
    for player in room["players"]:
        if player["id"] == kicked_id and player["alive"]:
            player["alive"] = False
            kicked_player = player
            break
            
    return kicked_player, vote_counts


def check_winner(room):
    alive_players = [p for p in room["players"] if p["alive"]]
    
    mafia_count = sum(1 for p in alive_players if p["role"] == "Мафия")
    peaceful_count = len(alive_players) - mafia_count
    
    if mafia_count == 0:
        return "peaceful"
    elif mafia_count >= peaceful_count:
        return "mafia"
        
    return None


def get_formatted_player_list(room) -> str:
    text = "📋 <b>АКТУАЛЬНЫЙ СТАТУС СЕТИ:</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for p in room["players"]:
        status = "🟢 В сети" if p["alive"] else "💀 Утрачен"
        text += f"• <b>{p['name']}</b> — {status}\n"
    return text


async def get_bot_chat_messages(room):
    alive_bots = [p for p in room["players"] if p.get("bot") and p["alive"]]
    if not alive_bots:
        return []
    
    # Выбираем от 2 до 3 случайных ботов для утренней беседы, чтобы они говорили по очереди
    num_speakers = min(len(alive_bots), random.randint(2, 3))
    speaking_bots = random.sample(alive_bots, num_speakers)
    
    messages = []
    used_phrases = set()
    
    for bot in speaking_bots:
        available_phrases = [p for p in BOT_PHRASES if p not in used_phrases]
        if not available_phrases:
            available_phrases = BOT_PHRASES
            
        phrase = random.choice(available_phrases)
        used_phrases.add(phrase)
        
        messages.append((bot["name"], phrase))
        
    return messages