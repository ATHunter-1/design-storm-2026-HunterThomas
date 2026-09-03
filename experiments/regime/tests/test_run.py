import json

import numpy as np
import pandas as pd

from regime.labels import MIN_REFERENCE_YEARS
from regime.run import LABELS_FILE, write_labels

KIT_APRIL_1 = {2023: 9.1, 2024: 12.0, 2025: 9.3, 2026: 0.8}


def _water_year_days(water_year: int, from_april_2: bool = False) -> pd.DatetimeIndex:
    start = f"{water_year}-04-02" if from_april_2 else f"{water_year - 1}-10-01"
    return pd.date_range(start, f"{water_year}-09-30", freq="D")


def _swe_rows(days: pd.DatetimeIndex, april1: float) -> pd.DataFrame:
    values = np.where(days < pd.Timestamp(f"{days[-1].year}-05-01"), april1, 0.0)
    return pd.DataFrame({"DATE": days, "SWE": values})


def _write_kit(path) -> None:
    rows = [_swe_rows(_water_year_days(2022, from_april_2=True), 0.0)]
    rows += [_swe_rows(_water_year_days(y), swe) for y, swe in KIT_APRIL_1.items()]
    kit = pd.concat(rows)
    kit["DATE"] = kit["DATE"].dt.strftime("%-m/%-d/%Y")
    kit.to_csv(path, index=False)


def _write_full(path, years: int) -> None:
    rows = [_swe_rows(_water_year_days(1999 + i), 8.0 + (i % 5)) for i in range(years)]
    full = pd.concat(rows)
    full["DATE"] = full["DATE"].dt.strftime("%Y-%m-%d")
    full.to_csv(path, index=False)


def _read_labels(results_dir) -> pd.DataFrame:
    return pd.read_csv(results_dir / LABELS_FILE, index_col="water_year", keep_default_na=False, na_values=[""])


def test_labels_csv_lists_every_water_year_with_a_blank_label_for_2022_and_is_byte_identical_twice(tmp_path):
    kit, full, results = tmp_path / "MichiganCreek.csv", tmp_path / "MichiganCreek_full.csv", tmp_path / "results"
    _write_kit(kit)
    _write_full(full, MIN_REFERENCE_YEARS)
    write_labels(kit, full, results)
    first = (results / LABELS_FILE).read_bytes()
    write_labels(kit, full, results)
    assert (results / LABELS_FILE).read_bytes() == first
    table = _read_labels(results)
    assert table.index.tolist() == [2022, 2023, 2024, 2025, 2026]
    assert np.isnan(table.loc[2022, "april1_swe"])
    assert pd.isna(table.loc[2022, "label"])
    assert np.isnan(table.loc[2022, "fraction_of_reference"])
    assert table.loc[2026, "label"] == "dry"
    assert table.loc[2024, "april1_swe"] == 12.0
    assert table["days_with_data"].tolist() == [182, 365, 366, 365, 365]


def test_long_record_present_means_reference_from_it_and_no_fallback(tmp_path):
    kit, full, results = tmp_path / "MichiganCreek.csv", tmp_path / "MichiganCreek_full.csv", tmp_path / "results"
    _write_kit(kit)
    _write_full(full, MIN_REFERENCE_YEARS + 2)
    write_labels(kit, full, results)
    table = _read_labels(results)
    assert table["reference_years"].unique().tolist() == [MIN_REFERENCE_YEARS + 2]
    assert table["fallback_used"].unique().tolist() == [False]
    assert np.isclose(table["reference_median"].iloc[0], 10.0)
    assert np.isclose(table.loc[2024, "fraction_of_reference"], 1.2)


def test_long_record_absent_means_in_kit_median_and_fallback(tmp_path):
    kit, full, results = tmp_path / "MichiganCreek.csv", tmp_path / "missing.csv", tmp_path / "results"
    _write_kit(kit)
    write_labels(kit, full, results)
    table = _read_labels(results)
    assert table["reference_years"].unique().tolist() == [4]
    assert table["fallback_used"].unique().tolist() == [True]
    assert np.isclose(table["reference_median"].iloc[0], 9.2)
    assert pd.isna(table.loc[2022, "label"])
    assert table["label"].tolist()[1:] == ["wet", "wet", "wet", "dry"]
