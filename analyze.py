"""Análisis exploratorio y evaluación por elección, sin partición aleatoria."""
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["previous_margin", "previous_dem_pct"]
CENSUS_FEATURES = ["college_pct", "median_age", "poverty_pct"]


def census_comparison(df):
    """Comparar modelos en las mismas filas y elecciones con ACS disponible."""
    available = df.dropna(subset=FEATURES + CENSUS_FEATURES)
    scores = []
    for year in [2016, 2020, 2024]:
        train, test = available[available.year < year], available[available.year == year]
        if train.year.nunique() < 2 or len(test) != 51:
            continue
        for label, features in [("historical_same_sample", FEATURES), ("historical_plus_census", FEATURES + CENSUS_FEATURES)]:
            model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
            model.fit(train[features], train.target_democrat)
            prob = model.predict_proba(test[features])[:, 1]
            scores.append({"year": year, "model": label, "train_rows": len(train), "test_rows": len(test), "accuracy": accuracy_score(test.target_democrat, prob >= .5), "brier_score": brier_score_loss(test.target_democrat, prob), "log_loss": log_loss(test.target_democrat, prob, labels=[0, 1]), "baseline_accuracy": accuracy_score(test.target_democrat, test.previous_margin.gt(0))})
    return pd.DataFrame(scores)


def backtest(df):
    predictions, scores = [], []
    for year in [2008, 2012, 2016, 2020, 2024]:
        train = df[df.year < year]
        test = df[df.year == year]
        assert train.year.max() < test.year.min()
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
        model.fit(train[FEATURES], train.target_democrat)
        prob = model.predict_proba(test[FEATURES])[:, 1]
        baseline = test.previous_margin.gt(0).astype(int)
        scores.append({"year": year, "train_rows": len(train), "test_rows": len(test), "accuracy": accuracy_score(test.target_democrat, prob >= .5), "balanced_accuracy": balanced_accuracy_score(test.target_democrat, prob >= .5), "baseline_accuracy": accuracy_score(test.target_democrat, baseline), "brier_score": brier_score_loss(test.target_democrat, prob), "log_loss": log_loss(test.target_democrat, prob, labels=[0, 1])})
        result = test[["year", "state_po", "winner", "margin", "target_democrat"]].copy()
        result["p_democrat"] = prob
        result["predicted_winner"] = np.where(prob >= .5, "DEMOCRAT", "REPUBLICAN")
        result["correct"] = result.winner.eq(result.predicted_winner)
        predictions.append(result)
    return pd.DataFrame(scores), pd.concat(predictions, ignore_index=True)


