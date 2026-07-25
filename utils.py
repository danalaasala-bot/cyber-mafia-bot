async def update_room(bot, code, room):
    text = room_text(code, room)

    for player in room["players"]:
        try:
            await bot.send_message(
                player["id"],
                text,
                parse_mode="Markdown"
            )
        except:
            pass


def room_text(code, room):
    text = (
        f"🎭 **Комната:** `{code}`\n\n"
        f"👥 **Игроков:** {len(room['players'])}/15\n\n"
        "**Участники:**\n"
    )

    for player in room["players"]:
        status = "🟢" if player.get("alive", True) else "💀"
        bot_mark = " 🤖" if player.get("bot") else ""
        text += f"{status} {player['name']}{bot_mark}\n"

    return text