import pandas as pd

from drivers.episodes import Episode, episodes

THRESHOLD = 3.0


def _series(values, dates):
    return pd.Series(values, index=pd.DatetimeIndex(dates), dtype=float)


def test_five_consecutive_days_yield_two_episodes():
    actual = _series([2, 4, 5, 2, 3.5], pd.date_range("2024-05-01", periods=5, freq="D"))
    found = episodes(actual, THRESHOLD, above=True)
    assert [(e.start, e.end) for e in found] == [
        (pd.Timestamp("2024-05-02"), pd.Timestamp("2024-05-03")),
        (pd.Timestamp("2024-05-05"), pd.Timestamp("2024-05-05")),
    ]


def test_episode_records_days_and_peak():
    actual = _series([2, 4, 5, 2, 3.5], pd.date_range("2024-05-01", periods=5, freq="D"))
    first, second = episodes(actual, THRESHOLD, above=True)
    assert isinstance(first, Episode)
    assert (first.days, first.peak_value, first.peak_date) == (2, 5.0, pd.Timestamp("2024-05-03"))
    assert (second.days, second.peak_value, second.peak_date) == (1, 3.5, pd.Timestamp("2024-05-05"))


def test_missing_calendar_day_splits_two_above_threshold_days():
    actual = _series([4, 5], [pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-03")])
    found = episodes(actual, THRESHOLD, above=True)
    assert [(e.start, e.end, e.days) for e in found] == [
        (pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-01"), 1),
        (pd.Timestamp("2024-05-03"), pd.Timestamp("2024-05-03"), 1),
    ]


def test_below_threshold_direction_takes_the_minimum_as_peak():
    actual = _series([70, 50, 40, 65], pd.date_range("2024-05-01", periods=4, freq="D"))
    (episode,) = episodes(actual, 60.0, above=False)
    assert (episode.days, episode.peak_value, episode.peak_date) == (2, 40.0, pd.Timestamp("2024-05-03"))


def test_no_days_beyond_threshold_yields_no_episodes():
    actual = _series([1, 2, 2.5], pd.date_range("2024-05-01", periods=3, freq="D"))
    assert episodes(actual, THRESHOLD, above=True) == []
