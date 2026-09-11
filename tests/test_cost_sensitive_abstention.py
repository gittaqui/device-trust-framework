"""Tests for cost-sensitive abstention sensitivity analysis."""

from evaluate_cost_sensitive_abstention import CostModel, decision_cost, evaluate_cost_sensitivity


def test_decision_cost_semantics():
    costs = CostModel(step_up=0.1, safe_deny=0.5)
    assert decision_cost(safe=False, decision="ALLOW", costs=costs) == 1.0
    assert decision_cost(safe=True, decision="ALLOW", costs=costs) == 0.0
    assert decision_cost(safe=True, decision="DENY", costs=costs) == 0.5
    assert decision_cost(safe=False, decision="DENY", costs=costs) == 0.0
    assert decision_cost(safe=True, decision="STEP_UP", costs=costs) == 0.1
    assert decision_cost(safe=False, decision="STEP_UP", costs=costs) == 0.1


def test_invalid_costs_are_rejected():
    try:
        CostModel(step_up=-0.01)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for a negative decision cost")


def test_low_and_higher_step_up_costs_can_change_winner():
    results = evaluate_cost_sensitivity(rows=20_000, overlap_fractions=(0.0,), step_up_costs=(0.025, 0.20))
    assert results[0.0]["costs"][0.025]["winner"] != results[0.0]["costs"][0.20]["winner"]


def test_full_benign_overlap_can_change_preferred_policy():
    results = evaluate_cost_sensitivity(rows=20_000, overlap_fractions=(0.0, 1.0), step_up_costs=(0.10,))
    assert results[0.0]["costs"][0.10]["winner"] != results[1.0]["costs"][0.10]["winner"]
