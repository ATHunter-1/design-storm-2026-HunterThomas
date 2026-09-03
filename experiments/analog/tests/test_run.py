import hashlib
import json

import numpy as np
import pandas as pd

from analog.run import ANALOGS_FILE, FOLLOWING_FILE, META_FILE, WATER_YEARS_FILE, build_results


def _write_inputs(data_dir):
    data_dir.mkdir()
    swe_rows, flow_rows = [], []
    for water_year, peak, peak_offset, melt_offset in [(2023, 9.0, 200, 240), (2024, 13.0, 220, 245), (2025, 10.0, 190, 245), (2026, 4.9, 167, 194)]:
        days = pd.date_range(f"{water_year - 1}-10-01", f"{water_year}-09-30", freq="D")
        values = np.zeros(len(days))
        values[peak_offset:melt_offset] = peak
        swe_rows.append(pd.DataFrame({"DATE": days.strftime("%Y-%m-%d"), "SWE": values}))
        flow_rows.append(pd.DataFrame({"measDate": days.strftime("%Y-%m-%d"), "Flow_CFS": 100.0 + peak * 50 * np.sin(np.linspace(0, 3, len(days))).clip(0)}))
    pd.concat(swe_rows).to_csv(data_dir / "MichiganCreek_full.csv", index=False)
    pd.concat(flow_rows).to_csv(data_dir / "SouthPlatteFlow_full.csv", index=False)


def _bytes(results_dir):
    return {name: (results_dir / name).read_bytes() for name in (WATER_YEARS_FILE, ANALOGS_FILE, FOLLOWING_FILE)}


def test_offline_run_writes_three_files_identically_twice_with_input_md5s(tmp_path):
    data_dir, results_dir = tmp_path / "data", tmp_path / "results"
    _write_inputs(data_dir)
    build_results(data_dir, results_dir)
    first = _bytes(results_dir)
    build_results(data_dir, results_dir)
    assert _bytes(results_dir) == first
    meta = json.loads((results_dir / META_FILE).read_text())
    expected = {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in data_dir.glob("*.csv")}
    assert meta["inputs_md5"] == expected
    assert set(meta) == {"inputs_md5", "versions", "git_commit"}
    analogs = pd.read_csv(results_dir / ANALOGS_FILE, index_col=0)
    assert 2026 not in analogs.index
    assert analogs.index[0] == 2023
    following = pd.read_csv(results_dir / FOLLOWING_FILE, index_col=0)
    assert following.loc[2023, "following_water_year"] == 2024
