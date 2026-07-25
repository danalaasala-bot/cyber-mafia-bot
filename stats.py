import json
import os

STATS_FILE = "player_stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

def get_user_stats(user_id: int):
    stats = load_stats()
    str_id = str(user_id)
    if str_id not in stats:
        stats[str_id] = {
            "games": 0,
            "wins": 0,
            "losses": 0
        }
        save_stats(stats)
    return stats[str_id]

def update_game_results(room, winner_team):
    """
    winner_team: "mafia" или "civilians" (мирные)
    """
    stats = load_stats()
    
    for player in room["players"]:
        if player.get("bot"):
         continue  # Ботов не учитываем в статистике игроков
            
        user_id = str(player["id"])
        if user_id not in stats:
            stats[user_id] = {"games": 0, "wins": 0, "losses": 0}
            
        stats[user_id]["games"] += 1
        
        player_role = player.get("role", "")
        # Определяем, победил ли конкретный игрок
        is_mafia_role = player_role in ["Мафия", "MAFIA"]
        
        if (winner_team == "mafia" and is_mafia_role) or (winner_team == "civilians" and not is_mafia_role):
            stats[user_id]["wins"] += 1
        else:
            stats[user_id]["losses"] += 1
            
    save_stats(stats)