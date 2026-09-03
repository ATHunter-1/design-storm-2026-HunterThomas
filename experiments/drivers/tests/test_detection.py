import pandas as pd

from drivers.episodes import Detection, Episode, episode_detection

THRESHOLD = 3.0
START, END = pd.Timestamp("2024-05-10"), pd.Timestamp("2024-05-12")
EPISODE = Episode(start=START, end=END, days=3, peak_value=4.0, peak_date=END)


def _preds(spikes: dict[str, float], start="2024-05-01", periods=20):
    preds = pd.Series(2.0, index=pd.date_range(start, periods=periods, freq="D"))
    for date, value in spikes.items():
        preds[pd.Timestamp(date)] = value
    return preds


def test_prediction_two_days_before_start_is_a_detection_with_lead_minus_two():
    detection = episode_detection(EPISODE, _preds({"2024-05-08": 3.5}), THRESHOLD, above=True)
    assert detection == Detection(detected=True, lead=-2)


def test_no_prediction_beyond_threshold_in_window_is_a_non_detection():
    detection = episode_detection(EPISODE, _preds({"2024-05-01": 3.5, "2024-05-13": 3.5}), THRESHOLD, above=True)
    assert detection == Detection(detected=False, lead=None)


def test_lead_is_the_first_qualifying_prediction_relative_to_start():
    preds = _preds({"2024-05-07": 3.5, "2024-05-11": 3.5})
    assert episode_detection(EPISODE, preds, THRESHOLD, above=True).lead == -3


def test_prediction_during_the_episode_has_a_non_negative_lead():
    assert episode_detection(EPISODE, _preds({"2024-05-11": 3.5}), THRESHOLD, above=True).lead == 1


def test_lead_days_bounds_how_far_before_start_counts():
    preds = _preds({"2024-05-08": 3.5})
    assert episode_detection(EPISODE, preds, THRESHOLD, above=True, lead_days=1).detected is False


def test_missing_prediction_days_in_window_are_skipped():
    preds = _preds({"2024-05-08": 3.5}).drop(pd.Timestamp("2024-05-09"))
    assert episode_detection(EPISODE, preds, THRESHOLD, above=True).lead == -2
