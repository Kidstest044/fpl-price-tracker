import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
DATA_FILE = Path("data/prices.json")


def main():
    request = Request(API_URL, headers={"User-Agent": "FPLPriceTracker/1.0"})

    with urlopen(request, timeout=30) as response:
        data = json.load(response)

    players = {
        str(p["id"]): {
            "name": p["web_name"],
            "team": p["team"],
            "price": p["now_cost"] / 10
        }
        for p in data["elements"]
    }

    previous = {}
    if DATA_FILE.exists():
        previous = json.loads(DATA_FILE.read_text(encoding="utf-8")).get("players", {})

    changes = []
    for player_id, player in players.items():
        old = previous.get(player_id)
        if old and old["price"] != player["price"]:
            changes.append({
                "player": player["name"],
                "old": old["price"],
                "new": player["price"],
                "difference": round(player["price"] - old["price"], 1)
            })

    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "players": players,
        "changes_since_previous_run": changes
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"{len(players)} joueurs récupérés.")
    print(f"{len(changes)} changements de prix détectés.")


if __name__ == "__main__":
    main()
