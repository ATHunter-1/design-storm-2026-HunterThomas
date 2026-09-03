"""Produce runnable copies of Jake Slawson's notebooks.

Jake's originals in ../scripts are left untouched. This script copies them
here with the smallest edits that let them run off Denver Water's network:

- hardcoded OneDrive paths become relative paths (../data, fresh-data, figures)
- the truststore cells (corporate TLS interception) are removed
- the model notebooks' first five cells, which build the target series from
  two internal lab exports Jake did not share, are replaced by one cell that
  loads FoothillsInfluent.csv, the output of that step
"""
import json
import re
from pathlib import Path

ORIGINALS = Path("../scripts")
HERE = Path(".")

ONEDRIVE = r'r"C:\\Users\\jslawson\\OneDrive - Denver Water\\SCO\\Source_water_early_warning_systems\\Data'
FIGURE_PATH = re.compile(ONEDRIVE + r'\\Figures\\(\w+)\.png"')
DATA_CSV_PATH = re.compile(ONEDRIVE + r'\\(\w+)\.csv"')
DATA_FOLDER = re.compile(ONEDRIVE + r'"')

GRABBERS = [
    "USGS_gage_data_grabber",
    "DWR_gage_grabber",
    "SNTL_grabber",
    "GHCN_grabber",
]
MODELS = {"TOC_SoftSensor": "TOC", "Alkalinity_Soft_Sensor": "Alk"}

FIRST_LOAD_CELL = 1
LAST_LOAD_CELL = 5


def source(cell):
    return "".join(cell["source"])


def set_source(cell, text):
    cell["source"] = text.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def is_truststore(cell):
    return "truststore" in source(cell)


def relocate_paths(text):
    text = FIGURE_PATH.sub(r'"figures/\1.png"', text)
    text = DATA_CSV_PATH.sub(r'"fresh-data/\1.csv"', text)
    text = DATA_FOLDER.sub('"fresh-data"', text)
    return text


def load_cell(target):
    sntl_line = 'sntl = pd.read_csv(DATA / "MichiganCreek.csv")\n' if target == "TOC" else ""
    return (
        "# Local replacement for Jake's cells 1-5. His notebook built the target\n"
        "# series from two internal lab exports (PL-FTH-INF_cleaned.csv and\n"
        "# PL-FTH-HW_cleaned.csv) that were not shared. FoothillsInfluent.csv is\n"
        "# the output of that step, so it is loaded directly here.\n"
        "from pathlib import Path\n"
        'DATA = Path("../data")\n'
        'usgs = pd.read_csv(DATA / "USGS_South_Platte.csv")\n'
        'dwr = pd.read_csv(DATA / "SouthPlatteTelemetry.csv")\n'
        'precip = pd.read_csv(DATA / "USC00058022.csv")\n'
        + sntl_line +
        'fth = pd.read_csv(DATA / "FoothillsInfluent.csv")\n'
        "fth['DATE'] = pd.to_datetime(fth['DATE'])\n"
        "combined_fth = (fth.set_index('DATE')\n"
        "                   .rename(columns={'TOC_mg_L': 'TOC', 'Alk_mg_L': 'Alk'})\n"
        f"                   [['{target}']].sort_index())\n"
        "combined_fth\n"
    )


def assert_load_cells(cells, name):
    first = source(cells[FIRST_LOAD_CELL])
    last = source(cells[LAST_LOAD_CELL])
    assert "PL-FTH-INF_cleaned" in first, f"{name}: cell {FIRST_LOAD_CELL} is not the load cell"
    assert "pd.concat([fth_inf_pivot" in last, f"{name}: cell {LAST_LOAD_CELL} is not the concat cell"


PYTHON3_KERNEL = {"name": "python3", "display_name": "Python 3", "language": "python"}


def use_local_kernel(nb):
    nb.setdefault("metadata", {})["kernelspec"] = PYTHON3_KERNEL


def patch_model(name, target):
    nb = json.loads((ORIGINALS / f"{name}.ipynb").read_text())
    use_local_kernel(nb)
    cells = nb["cells"]
    assert_load_cells(cells, name)
    replacement = dict(cells[FIRST_LOAD_CELL])
    set_source(replacement, load_cell(target))
    cells[FIRST_LOAD_CELL:LAST_LOAD_CELL + 1] = [replacement]
    nb["cells"] = [c for c in cells if not is_truststore(c)]
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            set_source(cell, relocate_paths(source(cell)))
    (HERE / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    print(f"patched {name}: {len(nb['cells'])} cells")


def patch_grabber(name):
    nb = json.loads((ORIGINALS / f"{name}.ipynb").read_text())
    use_local_kernel(nb)
    nb["cells"] = [c for c in nb["cells"] if not is_truststore(c)]
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            set_source(cell, relocate_paths(source(cell)))
    (HERE / f"{name}.ipynb").write_text(json.dumps(nb, indent=1))
    print(f"patched {name}: {len(nb['cells'])} cells")


if __name__ == "__main__":
    for name in GRABBERS:
        patch_grabber(name)
    for name, target in MODELS.items():
        patch_model(name, target)
