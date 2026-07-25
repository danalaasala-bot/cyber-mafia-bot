import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode

import game
import stats

router = Router()
rooms = {}

def get_or_create_room(chat_id: int):
    if chat_id not in rooms:
        rooms[chat_id] = {
            "started": False,
            "phase": "lobby",
            "players": [],
            "round": 1,
            "night": {"kill": None, "heal": None, "check": None, "subphase": "mafia"},
            "day": {"votes": {}},
            "history": {"dead_roles": {}, "voting_history": []}
        }
    return rooms[chat_id]


# --- ИНТУИТИВНЫЕ И УДОБНЫЕ КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕹️ Создать игру", callback_data="menu_create_lobby")],
        [InlineKeyboardButton(text="📋 Присоединиться к лобби", callback_data="menu_join_lobby")],
        [InlineKeyboardButton(text="📈 Статистика профиля", callback_data="menu_stats")],
        [InlineKeyboardButton(text="📖 Как играть (Правила)", callback_data="menu_rules")]
    ])


def get_back_to_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_menu")]
    ])


def get_lobby_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🙋‍♂️ Войти в игру", callback_data="join_game")],
        [InlineKeyboardButton(text="🤖 Добавить бота-игрока", callback_data="add_bot")],
        [InlineKeyboardButton(text="🚀 Запустить матч", callback_data="start_game")],
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_menu")]
    ])


def get_target_keyboard(room: dict, current_user_id: int, prefix: str):
    # Исключаем мертвых игроков, а также самого себя (чтобы нельзя было голосовать за себя)
    alive_players = [p for p in room["players"] if p["alive"] and p["id"] != current_user_id]
    buttons = []
    
    for p in alive_players:
        buttons.append(
            InlineKeyboardButton(text=f"👉 {p['name']}", callback_data=f"{prefix}_{p['id']}")
        )

    keyboard = []
    for i in range(0, len(buttons), 2):
        keyboard.append(buttons[i:i+2])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# --- 1. ГЛАВНОЕ МЕНЮ ---

@router.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "🤖 <b>CyberMafiaBot — Главное меню</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Добро пожаловать! Выберите нужный пункт с помощью кнопок ниже:"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery):
    text = (
        "🤖 <b>CyberMafiaBot — Главное меню</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Выберите нужный пункт с помощью кнопок ниже:"
    )
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)


# --- 2. НАВИГАЦИЯ МЕНЮ ---

