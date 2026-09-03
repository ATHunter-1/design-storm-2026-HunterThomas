import numpy as np
import pandas as pd

from analog.fetch import PAGE_SIZE, data_readme_text, dwr_frame, is_last_page, snotel_frame


def test_snotel_payload_becomes_date_swe_frame():
    payload = [{"data": [{"values": [{"date": "1998-09-30", "value": 0.0}, {"date": "1998-10-01", "value": None}]}]}]
    frame = snotel_frame(payload)
    assert list(frame.columns) == ["DATE", "SWE"]
    assert list(frame["DATE"]) == ["1998-09-30", "1998-10-01"]
    assert frame["SWE"].iloc[0] == 0.0
    assert np.isnan(frame["SWE"].iloc[1])


def test_dwr_rows_keep_streamflow_only_and_blank_missing_flag():
    rows = [
        {"measDate": "1900-01-01 00:00:00", "measType": "Streamflow", "value": 175.0},
        {"measDate": "1900-01-02 00:00:00", "measType": "Streamflow", "value": -999},
        {"measDate": "1900-01-04 00:00:00", "measType": "Streamflow", "value": 180.0},
        {"measDate": "1900-01-03 00:00:00", "measType": "GageHeight", "value": 2.0},
    ]
    frame = dwr_frame(rows)
    assert list(frame.columns) == ["measDate", "Flow_CFS"]
    assert list(frame["measDate"]) == ["1900-01-01", "1900-01-02", "1900-01-03", "1900-01-04"]
    assert frame["Flow_CFS"].iloc[0] == 175.0
    assert np.isnan(frame["Flow_CFS"].iloc[1])
    assert np.isnan(frame["Flow_CFS"].iloc[2])
    assert frame["Flow_CFS"].iloc[3] == 180.0


def test_paging_stops_when_a_page_is_short():
    assert is_last_page([{}] * (PAGE_SIZE - 1))
    assert not is_last_page([{}] * PAGE_SIZE)


def test_data_readme_names_fetch_date_row_counts_and_water_years():
    swe = pd.DataFrame({"DATE": ["1998-09-30", "1998-10-01", "1999-10-02"], "SWE": [0.0, 1.0, 2.0]})
    flow = pd.DataFrame({"measDate": ["1900-01-01", "1900-01-02"], "Flow_CFS": [175.0, np.nan]})
    text = data_readme_text("2026-08-28", swe, flow)
    assert "2026-08-28" in text
    assert "3 rows" in text
    assert "2 rows" in text
    assert "3 water years" in text
    assert "1998-09-30 to 1999-10-02" in text
    assert "1900-01-01 to 1900-01-02" in text


def test_data_readme_lists_the_may_2026_readings():
    dates = pd.date_range("2026-05-10", periods=7, freq="D").strftime("%Y-%m-%d")
    swe = pd.DataFrame({"DATE": dates, "SWE": [0.0, 0.0, 9.0, 9.0, 9.0, 9.0, 0.0]})
    flow = pd.DataFrame({"measDate": ["2026-05-10"], "Flow_CFS": [300.0]})
    text = data_readme_text("2026-08-28", swe, flow)
    assert "05-11: 0, 05-12: 9, 05-13: 9, 05-14: 9, 05-15: 9, 05-16: 0" in text
