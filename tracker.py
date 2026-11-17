
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
OUTPUT = Path("data/prices.json")


def main():
    request = Request(
        API_URL,
        headers={"User-Agent": "FPLPredictionTracker/1.0"}
    )

    with urlopen(request, timeout=30) as response:
        data = json.load(response)

    players = data.get("elements", [])
    if not players:
        raise RuntimeError("Aucun joueur reçu depuis l'API FPL.")

    # Vérification de la présence des prévisions officielles.
    prediction_fields = [
        "price_change_percent",
        "price_change_projections"
    ]

    available = [
        field for field in prediction_fields
        if any(field in player for player in players)
    ]

    if not available:
        sample_keys = sorted(players[0].keys())
        raise RuntimeError(
            "Les champs de prédiction sont absents de "
            "la réponse officielle FPL. "
            "Champs disponibles : " + ", ".join(sample_keys)
        )

    results = []

    for player in players:
        prediction = {
            field: player.get(field)
            for field in available
        }

        if all(value is None for value in prediction.values()):
            continue

        results.append({
            "id": player["id"],
            "name": player["web_name"],
            "team_id": player["team"],
            "current_price": player["now_cost"] / 10,
            "predictions": prediction
        })

    if not results:
        raise RuntimeError(
            "Les champs existent, mais aucune prédiction "
            "exploitable n'a été reçue."
        )

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Official Fantasy Premier League API",
        "prediction_fields": available,
        "players_with_predictions": len(results),
        "players": results
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("Source : FPL officielle")
    print("Champs trouvés :", ", ".join(available))
    print("Joueurs avec données :", len(results))
    print("Prédictions enregistrées :", OUTPUT)


if __name__ == "__main__":
    main()
