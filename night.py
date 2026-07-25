from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def mafia_keyboard(room, mafia_id):

    keyboard = []


    for player in room["players"]:

        if not player["alive"]:
            continue

        if player["id"] == mafia_id:
            continue


        keyboard.append(
            [
                InlineKeyboardButton(
                    text=player["name"],
                    callback_data=f"kill_{player['id']}"
                )
            ]
        )


    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )




def doctor_keyboard(room, doctor_id):

    keyboard = []


    for player in room["players"]:

        if not player["alive"]:
            continue


        keyboard.append(
            [
                InlineKeyboardButton(
                    text=player["name"],
                    callback_data=f"heal_{player['id']}"
                )
            ]
        )


    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )




def commissioner_keyboard(room, commissioner_id):

    keyboard = []


    for player in room["players"]:

        if not player["alive"]:
            continue


        if player["id"] == commissioner_id:
            continue


        keyboard.append(
            [
                InlineKeyboardButton(
                    text=player["name"],
                    callback_data=f"check_{player['id']}"
                )
            ]
        )


    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )




def vote_keyboard(room, voter_id=None):

    keyboard = []


    for player in room["players"]:

        if not player["alive"]:
            continue


        if voter_id and player["id"] == voter_id:
            continue


        keyboard.append(
            [
                InlineKeyboardButton(
                    text=player["name"],
                    callback_data=f"vote_{player['id']}"
                )
            ]
        )


    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )