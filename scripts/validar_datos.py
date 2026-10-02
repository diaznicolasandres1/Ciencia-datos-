"""Valida invariantes básicas del dataset sin dependencias externas."""
from csv import DictReader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "elecciones_presidenciales_1976_2020.csv"


def main() -> None:
    with DATA.open(encoding="utf-8", newline="") as source:
        rows = list(DictReader(source))

    years = [int(row["year"]) for row in rows]
    assert years == list(range(1976, 2021, 4)), "La serie debe ser cuatrienal"
    assert len(years) == len(set(years)), "Hay años duplicados"

    for row in rows:
        popular = sum(int(row[key]) for key in ("dem_votes", "rep_votes", "other_votes"))
        electoral = sum(
            int(row[key]) for key in ("dem_electoral", "rep_electoral", "other_electoral")
        )
        assert popular == int(row["total_votes"]), f"Suma popular inválida: {row['year']}"
        assert electoral == 538, f"Suma electoral inválida: {row['year']}"
        expected = "Democratic" if int(row["dem_electoral"]) > int(row["rep_electoral"]) else "Republican"
        assert row["winner"] == expected, f"Ganador inválido: {row['year']}"

    print(f"OK: {len(rows)} elecciones validadas ({years[0]}–{years[-1]}).")


if __name__ == "__main__":
    main()
