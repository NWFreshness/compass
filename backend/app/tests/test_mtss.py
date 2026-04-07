from app.services.mtss import calculate_tier, TierResult


def test_tier1_at_boundary():
    assert calculate_tier(80.0) == TierResult.tier1


def test_tier1_above():
    assert calculate_tier(95.0) == TierResult.tier1


def test_tier2_at_lower_boundary():
    assert calculate_tier(70.0) == TierResult.tier2


def test_tier2_at_upper_boundary():
    assert calculate_tier(79.9) == TierResult.tier2


def test_tier3_below():
    assert calculate_tier(69.9) == TierResult.tier3


def test_tier3_zero():
    assert calculate_tier(0.0) == TierResult.tier3


def test_custom_thresholds():
    assert calculate_tier(75.0, tier1_min=80.0, tier2_min=60.0) == TierResult.tier2
    assert calculate_tier(55.0, tier1_min=80.0, tier2_min=60.0) == TierResult.tier3
