from datetime import UTC, datetime, timedelta

from src.security import can_cancel


def test_owner_within_24h():
    now = datetime.now(UTC)
    assert can_cancel("NEW", 1, 1, False, now - timedelta(hours=1), now)

def test_stranger_denied():
    now = datetime.now(UTC)
    assert not can_cancel("NEW", 1, 2, False, now, now)

def test_shipped_denied_even_admin():
    now = datetime.now(UTC)
    assert not can_cancel("SHIPPED", 1, 1, True, now, now)

def test_expired_denied():
    now = datetime.now(UTC)
    assert not can_cancel("NEW", 1, 1, False, now - timedelta(hours=25), now)

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)  # fecha fija


def test_admin_cancels_new_order_of_other_user():
    created = NOW - timedelta(days=3)
    assert can_cancel("NEW", owner_id=1, user_id=99, is_admin=True, created_at=created, now=NOW)


def test_owner_exactly_24h_denied():
    created = NOW - timedelta(hours=24)
    assert not can_cancel("NEW", 1, 1, False, created, NOW)