def main():
    reports = ROOT / "reports"
    figures = reports / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "data/processed/elections_master.csv", dtype={"state_fips": str})
    quality = json.loads((ROOT / "data/processed/data_quality.json").read_text())
    national = df.groupby("year")[["dem_votes", "rep_votes", "other_votes", "total_votes"]].sum()
    national["dem_pct"] = national.dem_votes / national.total_votes * 100
    national["rep_pct"] = national.rep_votes / national.total_votes * 100
    national["margin"] = national.dem_pct - national.rep_pct
    national.to_csv(reports / "national_results.csv")
    df.isna().mean().mul(100).sort_values(ascending=False).rename("missing_pct").to_csv(reports / "missing_values.csv")
    competitive = df[df.year == 2024].assign(abs_margin=lambda x: x.margin.abs()).sort_values("abs_margin").head(10)
    competitive[["state_po", "dem_pct", "rep_pct", "margin", "winner"]].to_csv(reports / "competitive_states_2024.csv", index=False)
    scores, predictions = backtest(df)
    scores.to_csv(reports / "backtest_metrics.csv", index=False)
    predictions.to_csv(reports / "backtest_predictions.csv", index=False)
    comparison = census_comparison(df)
    if not comparison.empty:
        comparison.to_csv(reports / "census_model_comparison.csv", index=False)
    census_stats = df.groupby("year")[CENSUS_FEATURES + ["population", "median_income", "unemployment_pct"]].agg(["count", "min", "median", "max"])
    census_stats.to_csv(reports / "census_summary.csv")
    correlations = []
    for year, subset in df.groupby("year"):
        for feature in CENSUS_FEATURES + ["median_income", "unemployment_pct"]:
            paired = subset[[feature, "margin"]].dropna()
            if len(paired) >= 3:
                correlations.append({"year": year, "feature": feature, "n": len(paired), "pearson_r": paired[feature].corr(paired.margin)})
    pd.DataFrame(correlations, columns=["year", "feature", "n", "pearson_r"]).to_csv(reports / "census_correlations.csv", index=False)
    plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(national.index, national.dem_pct, marker="o", label="Demócrata", color="#2166ac")
    ax.plot(national.index, national.rep_pct, marker="o", label="Republicano", color="#b2182b")
    ax.set(xlabel="Elección", ylabel="% del voto popular (todos los votos)", title="Resultados presidenciales nacionales, 2000–2024", xticks=national.index)
    ax.legend(); fig.tight_layout(); fig.savefig(figures / "national_vote.png"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    comp = competitive.sort_values("margin")
    ax.barh(comp.state_po, comp.margin, color=np.where(comp.margin >= 0, "#2166ac", "#b2182b"))
    ax.axvline(0, color="black", linewidth=.7)
    ax.set(xlabel="Margen demócrata − republicano (puntos porcentuales)", title="Diez estados más competitivos de 2024")
    fig.tight_layout(); fig.savefig(figures / "competitive_states_2024.png"); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(scores.year, scores.accuracy * 100, marker="o", label="Regresión logística")
    ax.plot(scores.year, scores.baseline_accuracy * 100, marker="o", label="Repetir ganador anterior")
    ax.set(xlabel="Elección de evaluación", ylabel="Estados correctamente clasificados (%)", title="Evaluación temporal: entrenamiento solo en años anteriores", xticks=scores.year)
    ax.legend(); fig.tight_layout(); fig.savefig(figures / "backtest_accuracy.png"); plt.close(fig)
    lines = ["# Análisis inicial de elecciones presidenciales de EE. UU.", "", f"Panel de {len(df)} filas: 50 estados y DC × 7 elecciones (2000–2024). Estado de integración: **{quality['status']}**.", "", "## Voto popular nacional", "", "El porcentaje nacional se calcula sumando votos; no promediando porcentajes estatales. El voto popular no determina por sí solo la presidencia.", "", "| Año | Demócrata % | Republicano % | Margen D−R (pp) |", "|---|---:|---:|---:|"]
    lines += [f"| {year} | {row.dem_pct:.2f} | {row.rep_pct:.2f} | {row.margin:.2f} |" for year, row in national.iterrows()]
    lines += ["", "![Voto nacional](figures/national_vote.png)", "", "## Evaluación temporal", "", "Regresión logística con `previous_margin` y `previous_dem_pct`. Para cada elección, se entrena exclusivamente con elecciones anteriores. Se compara con repetir el ganador de la elección previa. Los resultados actuales, encuestas retrospectivas y variables posteriores no se usan como entradas.", "", "| Evaluación | Filas de entrenamiento | Aciertos / 51 | Accuracy | Baseline | Brier | Log loss |", "|---|---:|---:|---:|---:|---:|---:|"]
    lines += [f"| {int(r.year)} | {int(r.train_rows)} | {int(round(r.accuracy * 51))} | {r.accuracy:.3f} | {r.baseline_accuracy:.3f} | {r.brier_score:.3f} | {r.log_loss:.3f} |" for r in scores.itertuples()]
    lines += ["", "![Validación](figures/backtest_accuracy.png)", "", "Las filas de una misma elección no son observaciones independientes. Hay solo cinco elecciones de evaluación; una accuracy alta puede provenir de acertar estados seguros. Estas probabilidades no se han calibrado para pronosticar una elección futura.", "", "## Estados competitivos de 2024", "", "![Estados](figures/competitive_states_2024.png)", "", "## Fuentes pendientes y límites", ""]
    lines += [f"- {issue}" for issue in quality["issues"]]
    lines += [f"- {limit}" for limit in quality["limitations"]]
    lines += ["", "## Comparación con Census", "", "Se comparan los modelos con y sin educación universitaria, edad y pobreza en las mismas filas con ACS disponible (desde 2008). Las evaluaciones 2016, 2020 y 2024 usan al menos dos elecciones anteriores para entrenar. No deben compararse directamente con el primer backtest, que dispone de más años de entrenamiento.", "", "| Año | Modelo | Filas de entrenamiento | Accuracy | Brier |", "|---|---|---:|---:|---:|"]
    if not comparison.empty:
        lines += [f"| {r.year} | {r.model} | {r.train_rows} | {r.accuracy:.3f} | {r.brier_score:.3f} |" for r in comparison.itertuples()]
    else:
        lines += ["", "Comparación pendiente: faltan datos ACS suficientes."]
    lines += ["", "## Próximos pasos", "", "Revisar calidad, comparabilidad y fechas de publicación de Census; verificar vintages de FRED; incorporar encuestas de 2020/2024; conseguir asignaciones electorales históricas y datos distritales para Maine y Nebraska. La simulación del Colegio Electoral requiere además modelar errores correlacionados entre estados. Una proyección de 2028 requiere supuestos y datos de ese ciclo.", ""]
    (reports / "analisis.md").write_text("\n".join(lines), encoding="utf-8")
    print(scores.to_string(index=False))
    print("Informe: reports/analisis.md")
    if not comparison.empty:
        print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
