import random


ROLES = [
    "Мафия",
    "Доктор",
    "Комиссар",
    "Житель"
]


def give_roles(room):

    players = room["players"]

    count = len(players)


    roles = []


    # Для 4 игроков:
    # 1 мафия
    # 1 доктор
    # 1 комиссар
    # остальные жители

    if count >= 4:

        roles.append("Мафия")
        roles.append("Доктор")
        roles.append("Комиссар")


        for _ in range(count - 3):

            roles.append("Житель")


    random.shuffle(roles)


    for player, role in zip(players, roles):

        player["role"] = role
        player["alive"] = True