import numpy as np
import pandas as pd
import pytest

from build_dataset import aggregate_returns, previous_features, validate
from analyze import FEATURES, backtest


def test_totals_do_not_double_count_modes_and_fusion_lines():
    raw = pd.DataFrame({"year": [2024] * 5, "state_po": ["NY"] * 5, "state_fips": [36] * 5, "state": ["NEW YORK"] * 5, "party_simplified": ["DEMOCRAT", "DEMOCRAT", "REPUBLICAN", "OTHER", "DEMOCRAT"], "votes": [45, 5, 40, 10, 30], "totalvotes": [100] * 5, "mode": ["TOTAL"] * 4 + ["EARLY"]})
    result = aggregate_returns(raw).iloc[0]
    assert result.dem_votes == 50
    assert result.rep_votes == 40
    assert result.other_votes == 10
    assert result.dem_pct == 50
    assert result.state_fips == "36"


def test_lag_does_not_cross_states():
    raw = pd.DataFrame({"year": [2000, 1996, 2000, 1996], "state_po": ["NY", "NY", "TX", "TX"], "dem_pct": [60, 55, 40, 45], "rep_pct": [40, 45, 60, 55], "margin": [20, 10, -20, -10], "winner": ["DEMOCRAT", "DEMOCRAT", "REPUBLICAN", "REPUBLICAN"]})
    result = previous_features(raw).query("year == 2000").set_index("state_po")
    assert result.loc["NY", "previous_margin"] == 10
    assert result.loc["TX", "previous_margin"] == -10


def test_real_dataset_contract():
    from build_dataset import ROOT
    df = pd.read_csv(ROOT / "data/processed/elections_master.csv")
    validate(df)
    assert df.query("year == 2024 and state_po == 'PA'").winner.item() == "REPUBLICAN"
    assert df.query("year == 2000 and state_po == 'FL'").margin.item() < 0
    assert df.previous_margin.notna().all()
    with pytest.raises(ValueError):
        validate(pd.concat([df, df.iloc[:1]]))


def test_backtest_does_not_use_current_targets_as_features():
    from build_dataset import ROOT
    df = pd.read_csv(ROOT / "data/processed/elections_master.csv")
    assert FEATURES == ["previous_margin", "previous_dem_pct"]
    scores, predictions = backtest(df)
    assert scores.test_rows.eq(51).all()
    assert len(predictions) == 255
    # Cambiar los resultados de 2024 no debe cambiar sus probabilidades.
    altered = df.copy()
    altered.loc[altered.year == 2024, "target_democrat"] = 1 - altered.loc[altered.year == 2024, "target_democrat"]
    _, new_predictions = backtest(altered)
    np.testing.assert_allclose(predictions.query("year == 2024").p_democrat, new_predictions.query("year == 2024").p_democrat)


def test_census_denominators_and_sentinel(tmp_path, monkeypatch):
    import json
    import build_dataset as builder
    values = ["Example", "1000", "-666666666", "50000", "500", "100", "20", "10", "5", "600", "200", "150", "900", "90", "400", "20", "01"]
    (tmp_path / "census_2022_acs5.json").write_text(json.dumps([builder.ACS_VARIABLES + ["state"], values]))
    monkeypatch.setattr(builder, "RAW", tmp_path)
    result = builder.census(2024, offline=True).iloc[0]
    assert result.state_fips == "01"
    assert result.census_reference_year == 2022
    assert result.college_pct == 27
    assert result.poverty_pct == 10
    assert result.unemployment_pct == 5
    assert pd.isna(result.median_age)


def test_economy_uses_prior_year_only(monkeypatch):
    import build_dataset as builder
    values = {"UNRATE": [4, 6, 99], "CPIAUCSL": [100, 102, 999], "GDPC1": [1000, 1030, 9999]}
    def load(name, offline):
        series = name.removeprefix("fred_").removesuffix(".csv")
        return pd.DataFrame({"observation_date": ["1998-01-01", "1999-01-01", "2000-01-01"], series: values[series]})
    monkeypatch.setattr(builder, "cached_csv", load)
    result = builder.economy(offline=True).iloc[0]
    assert result.year == 2000
    assert result.economy_reference_year == 1999
    assert result.unemployment == 6
    assert result.inflation_pct == pytest.approx(2)
    assert result.gdp_growth_pct == pytest.approx(3)


def test_census_real_coverage_and_percentage_validation():
    from build_dataset import ROOT
    frame = pd.read_csv(ROOT / "data/processed/elections_master.csv")
    assert frame.query("year >= 2008").population.notna().all()
    assert frame.query("year < 2008").population.isna().all()
    assert frame.population.notna().sum() == 255
    frame.loc[frame.year == 2024, "college_pct"] = 101
    with pytest.raises(ValueError, match="college_pct"):
        validate(frame)


def test_census_comparison_uses_identical_samples():
    from build_dataset import ROOT
    from analyze import census_comparison
    frame = pd.read_csv(ROOT / "data/processed/elections_master.csv")
    comparison = census_comparison(frame)
    assert len(comparison) == 6
    assert comparison.groupby("year").train_rows.nunique().eq(1).all()
    assert comparison.test_rows.eq(51).all()
    assert comparison.groupby("year").train_rows.first().tolist() == [102, 153, 204]
