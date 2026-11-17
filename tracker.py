
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
OUTPUT = Path("data/prices.json")
TOP_COUNT = 20


def number(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    request = Request(
        API_URL,
        headers={"User-Agent": "FPLPredictionTracker/1.0"}
    )

    with urlopen(request, timeout=30) as response:
        data = json.load(response)

    elements = data.get("elements", [])
    teams = {
        team["id"]: team["name"]
        for team in data.get("teams", [])
    }

    if not elements:
        raise RuntimeError("Aucun joueur recu depuis FPL.")

    players = []
    valid_predictions = 0

    for p in elements:
        projections = p.get("price_change_projections")

        if not isinstance(projections, list):
            continue

        # La prochaine echeance correspond a offset = 0.
        next_projection = next(
            (
                item for item in projections
                if isinstance(item, dict)
                and item.get("offset") == 0
            ),
            None
        )

        if next_projection is None:
            continue

        projected = number(
            next_projection.get("projected_percent")
        )
        current = number(p.get("price_change_percent"))

        if projected is None:
            continue

        valid_predictions += 1

        players.append({
            "id": p["id"],
            "name": p["web_name"],
            "team": teams.get(p["team"], str(p["team"])),
            "team_id": p["team"],
            "current_price": p["now_cost"] / 10,
            "current_progress": current,
            "projected_progress": projected,
            "likelihood": next_projection.get("likelihood"),
            "projections": projections
        })

    if valid_predictions == 0:
        raise RuntimeError(
            "Aucune projection officielle exploitable. "
            "Le fichier existant est conserve."
        )

    # Classement par progression projetee, pas par
    # probabilite mathematique.
    rises = sorted(
        (p for p in players if p["projected_progress"] > 0),
        key=lambda p: p["projected_progress"],
        reverse=True
    )[:TOP_COUNT]

    falls = sorted(
        (p for p in players if p["projected_progress"] < 0),
        key=lambda p: p["projected_progress"]
    )[:TOP_COUNT]

    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Official Fantasy Premier League API",
        "projection_offset": 0,
        "ranking_method": "projected_percent",
        "players_with_predictions": valid_predictions,
        "top_expected_rises": rises,
        "top_expected_falls": falls,
        "players": players
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"{valid_predictions} projections officielles.")
    print("\nTOP HAUSSES ATTENDUES")
    for p in rises:
        print(
            f'{p["name"]} ({p["team"]}): '
            f'{p["projected_progress"]:+.1f}%'
        )

    print("\nTOP BAISSES ATTENDUES")
    for p in falls:
        print(
            f'{p["name"]} ({p["team"]}): '
            f'{p["projected_progress"]:+.1f}%'
        )


if __name__ == "__main__":
    main()

