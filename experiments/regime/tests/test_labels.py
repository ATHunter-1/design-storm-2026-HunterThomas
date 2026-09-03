import numpy as np
import pandas as pd

from snowpack.wateryear import DRY_BELOW_FRACTION
from regime.labels import MIN_REFERENCE_YEARS, Reference, labels_table, reference_from


def _summary(april1_by_year: dict[int, float]) -> pd.DataFrame:
    years = list(april1_by_year)
    return pd.DataFrame(
        {"april1_swe": list(april1_by_year.values()), "days_with_data": [365] * len(years)},
        index=pd.Index(years, name="water_year"),
    )


KIT = {2022: np.nan, 2023: 9.1, 2024: 12.0, 2025: 9.3, 2026: 0.8}


def _long_record(years: int) -> pd.DataFrame:
    return _summary({1999 + i: 8.0 + (i % 5) for i in range(years)})


def test_reference_comes_from_the_long_record_when_it_has_enough_april_1_years():
    full = _long_record(MIN_REFERENCE_YEARS)
    reference = reference_from(full, _summary(KIT))
    assert reference == Reference(median=float(full["april1_swe"].median()), years=MIN_REFERENCE_YEARS, fallback_used=False)


def test_reference_falls_back_to_the_in_kit_median_when_the_long_record_is_short():
    reference = reference_from(_long_record(MIN_REFERENCE_YEARS - 1), _summary(KIT))
    assert (reference.years, reference.fallback_used) == (4, True)
    assert np.isclose(reference.median, 9.2)


def test_reference_falls_back_when_the_long_record_is_absent():
    reference = reference_from(None, _summary(KIT))
    assert (reference.years, reference.fallback_used) == (4, True)
    assert np.isclose(reference.median, 9.2)


def test_years_without_an_april_1_reading_do_not_count_toward_the_reference():
    full = _long_record(MIN_REFERENCE_YEARS + 1)
    full.loc[1999, "april1_swe"] = np.nan
    reference = reference_from(full, _summary(KIT))
    assert (reference.years, reference.fallback_used) == (MIN_REFERENCE_YEARS, False)


def test_labels_table_has_fraction_label_days_and_a_blank_label_for_years_without_april_1():
    reference = Reference(median=10.0, years=28, fallback_used=False)
    table = labels_table(_summary(KIT), reference)
    assert table.index.tolist() == [2022, 2023, 2024, 2025, 2026]
    assert table.loc[2026, "label"] == "dry"
    assert table.loc[2023, "label"] == "wet"
    assert pd.isna(table.loc[2022, "label"])
    assert np.isnan(table.loc[2022, "fraction_of_reference"])
    assert np.isclose(table.loc[2024, "fraction_of_reference"], 1.2)
    assert table.loc[2024, "days_with_data"] == 365
    assert (table["reference_median"] == 10.0).all()
    assert (table["reference_years"] == 28).all()
    assert (table["fallback_used"] == False).all()


def test_labels_table_uses_the_shared_dry_cutoff():
    just_below = DRY_BELOW_FRACTION * 10.0 - 0.01
    table = labels_table(_summary({2030: just_below, 2031: DRY_BELOW_FRACTION * 10.0}), Reference(10.0, 28, False))
    assert table["label"].tolist() == ["dry", "wet"]
