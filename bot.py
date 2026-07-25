import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiohttp import web  # <--- Добавили импорт для веб-сервера

from config import TOKEN
from handlers import router
import game

bot = Bot(token=TOKEN)
dp = Dispatcher()

active_timers = {}

# --- Веб-сервер для Render, чтобы не было ошибки тайм-аута ---
async def handle(request):
    return web.Response(text="Mafia Bot is running and alive!")

app = web.Application()
app.router.add_get("/", handle)
runner = web.AppRunner(app)

async def start_web_server():
    port = int(os.getenv("PORT", 10000))
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")
# -----------------------------------------------------------


async def start_phase_timer(chat_id: int, room: dict, phase: str, duration: int = 45):
    if chat_id in active_timers:
        active_timers[chat_id].cancel()

    task = asyncio.create_task(_timer_coroutine(chat_id, room, phase, duration))
    active_timers[chat_id] = task


async def _timer_coroutine(chat_id: int, room: dict, phase: str, duration: int):
    try:
        if duration > 10:
            await asyncio.sleep(duration - 10)
            if room["started"] and room["phase"] == phase:
                await bot.send_message(
                    chat_id, 
                    "⚠️ <b>Осталось 10 секунд!</b> Поторопитесь с решением!", 
                    parse_mode=ParseMode.HTML
                )
            await asyncio.sleep(10)
        else:
            await asyncio.sleep(duration)

        if not room["started"] or room["phase"] != phase:
            return

        if phase == "night":
            await bot.send_message(chat_id, "⏰ <b>Время ночи истекло!</b> Город просыпается...", parse_mode=ParseMode.HTML)
            
            game.bot_night_action(room)
            dead_player, winner = game.finish_night(room)
            
            room["phase"] = "day"
            
            await process_morning_results(chat_id, room, dead_player, winner)
            if not winner:
                from handlers import send_day_voting_message
                await start_phase_timer(chat_id, room, phase="day", duration=60)
                await send_day_voting_message(bot, chat_id, room)

        elif phase == "day":
            await bot.send_message(chat_id, "⏰ <b>Время на обсуждение вышло!</b> Подводим итоги...", parse_mode=ParseMode.HTML)
            
            game.bot_vote(room)
            kicked_player, votes = game.end_day(room)
            
            room["phase"] = "night"
            
            await process_evening_results(chat_id, room, kicked_player)
            winner = game.check_winner(room)
            if not winner:
                await start_phase_timer(chat_id, room, phase="night", duration=45)

    except asyncio.CancelledError:
        pass


def stop_timer(chat_id: int):
    if chat_id in active_timers:
        active_timers[chat_id].cancel()
        del active_timers[chat_id]


async def process_morning_results(chat_id, room, dead_player, winner):
    if winner:
        await announce_winner(chat_id, winner)
        return

    if dead_player:
        text = f"☀️ <b>ГОРОД ПРОСНУЛСЯ!</b>\n━━━━━━━━━━━━━━━━━━━\n💀 Прошлой ночью был убит: <b>{dead_player['name']}</b>"
    else:
        text = "☀️ <b>ГОРОД ПРОСНУЛСЯ!</b>\n━━━━━━━━━━━━━━━━━━━\n🎉 Отличные новости! Доктор спас жертву, никто не погиб!"

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
    
    player_list = game.get_formatted_player_list(room)
    await bot.send_message(chat_id, player_list, parse_mode=ParseMode.HTML)

    bot_messages = await game.get_bot_chat_messages(room)
    for msg in bot_messages:
        await bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML)


async def process_evening_results(chat_id, room, kicked_player):
    if kicked_player:
        text = f"🌆 <b>ВЕЧЕРНИЙ СУД ОКОНЧЕН!</b>\n━━━━━━━━━━━━━━━━━━━\n⚖️ Решением жителей из города был изгнан: <b>{kicked_player['name']}</b> (Роль: <i>{kicked_player['role']}</i>)"
    else:
        text = "🌆 <b>ВЕЧЕРНИЙ СУД ОКОНЧЕН!</b>\n━━━━━━━━━━━━━━━━━━━\n🤝 Голоса разделились, никто не выбыл из игры."

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


async def announce_winner(chat_id, winner):
    if winner == "mafia":
        text = "🏆 <b>ИГРА ОКОНЧЕНА! ПОБЕДИЛА МАФИЯ!</b> 🔪\n━━━━━━━━━━━━━━━━━━━\nПреступный мир полностью захватил город."
    else:
        text = "🏆 <b>ИГРА ОКОНЧЕНА! ПОБЕДИЛИ МИРНЫЕ ЖИТЕЛИ!</b> 🌾\n━━━━━━━━━━━━━━━━━━━\nВся мафия была успешно вычислена и нейтрализована."

    await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


async def main():
    # Запускаем веб-сервер перед стартом бота, чтобы Render видел открытый порт
    await start_web_server()
    
    dp.include_router(router)
    logging.basicConfig(level=logging.INFO)
    print("Бот и веб-сервер запущены!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())