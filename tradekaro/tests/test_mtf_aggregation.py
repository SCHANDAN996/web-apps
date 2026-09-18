"""
Vote aggregation rules for MultiTimeframeBrain.

These exercise _aggregate_votes directly with hand-written vote dicts, so they
need no model, no candles and no network -- the whole file runs in
milliseconds. main.py trades on `direction` and `agreement >= 3`, so those two
fields agreeing with each other is the contract being pinned down here.

The votes are the model's reading of the latest four 5-minute bars, oldest
first: t-15m, t-10m, t-5m, now.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.multi_timeframe_brain import MultiTimeframeBrain


def _brain():
    # _aggregate_votes never touches self.brain, so None is fine and keeps the
    # test off the GPU/model path entirely.
    return MultiTimeframeBrain(None, scaler=None)


def bars(t15, t10, t5, now):
    return {'t-15m': t15, 't-10m': t10, 't-5m': t5, 'now': now}


def test_agreement_is_counted_for_the_direction_taken():
    """Agreement must count the votes behind the direction, never the other camp."""
    result = _brain()._aggregate_votes(bars(0.30, 0.30, 0.30, 0.80))

    assert result['direction'] == 'HOLD', (
        f"three bearish bars and one bullish must not trade either way, "
        f"got {result['direction']} at {result['position_size_pct']}%")
    assert result['position_size_pct'] == 0


def test_unanimous_buy_takes_full_size():
    result = _brain()._aggregate_votes(bars(0.70, 0.75, 0.80, 0.85))

    assert result['direction'] == 'BUY'
    assert result['agreement'] == 4
    assert result['position_size_pct'] == 100
    assert result['strength'] == 'STRONG'
    assert result['aligned'] is True


def test_unanimous_sell_takes_full_size():
    result = _brain()._aggregate_votes(bars(0.30, 0.25, 0.20, 0.15))

    assert result['direction'] == 'SELL'
    assert result['agreement'] == 4
    assert result['position_size_pct'] == 100


def test_three_of_four_agreeing_sizes_down():
    """3/4 in the traded direction is a real signal -- 75% size."""
    result = _brain()._aggregate_votes(bars(0.50, 0.70, 0.75, 0.80))

    assert result['direction'] == 'BUY'
    assert result['agreement'] == 3
    assert result['position_size_pct'] == 75
    assert result['aligned'] is False  # the oldest bar sat it out


def test_a_signal_that_has_just_faded_is_not_an_entry():
    """Three bullish bars, then the latest one is not: the move already ended."""
    result = _brain()._aggregate_votes(bars(0.70, 0.75, 0.80, 0.50))

    assert result['direction'] == 'HOLD'
    assert result['position_size_pct'] == 0


def test_a_lone_vote_never_trades():
    """Only the latest bar has an opinion; nothing confirms it."""
    result = _brain()._aggregate_votes(bars(0.50, 0.50, 0.50, 0.80))

    assert result['direction'] == 'HOLD'
    assert result['position_size_pct'] == 0
    assert result['strength'] == 'NO_TRADE'


def test_a_split_market_has_no_direction():
    result = _brain()._aggregate_votes(bars(0.80, 0.80, 0.20, 0.20))

    assert result['direction'] == 'HOLD'
    assert result['agreement'] == 0


def test_flat_market_holds():
    result = _brain()._aggregate_votes(bars(0.50, 0.50, 0.50, 0.50))

    assert result['direction'] == 'HOLD'
    assert result['agreement'] == 0


def test_confidence_stays_on_the_side_of_its_direction():
    """prediction_from_vote refuses a SELL whose confidence is above 0.5."""
    result = _brain()._aggregate_votes(bars(0.90, 0.30, 0.25, 0.20))

    assert result['direction'] == 'SELL'
    assert result['confidence'] < 0.5, (
        f"SELL carried confidence {result['confidence']} -- the one bullish "
        f"bar dragged the mean across 0.5")


def test_empty_votes_do_not_report_alignment():
    """all([]) is True, so an empty vote dict used to come back aligned."""
    result = _brain()._aggregate_votes({})

    assert result['direction'] == 'HOLD'
    assert result['aligned'] is False
    assert result['position_size_pct'] == 0
    assert 'reason' in result


def test_failed_views_are_reported():
    """A broken brain must not be indistinguishable from a quiet market."""
    result = _brain()._aggregate_votes(
        {'t-15m': 0.5, 't-10m': 0.5, 't-5m': 0.5},
        failed=['now: RuntimeError: size mismatch'],
    )

    assert result['failed_views'] == ['now: RuntimeError: size mismatch']
    assert result['aligned'] is False


def test_result_always_carries_the_keys_main_py_reads():
    """main.py does .get() on these; _no_signal must match too."""
    for result in (
        _brain()._aggregate_votes(bars(0.6, 0.6, 0.6, 0.6)),
        _brain()._no_signal("insufficient data"),
    ):
        for key in ('direction', 'confidence', 'agreement', 'position_size_pct',
                    'votes', 'aligned', 'failed_views'):
            assert key in result, f"{key} missing from {result}"


if __name__ == '__main__':
    import pytest
    raise SystemExit(pytest.main([__file__, '-v']))
