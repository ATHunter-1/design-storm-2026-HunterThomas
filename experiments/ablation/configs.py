"""Which feature sets get scored. Pure: no I/O, no model fitting."""

from dataclasses import dataclass

JAKE_FEATURES = {
    "TOC": [
        "Specific_Cond_Mean", "month_cos", "month_sin", "turb_flow", "turb_3day",
        "precip_7day", "swe_7day", "turb/cond", "Turbidity_Median", "Turbidity_Max",
    ],
    "Alk": [
        "Specific_Cond_Mean", "pH_Median", "month_sin", "month_cos", "flow_7day_avg",
        "turb_3day", "turb_flow", "Dissolved_Oxygen_Mean",
    ],
}

JAKE_BASELINE = {"TOC": ["turb_flow"], "Alk": ["Specific_Cond_Mean"]}

MINIMAL_SETS = {
    "TOC": {
        "top3_catboost": ["turb_flow", "Specific_Cond_Mean", "swe_7day"],
        "loading_plus_season": ["turb_flow", "month_sin", "month_cos"],
        "no_season": ["Specific_Cond_Mean", "turb_flow", "turb_3day", "precip_7day", "swe_7day",
                      "turb/cond", "Turbidity_Median", "Turbidity_Max"],
        "no_turbidity_family": ["Specific_Cond_Mean", "month_cos", "month_sin", "precip_7day", "swe_7day"],
    },
    "Alk": {
        "top2_catboost": ["Specific_Cond_Mean", "pH_Median"],
        "cond_plus_season": ["Specific_Cond_Mean", "month_sin", "month_cos"],
        "no_season": ["Specific_Cond_Mean", "pH_Median", "flow_7day_avg", "turb_3day", "turb_flow",
                      "Dissolved_Oxygen_Mean"],
        "chemistry_only": ["Specific_Cond_Mean", "pH_Median", "Dissolved_Oxygen_Mean"],
    },
}


@dataclass(frozen=True)
class Config:
    target: str
    label: str
    features: tuple[str, ...]
    model: str


def ablation_configs(target: str, models: tuple[str, ...]) -> list[Config]:
    configs = [Config(target, "baseline_linear", tuple(JAKE_BASELINE[target]), "linear")]
    for model in models:
        configs.extend(_configs_for_model(target, model))
    return configs


def _configs_for_model(target: str, model: str) -> list[Config]:
    full = JAKE_FEATURES[target]
    configs = [Config(target, "jake_full", tuple(full), model)]
    configs.extend(_leave_one_out(target, full, model))
    for label, features in MINIMAL_SETS[target].items():
        configs.append(Config(target, label, tuple(features), model))
    return configs


def _leave_one_out(target: str, full: list[str], model: str) -> list[Config]:
    return [
        Config(target, f"drop:{dropped}", tuple(f for f in full if f != dropped), model)
        for dropped in full
    ]
