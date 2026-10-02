"""Descarga fuentes reales y construye un panel estatal 2000–2024.

Sin --allow-partial, una fuente requerida inaccesible impide publicar el CSV.
--offline reutiliza exclusivamente los archivos del repositorio.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data/raw"
OUT = ROOT / "data/processed"
YEARS = list(range(2000, 2025, 4))
SOURCES = {
    "1976-2020-president.csv": "https://raw.githubusercontent.com/plotly/Figure-Friday/main/2024/week-33/1976-2020-president.csv",
    "2024-president-state.csv": "https://raw.githubusercontent.com/MEDSL/2024-elections-official/main/2024-president-state.csv",
    "pres_pollaverages_1968-2016.csv.gz": "https://raw.githubusercontent.com/fivethirtyeight/data/master/polls/pres_pollaverages_1968-2016.csv",
    **{f"fred_{s}.csv": f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}" for s in ["UNRATE", "CPIAUCSL", "GDPC1"]},
}
DEMOGRAPHICS = ["population", "median_age", "median_income", "college_pct", "white_pct", "black_pct", "hispanic_pct", "poverty_pct", "unemployment_pct"]
ACS_VARIABLES = ["NAME", "B01001_001E", "B01002_001E", "B19013_001E", "B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E", "B02001_002E", "B02001_003E", "B03003_003E", "B17001_001E", "B17001_002E", "B23025_003E", "B23025_005E"]
NOMINEES = {
    2000: ("Al Gore", "George W. Bush"),
    2004: ("John Kerry", "George W. Bush"),
    2008: ("Barack Obama", "John McCain"),
    2012: ("Barack Obama", "Mitt Romney"),
    2016: ("Hillary Rodham Clinton", "Donald Trump"),
}


class SourceUnavailable(RuntimeError):
    pass


def cached_csv(name: str, offline: bool = False) -> pd.DataFrame:
    path = RAW / name
    if not path.exists():
        if offline:
            raise SourceUnavailable(f"No está en caché: {name}")
        print(f"Descargando {name}", flush=True)
        try:
            response = requests.get(SOURCES[name], timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SourceUnavailable(f"Descarga bloqueada o fallida: {name} ({type(exc).__name__})") from exc
        content = response.content
        # Comprobar que no sea una página de error antes de guardar la caché.
        frame = pd.read_csv(io.BytesIO(content), low_memory=False)
        if frame.shape[1] < 2:
            raise SourceUnavailable(f"Respuesta sin esquema CSV válido: {name}")
        if name.endswith('.gz'):
            content = gzip.compress(content, mtime=0)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_bytes(content)
        temporary.replace(path)
    return pd.read_csv(path, low_memory=False)


def aggregate_returns(raw: pd.DataFrame) -> pd.DataFrame:
    """Sumar líneas partidarias sin mezclar TOTAL con modos desagregados."""
    raw = raw.copy()
    if "mode" in raw:
        raw["mode"] = raw["mode"].str.upper()
        keys = ["year", "state_po"]
        has_total = raw.groupby(keys)["mode"].transform(lambda x: x.eq("TOTAL").any())
        raw = raw[~has_total | raw["mode"].eq("TOTAL")].copy()
    vote_col = "candidatevotes" if "candidatevotes" in raw else "votes"
    raw[vote_col] = pd.to_numeric(raw[vote_col], errors="raise")
    raw["totalvotes"] = pd.to_numeric(raw["totalvotes"], errors="raise")
    raw["state_fips"] = raw["state_fips"].astype(int).astype(str).str.zfill(2)
    raw["state_po"] = raw["state_po"].str.strip().str.upper()
    keys = ["year", "state_po", "state_fips", "state"]
    totals = raw.groupby(keys, as_index=False).agg(total_votes=("totalvotes", "max"))
    party = raw[raw.party_simplified.isin(["DEMOCRAT", "REPUBLICAN"])]
    pivot = party.pivot_table(index=keys, columns="party_simplified", values=vote_col, aggfunc="sum").reset_index()
    pivot.columns.name = None
    result = totals.merge(pivot, on=keys, validate="one_to_one").rename(columns={"DEMOCRAT": "dem_votes", "REPUBLICAN": "rep_votes"})
    result["other_votes"] = result.total_votes - result.dem_votes - result.rep_votes
    if (result.other_votes < 0).any() or result[["dem_votes", "rep_votes"]].isna().any().any():
        raise ValueError("Votos inconsistentes o falta una candidatura principal")
    result["dem_pct"] = result.dem_votes / result.total_votes * 100
    result["rep_pct"] = result.rep_votes / result.total_votes * 100
    result["margin"] = result.dem_pct - result.rep_pct
    result["winner"] = np.select([result.margin.gt(0), result.margin.lt(0)], ["DEMOCRAT", "REPUBLICAN"], default="TIE")
    return result


def previous_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values(["state_po", "year"]).copy()
    for col in ["dem_pct", "rep_pct", "margin", "winner"]:
        frame[f"previous_{col}"] = frame.groupby("state_po")[col].shift()
    frame["previous_election_year"] = frame.groupby("state_po").year.shift()
    return frame


def elections(offline: bool) -> pd.DataFrame:
    historical = aggregate_returns(cached_csv("1976-2020-president.csv", offline))
    current = aggregate_returns(cached_csv("2024-president-state.csv", offline))
    # 1996 proporciona el rezago real para 2000, sin perder la primera elección.
    full = pd.concat([historical, current], ignore_index=True)
    if full.duplicated(["year", "state_po"]).any():
        raise ValueError("Resultados estatales duplicados")
    return previous_features(full).query("year in @YEARS").reset_index(drop=True)


def polls(state_names: dict[str, str], offline: bool) -> pd.DataFrame:
    raw = cached_csv("pres_pollaverages_1968-2016.csv.gz", offline)
    raw["date"] = pd.to_datetime(raw.modeldate, format="%m/%d/%Y")
    raw["state_po"] = raw.state.str.upper().map(state_names)
    frames = []
    for year, names in NOMINEES.items():
        cutoff = pd.Timestamp(year=year, month=10, day=31)
        selected = raw[(raw.cycle == year) & raw.state_po.notna() & raw.date.le(cutoff)].copy()
        selected["party"] = selected.candidate_name.map(dict(zip(names, ["poll_dem", "poll_rep"])))
        selected = selected[selected.party.notna()]
        selected = selected.sort_values("date").drop_duplicates(["state_po", "party"], keep="last")
        # Excluir estimaciones antiguas de más de 30 días.
        selected = selected[selected.date.ge(cutoff - pd.Timedelta(days=30))]
        frame = selected.pivot(index="state_po", columns="party", values="pct_estimate").reindex(columns=["poll_dem", "poll_rep"]).reset_index()
        frame.columns.name = None
        frame["year"] = year
        frame["poll_margin"] = frame.poll_dem - frame.poll_rep
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def census(year: int, offline: bool) -> pd.DataFrame:
    reference = year - 2
    product = "acs1" if year == 2008 else "acs5"
    name = f"census_{reference}_{product}.json"
    path = RAW / name
    legacy = reference <= 2010
    college_cols = ([f"B15002_{i:03d}E" for i in [15, 16, 17, 18, 32, 33, 34, 35]]
                    if legacy else [f"B15003_{i:03d}E" for i in range(22, 26)])
    college_total = "B15002_001E" if legacy else "B15003_001E"
    hispanic = "B03001_003E" if legacy else "B03003_003E"
    # Antes de 2011 no existen B15003/B23025 en estos endpoints.
    # B23001 permite sumar empleados y desempleados civiles de ambos sexos
    # y todas las edades; no incorpora las categorías de Fuerzas Armadas.
    unemployed_indices = [8, 15, 22, 29, 36, 43, 50, 57, 64, 71, 76, 81, 86]
    unemployed_indices += [i + 86 for i in unemployed_indices.copy()]
    unemployed_cols = [f"B23001_{i:03d}E" for i in unemployed_indices]
    employed_cols = [f"B23001_{i - 1:03d}E" for i in unemployed_indices]
    variables = (["NAME", "B01001_001E", "B01002_001E", "B19013_001E", college_total]
                 + college_cols + ["B02001_002E", "B02001_003E", hispanic, "B17001_001E", "B17001_002E"]
                 + unemployed_cols + employed_cols) if legacy else ACS_VARIABLES
    if not path.exists():
        if offline:
            raise SourceUnavailable(f"No está en caché: {name}")
        try:
            combined = None
            # La API admite como máximo 50 variables en cada consulta.
            for start in range(0, len(variables), 45):
                params = {"get": ",".join(variables[start:start + 45]), "for": "state:*"}
                if os.getenv("CENSUS_API_KEY"):
                    params["key"] = os.environ["CENSUS_API_KEY"]
                response = requests.get(f"https://api.census.gov/data/{reference}/acs/{product}", params=params, timeout=60)
                response.raise_for_status()
                if "Missing Key" in response.text[:2000]:
                    raise SourceUnavailable("Census requiere CENSUS_API_KEY; configurarla de forma segura, sin pegarla en el chat")
                batch = response.json()
                if not isinstance(batch, list) or not batch or "state" not in batch[0]:
                    raise SourceUnavailable(f"Census {reference}: esquema inesperado")
                piece = pd.DataFrame(batch[1:], columns=batch[0])
                combined = piece if combined is None else combined.merge(piece, on="state", validate="one_to_one")
            data = [combined.columns.tolist()] + combined.values.tolist()
        except (requests.RequestException, ValueError) as exc:
            # No imprimir URL ni cuerpo, porque podrían contener la clave.
            raise SourceUnavailable(f"Census {reference}/{product}: acceso o respuesta inválida ({type(exc).__name__})") from exc
        if not isinstance(data, list) or not data or "state" not in data[0]:
            raise SourceUnavailable(f"Census {reference}: esquema inesperado")
        path.write_text(json.dumps(data), encoding="utf-8")
    data = json.loads(path.read_text())
    raw = pd.DataFrame(data[1:], columns=data[0])
    numeric = raw.drop(columns=["NAME", "state"]).apply(pd.to_numeric, errors="raise")
    numeric = numeric.mask(numeric < 0)  # Sentinel values del Census.
    result = pd.DataFrame({"year": year, "state_fips": raw.state.str.zfill(2), "census_reference_year": reference, "census_product": product})
    for col, source in [("population", "B01001_001E"), ("median_age", "B01002_001E"), ("median_income", "B19013_001E")]:
        result[col] = numeric[source]
    result["college_pct"] = numeric[college_cols].sum(axis=1, min_count=len(college_cols)) / numeric[college_total].replace(0, np.nan) * 100
    ratios = [("white_pct", "B02001_002E", "B01001_001E"), ("black_pct", "B02001_003E", "B01001_001E"), ("hispanic_pct", hispanic, "B01001_001E"), ("poverty_pct", "B17001_002E", "B17001_001E")]
    if legacy:
        unemployed = numeric[unemployed_cols].sum(axis=1, min_count=len(unemployed_cols))
        employed = numeric[employed_cols].sum(axis=1, min_count=len(employed_cols))
        result["unemployment_pct"] = unemployed / (employed + unemployed).replace(0, np.nan) * 100
    else:
        ratios.append(("unemployment_pct", "B23025_005E", "B23025_003E"))
    for col, numerator, denominator in ratios:
        result[col] = numeric[numerator] / numeric[denominator].replace(0, np.nan) * 100
    return result


def economy(offline: bool) -> pd.DataFrame:
    annual = {}
    for series in ["UNRATE", "CPIAUCSL", "GDPC1"]:
        raw = cached_csv(f"fred_{series}.csv", offline)
        date_col = raw.columns[0]
        raw[date_col] = pd.to_datetime(raw[date_col], errors="raise")
        raw[series] = pd.to_numeric(raw[series], errors="coerce")
        annual[series] = raw.groupby(raw[date_col].dt.year)[series].mean()
    frame = pd.DataFrame(annual).sort_index()
    result = pd.DataFrame({"economy_reference_year": frame.index, "unemployment": frame.UNRATE, "inflation_pct": frame.CPIAUCSL.pct_change(fill_method=None) * 100, "gdp_growth_pct": frame.GDPC1.pct_change(fill_method=None) * 100})
    # Todo el período observado es anterior a la elección, pero las series están revisadas.
    result["year"] = result.economy_reference_year + 1
    return result[result.year.isin(YEARS)]


def validate(master: pd.DataFrame) -> None:
    if len(master) != 357 or master.duplicated(["year", "state_po"]).any():
        raise ValueError("Se esperaban exactamente 7 × 51 filas únicas")
    if not master.groupby("year").state_po.nunique().eq(51).all():
        raise ValueError("Faltan estados o DC")
    if not master.previous_election_year.eq(master.year - 4).all():
        raise ValueError("Rezago electoral no consecutivo")
    if not master.margin.between(-100, 100).all():
        raise ValueError("Margen fuera de rango")
    for col in ["dem_pct", "rep_pct"]:
        if not master[col].between(0, 100).all():
            raise ValueError(f"{col} fuera de rango")
    for col in ["college_pct", "white_pct", "black_pct", "hispanic_pct", "poverty_pct", "unemployment_pct"]:
        if col in master and not master[col].dropna().between(0, 100).all():
            raise ValueError(f"{col} fuera de rango")
    if "census_reference_year" in master:
        known = master.dropna(subset=["census_reference_year"])
        if not known.census_reference_year.lt(known.year).all():
            raise ValueError("Census debe referir a un período anterior a la elección")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--allow-partial", action="store_true", help="Publicar datos parciales con faltantes y diagnóstico explícitos")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    master = elections(args.offline)
    issues = []
    name_map = master[["state", "state_po"]].drop_duplicates().set_index("state").state_po.to_dict()
    try:
        master = master.merge(polls(name_map, args.offline), on=["year", "state_po"], how="left", validate="one_to_one")
    except SourceUnavailable as exc:
        issues.append(str(exc))
        for col in ["poll_dem", "poll_rep", "poll_margin"]:
            master[col] = np.nan
    frames = []
    for year in YEARS[2:]:
        try:
            frames.append(census(year, args.offline))
        except SourceUnavailable as exc:
            issues.append(str(exc))
    if frames:
        master = master.merge(pd.concat(frames), on=["year", "state_fips"], how="left", validate="one_to_one")
    for col in DEMOGRAPHICS + ["census_reference_year", "census_product"]:
        if col not in master:
            master[col] = np.nan
    try:
        master = master.merge(economy(args.offline), on="year", how="left", validate="many_to_one")
    except SourceUnavailable as exc:
        issues.append(str(exc))
        for col in ["economy_reference_year", "unemployment", "inflation_pct", "gdp_growth_pct"]:
            master[col] = np.nan
    validate(master)
    master["target_democrat"] = master.winner.map({"DEMOCRAT": 1, "REPUBLICAN": 0}).astype("Int64")
    master["state_year"] = master.state_po + "_" + master.year.astype(str)
    # Guardar auditoría incluso cuando la ejecución estricta falla.
    quality = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "rows": len(master), "states_including_dc": 51, "years": YEARS, "status": "partial" if issues else "available_sources_complete", "issues": issues, "missing_counts": master.isna().sum().to_dict(), "limitations": ["No hay ACS anterior a 2000/2004 en este pipeline; quedan faltantes.", "Encuestas disponibles solo 2000–2016; archivo retrospectivo publicado en 2020, excluido del modelo predictivo.", "FRED usa valores revisados y el año previo; no constituye un backtest de vintages en tiempo real.", "No se incluyen votos electorales sin verificar las asignaciones históricas y los distritos de ME/NE.", "No es una predicción de 2028."]}
    (OUT / "data_quality.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = []
    for path in sorted(RAW.iterdir()):
        if not path.is_file() or path.name.endswith('.tmp') or path.name == 'manifest.json':
            continue
        url = SOURCES.get(path.name)
        if path.name.startswith('census_'):
            reference, product = path.stem.removeprefix('census_').split('_')
            url = f"https://api.census.gov/data/{reference}/acs/{product}"
        manifest.append({"file": path.name, "url": url, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if issues and not args.allow_partial:
        raise SystemExit("Fuentes pendientes. Revisar data_quality.json; usar --allow-partial para explorar datos incompletos.")
    master.to_csv(OUT / "elections_master.csv", index=False)
    print(f"Dataset: {len(master)} filas; {master.shape[1]} columnas; estado: {quality['status']}")
    for issue in issues:
        print(f"Pendiente: {issue}")


if __name__ == "__main__":
    main()
