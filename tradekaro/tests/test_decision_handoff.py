"""
The handoff from the brain's vote to the number TheCouncil votes on.

This is where a bearish call used to become a BUY. The mapping was inline in
main.py with no test, so nothing objected for the two weeks it was live.

TheCouncil.review_trade derives direction from that single number:

    tech_signal >= 0.55  ->  BUY
    tech_signal <= 0.45  ->  SELL
    otherwise            ->  no direction

so these tests apply the same rule and assert the brain's direction survives.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.multi_timeframe_brain import MultiTimeframeBrain, prediction_from_vote


def council_reads(prediction):
    """TheCouncil.review_trade's direction rule, copied verbatim."""
    if prediction >= 0.55:
        return 'BUY'
    if prediction <= 0.45:
        return 'SELL'
    return 'NO_DIRECTION'


def vote_for(t15, t10, t5, now):
    """Votes for the latest four 5-minute bars, oldest first."""
    return MultiTimeframeBrain(None, scaler=None)._aggregate_votes(
        {'t-15m': t15, 't-10m': t10, 't-5m': t5, 'now': now})


def test_a_bearish_brain_reaches_the_council_as_a_sell():
    """The regression. This produced BUY before the fix."""
    result = vote_for(0.20, 0.18, 0.15, 0.12)
    assert result['direction'] == 'SELL'

    prediction = prediction_from_vote(result)

    assert council_reads(prediction) == 'SELL', (
        f"brain said SELL, council reads {council_reads(prediction)} "
        f"from prediction {prediction}")


def test_a_bullish_brain_reaches_the_council_as_a_buy():
    result = vote_for(0.80, 0.82, 0.85, 0.88)
    assert result['direction'] == 'BUY'

    assert council_reads(prediction_from_vote(result)) == 'BUY'


def test_direction_survives_across_the_whole_confidence_range():
    """Mild and extreme convictions must both keep their sign."""
    for votes, expected in [
        ((0.44, 0.42, 0.40, 0.38), 'SELL'),
        ((0.30, 0.28, 0.25, 0.22), 'SELL'),
        ((0.05, 0.04, 0.03, 0.02), 'SELL'),
        ((0.56, 0.58, 0.60, 0.62), 'BUY'),
        ((0.95, 0.96, 0.97, 0.98), 'BUY'),
    ]:
        result = vote_for(*votes)
        assert result['direction'] == expected, f"{votes} -> {result['direction']}"

        prediction = prediction_from_vote(result)
        assert council_reads(prediction) == expected, (
            f"{votes}: brain {expected}, council {council_reads(prediction)} "
            f"(prediction {prediction})")


def test_hold_hands_over_a_neutral_number():
    result = vote_for(0.50, 0.50, 0.50, 0.50)

    assert prediction_from_vote(result) == 0.5
    assert council_reads(prediction_from_vote(result)) == 'NO_DIRECTION'


def test_agreement_below_the_threshold_does_not_trade():
    """2/4 is a real direction but not enough of one."""
    result = vote_for(0.50, 0.50, 0.75, 0.80)

    assert result['direction'] == 'BUY'
    assert result['agreement'] == 2
    assert prediction_from_vote(result) == 0.5


def test_min_agreement_is_configurable():
    result = vote_for(0.50, 0.50, 0.75, 0.80)

    assert prediction_from_vote(result, min_agreement=2) == result['confidence']


def test_contradictory_result_is_refused_rather_than_guessed():
    """If direction and confidence ever disagree, sit it out.

    A hand-made result, since _aggregate_votes should never produce one -- this
    guards the mapping against a future change upstream that reintroduces the
    same class of bug.
    """
    assert prediction_from_vote(
        {'direction': 'SELL', 'agreement': 4, 'confidence': 0.90}) == 0.5
    assert prediction_from_vote(
        {'direction': 'BUY', 'agreement': 4, 'confidence': 0.10}) == 0.5


def test_missing_keys_default_to_no_opinion():
    assert prediction_from_vote({}) == 0.5