@router.callback_query(F.data == "menu_create_lobby")
async def cb_create_lobby(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    room = get_or_create_room(chat_id)

    if room["started"]:
        await callback.answer("⚠️ Игра уже идет!", show_alert=True)
        return

    user = callback.from_user
    if not any(p["id"] == user.id for p in room["players"]):
        room["players"].append({
            "id": user.id,
            "name": user.full_name or user.first_name,
            "bot": False
        })

    text = (
        "🎮 <b>Игровое лобби</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Комната создана. Ждем игроков или можете добавить ботов для теста.\n\n"
        f"👥 <b>Игроков в лобби:</b> <b>{len(room['players'])}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_lobby_keyboard(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "menu_join_lobby")
async def cb_menu_join_lobby(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    room = rooms.get(chat_id)

    if not room or room["phase"] == "lobby":
        text = (
            "🎮 <b>Игровое лобби</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Активная комната найдена. Нажмите кнопку ниже, чтобы присоединиться:"
        )
        await callback.message.edit_text(text, reply_markup=get_lobby_keyboard(), parse_mode=ParseMode.HTML)
    else:
        await callback.answer("❌ Сейчас нет открытых комнат. Создайте новую игру!", show_alert=True)


@router.callback_query(F.data == "menu_stats")
async def cb_menu_stats(callback: CallbackQuery):
    user = callback.from_user
    user_data = stats.get_user_stats(user.id)
    
    text = (
        f"📈 <b>Статистика: {user.first_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 Всего матчей: <b>{user_data['games']}</b>\n"
        f"🏆 Побед: <b>{user_data['wins']}</b>\n"
        f"💀 Поражений: <b>{user_data['losses']}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_back_to_menu_keyboard(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "menu_rules")
async def cb_menu_rules(callback: CallbackQuery):
    text = (
        "📖 <b>Правила игры в Мафию</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. 🌙 <b>Ночь:</b> Мафия выбирает жертву, доктор лечит, комиссар проверяет игроков.\n"
        "2. ☀️ <b>День:</b> Все обсуждают события и голосуют на трибунале против подозреваемого.\n"
        "3. 🎯 <b>Цель:</b> Мирные ищут мафию, а мафия пытается захватить контроль."
    )
    await callback.message.edit_text(text, reply_markup=get_back_to_menu_keyboard(), parse_mode=ParseMode.HTML)


# --- 3. ЛОББИ И УПРАВЛЕНИЕ ИГРОКАМИ ---

@router.callback_query(F.data == "join_game")
async def cb_join_game(callback: CallbackQuery):
    room = get_or_create_room(callback.message.chat.id)
    user = callback.from_user

    if room["started"]:
        await callback.answer("⚠️ Игра уже началась!", show_alert=True)
        return

    if any(p["id"] == user.id for p in room["players"]):
        await callback.answer("⚠️ Вы уже за столом!", show_alert=True)
        return

    room["players"].append({
        "id": user.id,
        "name": user.full_name or user.first_name,
        "bot": False
    })

    await callback.answer("✅ Вы успешно вошли в игру!")
    
    text = (
        "🎮 <b>Игровое лобби</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>{user.first_name}</b> присоединился к игре.\n\n"
        f"👥 <b>Игроков в лобби:</b> <b>{len(room['players'])}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_lobby_keyboard(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "add_bot")
async def cb_add_bot(callback: CallbackQuery):
    room = get_or_create_room(callback.message.chat.id)

    if room["started"]:
        await callback.answer("⚠️ Игра уже началась!", show_alert=True)
        return

    bot_id = -len(room["players"]) - 1
    bot_name = game.generate_bot_name(room["players"])

    room["players"].append({
        "id": bot_id,
        "name": bot_name,
        "bot": True
    })

    await callback.answer(f"🤖 Бот {bot_name} добавлен!")

    text = (
        "🎮 <b>Игровое лобби</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Добавлен бот: <b>{bot_name}</b>\n\n"
        f"👥 <b>Игроков в лобби:</b> <b>{len(room['players'])}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_lobby_keyboard(), parse_mode=ParseMode.HTML)


# --- 4. ИГРОВЫЕ ФАЗЫ (НОЧЬ / ДЕНЬ) ---

async def start_night_phase(bot: Bot, chat_id: int, room: dict):
    room["phase"] = "night"
    room["night"]["subphase"] = "mafia"
    room["night"]["kill"] = None
    room["night"]["heal"] = None
    room["night"]["check"] = None

    is_private_chat = room.get("is_private", False)
    mafia_players = [p for p in room["players"] if p["role"] == "Мафия" and p["alive"]]
    
    await bot.send_message(
        chat_id,
        "🌙 <b>Наступила ночь. Город засыпает...</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔪 <i>Мафия выбирает жертву.</i>",
        parse_mode=ParseMode.HTML
    )

    if not mafia_players:
        await asyncio.sleep(2)
        await start_doctor_phase(bot, chat_id, room)
        return

    human_mafia = next((p for p in mafia_players if not p.get("bot")), None)

    if human_mafia:
        kb = get_target_keyboard(room, human_mafia["id"], f"night_kill_{chat_id}")
        target_chat = chat_id if is_private_chat else human_mafia["id"]
        try:
            await bot.send_message(target_chat, "🔪 <b>Ваш ход (Мафия):</b> Выберите цель для устранения:", reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        await asyncio.sleep(3)
        game.bot_night_action(room)
        await start_doctor_phase(bot, chat_id, room)


async def start_doctor_phase(bot: Bot, chat_id: int, room: dict):
    room["night"]["subphase"] = "doctor"
    is_private_chat = room.get("is_private", False)
    doctor_players = [p for p in room["players"] if p["role"] == "Доктор" and p["alive"]]
    
    await bot.send_message(
        chat_id,
        "🌙 <i>Мафия сделала выбор. Просыпается доктор...</i>",
        parse_mode=ParseMode.HTML
    )

    if not doctor_players:
        await asyncio.sleep(2)
        await start_cop_phase(bot, chat_id, room)
        return

    human_doctor = next((p for p in doctor_players if not p.get("bot")), None)

    if human_doctor:
        kb = get_target_keyboard(room, human_doctor["id"], f"night_heal_{chat_id}")
        target_chat = chat_id if is_private_chat else human_doctor["id"]
        try:
            await bot.send_message(target_chat, "🩺 <b>Ваш ход (Доктор):</b> Кого вы хотите вылечить этой ночью?", reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        await asyncio.sleep(3)
        alive_targets = [p for p in room["players"] if p["alive"]]
        if alive_targets:
            import random
            room["night"]["heal"] = random.choice(alive_targets)["id"]
        await start_cop_phase(bot, chat_id, room)


async def start_cop_phase(bot: Bot, chat_id: int, room: dict):
    room["night"]["subphase"] = "cop"
    is_private_chat = room.get("is_private", False)
    cop_players = [p for p in room["players"] if p["role"] == "Комиссар" and p["alive"]]
    
    await bot.send_message(
        chat_id,
        "🌙 <i>Доктор закончил работу. Просыпается комиссар...</i>",
        parse_mode=ParseMode.HTML
    )

    if not cop_players:
        await asyncio.sleep(2)
        await finish_night_phase(bot, chat_id, room)
        return

    human_cop = next((p for p in cop_players if not p.get("bot")), None)

    if human_cop:
        kb = get_target_keyboard(room, human_cop["id"], f"night_check_{chat_id}")
        target_chat = chat_id if is_private_chat else human_cop["id"]
        try:
            await bot.send_message(target_chat, "🕵️‍♂️ <b>Ваш ход (Комиссар):</b> Чью роль вы хотите проверить?", reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        await asyncio.sleep(3)
        un_checked = [p for p in room["players"] if p["id"] != cop_players[0]["id"] and p["alive"]]
        if un_checked:
            import random
            target = random.choice(un_checked)
            room["night"]["checked_mafia_id"] = target["id"]
        await finish_night_phase(bot, chat_id, room)


async def finish_night_phase(bot: Bot, chat_id: int, room: dict):
    await bot.send_message(
        chat_id,
        "☀️ <b>Наступает утро. Город просыпается...</b>",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(2)

    dead_player, winner = game.finish_night(room)
    room["phase"] = "day"

    await process_morning_results(bot, chat_id, room, dead_player, winner)
    
    if not winner:
        await send_day_voting_message(bot, chat_id, room)


@router.callback_query(F.data == "start_game")
async def cb_start_game(callback: CallbackQuery, bot: Bot):
    chat_id = callback.message.chat.id
    room = get_or_create_room(chat_id)

    if room["started"]:
        await callback.answer("⚠️ Игра уже идет!", show_alert=True)
        return

    if len(room["players"]) < 3:
        await callback.answer("⚠️ Нужно минимум 3 игрока (включая ботов)!", show_alert=True)
        return

    room["is_private"] = callback.message.chat.type == "private"
    game.start_game(room)

    await callback.message.edit_text(
        "🚀 <b>Матч начался!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Роли успешно распределены. Проверьте личные сообщения с ботом.",
        parse_mode=ParseMode.HTML
    )

    for player in room["players"]:
        if not player.get("bot"):
            role_card = game.get_role_card(player["role"])
            target_chat_id = chat_id if room["is_private"] else player["id"]
            try:
                await bot.send_message(target_chat_id, role_card, parse_mode=ParseMode.HTML)
            except Exception:
                await callback.message.answer(f"⚠️ Не удалось отправить роль игроку <b>{player['name']}</b>. Напишите боту в ЛС!", parse_mode=ParseMode.HTML)

    await start_night_phase(bot, chat_id, room)


# --- 5. ОБРАБОТКА НОЧИ ---

@router.callback_query(F.data.startswith("night_"))
async def cb_night_action(callback: CallbackQuery, bot: Bot):
    data_parts = callback.data.split("_")
    action_type = data_parts[1]
    chat_id = int(data_parts[2])
    target_id = int(data_parts[3])

    room = rooms.get(chat_id)
    if not room or room["phase"] != "night":
        await callback.answer("⚠️ Ночной этап завершен.", show_alert=True)
        return

    target_player = next((p for p in room["players"] if p["id"] == target_id), None)
    if not target_player:
        return

    subphase = room["night"]["subphase"]

    if action_type == "kill" and subphase == "mafia":
        game.save_kill(room, target_id)
        await callback.answer(f"🎯 Цель выбрана: {target_player['name']}")
        await callback.message.edit_reply_markup(reply_markup=None)
        await start_doctor_phase(bot, chat_id, room)

    elif action_type == "heal" and subphase == "doctor":
        game.save_heal(room, target_id)
        await callback.answer(f"🩺 Вылечен: {target_player['name']}")
        await callback.message.edit_reply_markup(reply_markup=None)
        await start_cop_phase(bot, chat_id, room)

    elif action_type == "check" and subphase == "cop":
        game.save_check(room, target_id)
        is_mafia = target_player.get("role") in ["Мафия", "MAFIA"]
        status_text = "<b>МАФИЯ 🔪</b>" if is_mafia else "<b>МИРНЫЙ ЖИТЕЛЬ 🌾</b>"
        await callback.message.answer(f"🕵️‍♂️ <b>Результат проверки:</b> {target_player['name']} — {status_text}", parse_mode=ParseMode.HTML)
        await callback.answer("Проверка завершена!")
        await callback.message.edit_reply_markup(reply_markup=None)
        await finish_night_phase(bot, chat_id, room)
    else:
        await callback.answer("⚠️ Сейчас не ваш ход!", show_alert=True)


# --- 6. ДНЕВНОЕ ГОЛОСОВАНИЕ ---

async def send_day_voting_message(bot: Bot, chat_id: int, room: dict):
    # Очищаем старые голоса перед началом нового голосования
    room["day"]["votes"] = {}
    
    game.bot_vote(room)
    
    alive_humans = [p for p in room["players"] if p["alive"] and not p.get("bot")]

    if not alive_humans:
        await bot.send_message(
            chat_id,
            "☀️ <b>Дневной трибунал (Голосование)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👀 В живых не осталось игроков-людей. Боты принимают решение автоматически...",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(2)
        
        kicked_player, votes = game.end_day(room)
        await process_evening_results(bot, chat_id, room, kicked_player)
        winner = game.check_winner(room)

        if winner:
            await announce_winner(bot, chat_id, winner, room)
        else:
            await asyncio.sleep(2)
            await start_night_phase(bot, chat_id, room)
        return

    text = (
        "☀️ <b>Дневной трибунал (Голосование)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Обсудите улики и выберите игрока, которого хотите изгнать:"
    )
    
    for human in alive_humans:
        kb = get_target_keyboard(room, human["id"], f"day_vote_{chat_id}")
        target_chat = chat_id if room.get("is_private", False) else human["id"]
        try:
            await bot.send_message(target_chat, text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await bot.send_message(chat_id, f"⚠️ {human['name']}, откройте ЛС с ботом для голосования!", parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("day_vote_"))
async def cb_day_vote(callback: CallbackQuery, bot: Bot):
    data_parts = callback.data.split("_")
    chat_id = int(data_parts[2])
    target_id = int(data_parts[3])

    room = rooms.get(chat_id)
    if not room or room["phase"] != "day":
        await callback.answer("⚠️ Голосование уже завершено.", show_alert=True)
        return

    voter_id = callback.from_user.id
    
    player_check = next((p for p in room["players"] if p["id"] == voter_id), None)
    if not player_check:
        await callback.answer("⚠️ Вы не участник этой игры.", show_alert=True)
        return

    if not player_check["alive"]:
        await callback.answer("👀 Вы мертвы и можете только наблюдать за игрой.", show_alert=True)
        return

    game.save_vote(room, voter_id, target_id)
    target_player = next((p for p in room["players"] if p["id"] == target_id), None)
    
    await callback.answer(f"✅ Ваш голос против {target_player['name']} учтен!")

    alive_humans = [p for p in room["players"] if p["alive"] and not p.get("bot")]
    voted_count = len(room["day"]["votes"])

    if voted_count >= len(alive_humans):
        await asyncio.sleep(2)
        kicked_player, votes = game.end_day(room)
        
        await process_evening_results(bot, chat_id, room, kicked_player)
        winner = game.check_winner(room)

        if winner:
            await announce_winner(bot, chat_id, winner, room)
        else:
            await asyncio.sleep(2)
            await start_night_phase(bot, chat_id, room)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ВЫВОДА ---

async def process_morning_results(bot: Bot, chat_id, room, dead_player, winner):
    if winner:
        await announce_winner(bot, chat_id, winner, room)
        return

    if dead_player:
        text = f"☀️ <b>Итоги ночи</b>\n━━━━━━━━━━━━━━━━━━━━━━\n💀 Прошлой ночью был убит: <b>{dead_player['name']}</b> (Роль: <i>{dead_player['role']}</i>)"
    else:
        text = "☀️ <b>Итоги ночи</b>\n━━━━━━━━━━━━━━━━━━━━━━\n🎉 Прекрасные новости! Ночь обошлась без жертв."

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
    
    player_list = game.get_formatted_player_list(room)
    await bot.send_message(chat_id, player_list, parse_mode=ParseMode.HTML)


async def process_evening_results(bot: Bot, chat_id, room, kicked_player):
    votes = room["day"]["votes"]
    
    voting_details = []
    for voter_id, target_id in votes.items():
        voter = next((p for p in room["players"] if p["id"] == voter_id), None)
        target = next((p for p in room["players"] if p["id"] == target_id), None)
        if voter and target:
            voting_details.append(f"• <b>{voter['name']}</b> ➔ {target['name']}")

    votes_text = "\n".join(voting_details) if voting_details else "Никто не проголосовал."

    if kicked_player:
        text = (
            f"🌆 <b>Итоги трибунала и голосование</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 <b>Как распределились голоса:</b>\n{votes_text}\n\n"
            f"⚖️ Большинством голосов изгнан: <b>{kicked_player['name']}</b> (Роль: <i>{kicked_player['role']}</i>)"
        )
    else:
        text = (
            f"🌆 <b>Итоги трибунала и голосование</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 <b>Как распределились голоса:</b>\n{votes_text}\n\n"
            f"🤝 Голоса разделились поровну, никто не изгнан."
        )

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


async def announce_winner(bot: Bot, chat_id, winner, room=None):
    if room:
        stats.update_game_results(room, winner)

    if winner == "mafia":
        text = "🏆 <b>ИГРА ОКОНЧЕНА — ПОБЕДА МАФИИ!</b> 🔪\n━━━━━━━━━━━━━━━━━━━━━━\n<i>Синдикат захватил контроль над городом.</i>"
    else:
        text = "🏆 <b>ИГРА ОКОНЧЕНА — ПОБЕДА МИРНЫХ!</b> 🌾\n━━━━━━━━━━━━━━━━━━━━━━\n<i>Все преступники были найдены и обезврежены.</i>"

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)