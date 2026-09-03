from ablation.configs import JAKE_FEATURES, MINIMAL_SETS, ablation_configs


def test_leave_one_out_drops_exactly_one_feature_each():
    configs = [c for c in ablation_configs("Alk", ("catboost",)) if c.label.startswith("drop:")]
    full = JAKE_FEATURES["Alk"]
    assert len(configs) == len(full)
    for config in configs:
        dropped = config.label.removeprefix("drop:")
        assert dropped in full
        assert dropped not in config.features
        assert len(config.features) == len(full) - 1


def test_every_run_includes_baseline_full_and_minimal_sets():
    labels = [c.label for c in ablation_configs("TOC", ("rf_grid",))]
    assert labels[0] == "baseline_linear"
    assert "jake_full" in labels
    for minimal in MINIMAL_SETS["TOC"]:
        assert minimal in labels


def test_models_multiply_configs_but_share_one_baseline():
    one = ablation_configs("TOC", ("rf_grid",))
    two = ablation_configs("TOC", ("rf_grid", "catboost"))
    assert len(two) == 2 * len(one) - 1


def test_minimal_sets_only_use_features_the_frame_can_produce():
    known = set(JAKE_FEATURES["TOC"]) | set(JAKE_FEATURES["Alk"])
    for target, sets in MINIMAL_SETS.items():
        for features in sets.values():
            assert set(features) <= known, (target, features)
