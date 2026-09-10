"""Tests for the benign identity-overlap sensitivity experiment."""

from evaluate_benign_identity_overlap import evaluate_label_overlap


def test_overlap_sets_are_nested_and_complete():
    results = evaluate_label_overlap(rows=5_000, fractions=(0.0, 0.25, 0.50, 1.0))
    relabeled = [results[f]["relabeled_identity_risk_rows"] for f in (0.0, 0.25, 0.50, 1.0)]
    assert relabeled == sorted(relabeled)
    assert relabeled[0] == 0
    assert relabeled[-1] == results[1.0]["identity_risk_rows"]


def test_invalid_overlap_fraction_is_rejected():
    try:
        evaluate_label_overlap(rows=100, fractions=(-0.01,))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid overlap fraction")


def test_full_overlap_increases_guarded_safe_step_up_rate():
    results = evaluate_label_overlap(rows=10_000, fractions=(0.0, 1.0))
    baseline = results[0.0]["policies"]["guarded_075"]["safe_step_up_rate"]
    full = results[1.0]["policies"]["guarded_075"]["safe_step_up_rate"]
    assert full > baseline


def test_policy_does_not_change_when_only_labels_change():
    results = evaluate_label_overlap(rows=5_000, fractions=(0.0, 1.0))
    # Relabeling changes evaluation denominators, not the policy outputs themselves.
    for policy in ("additive_075", "additive_080", "guarded_075"):
        zero = results[0.0]["policies"][policy]
        full = results[1.0]["policies"][policy]
        assert zero["safe"] + zero["unsafe"] == full["safe"] + full["unsafe"] == 5_000
