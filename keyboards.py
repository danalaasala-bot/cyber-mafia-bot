from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Меню старта в группе
main_group_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎭 Создать игру", 
                callback_data="create_group_room"
            )
        ]
    ]
)

# Лобби в группе
group_lobby_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Присоединиться", callback_data="join_group_game"),
            InlineKeyboardButton(text="🤖 Добавить бота", callback_data="add_group_bot")
        ],
        [
            InlineKeyboardButton(text="🚀 Начать игру", callback_data="start_group_game"),
            InlineKeyboardButton(text="🚪 Покинуть", callback_data="leave_group_game")
        ]
    ]
)

# Меню перезапуска
restart_group_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔄 Сыграть ещё раз", 
                callback_data="restart_group_game"
            )
        ]
    ]
)