from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from src.fitzone import (
    OFFER_WINDOW,
    OfferExpired,
    Waitlist,
    WaitlistEmpty,
    WaitlistService,
    assign_on_no_show,
)
from src.fitzone_repository import SqlWaitlistRepository
from src.repository import make_engine

T0 = datetime(2026, 11, 2, 18, 0, tzinfo=UTC)  # fecha fija


# --- Regla 1: lista de espera FIFO (ADR-002) ---
def test_cp01_fifo_offers_first_in_line():
    w = Waitlist()
    w.join(10)
    w.join(20)
    offer = w.next_for_cancellation(T0)
    assert offer.member_id == 10
    assert w.members() == [20]


def test_cp02_empty_waitlist_rejected():
    with pytest.raises(WaitlistEmpty):
        Waitlist().next_for_cancellation(T0)


def test_cp03_single_member_leaves_waitlist_empty():
    w = Waitlist()
    w.join(10)
    assert w.next_for_cancellation(T0).member_id == 10
    assert w.members() == []


# --- Regla 2: 15 minutos para confirmar (ADR-002) ---
def test_cp04_confirm_within_window():
    w = Waitlist()
    w.join(10)
    offer = w.next_for_cancellation(T0)
    assert offer.confirm(T0 + timedelta(minutes=10)) == 10
    assert offer.status == "CONFIRMED"


def test_cp05_confirm_after_window_rejected():
    w = Waitlist()
    w.join(10)
    offer = w.next_for_cancellation(T0)
    with pytest.raises(OfferExpired):
        offer.confirm(T0 + timedelta(minutes=16))
    assert offer.status == "EXPIRED"


def test_cp06_confirm_exactly_15_minutes_allowed():
    w = Waitlist()
    w.join(10)
    offer = w.next_for_cancellation(T0)
    assert offer.confirm(T0 + OFFER_WINDOW) == 10


# --- Regla 3: retraso de 10 min => asignación inmediata al socio presente ---
def test_cp07_no_show_assigns_present_member():
    assert assign_on_no_show(T0, T0 + timedelta(minutes=12), [30, 31]) == 30


def test_cp08_too_early_rejected():
    with pytest.raises(ValueError):
        assign_on_no_show(T0, T0 + timedelta(minutes=9), [30])


def test_cp09_exactly_10_minutes_releases_spot():
    assert assign_on_no_show(T0, T0 + timedelta(minutes=10), [30]) == 30


def test_cp10_no_present_member_rejected():
    with pytest.raises(WaitlistEmpty):
        assign_on_no_show(T0, T0 + timedelta(minutes=12), [])


# --- Persistencia (commit / rollback) ---
def test_cp11_waitlist_commit_keeps_order():
    engine = make_engine()
    with Session(engine) as session:
        repo = SqlWaitlistRepository(session)
        repo.add(class_id=1, member_id=20, position=2)
        repo.add(class_id=1, member_id=10, position=1)
        session.commit()
        assert repo.members(1) == [10, 20]


def test_cp12_waitlist_rollback_discards():
    engine = make_engine()
    with Session(engine) as session:
        repo = SqlWaitlistRepository(session)
        repo.add(class_id=1, member_id=10, position=1)
        session.rollback()
        assert repo.members(1) == []


# --- Servicio externo simulado (notificación) ---
def test_cp13_offer_notifies_member_with_deadline():
    notifier = Mock()
    w = Waitlist()
    w.join(10)
    WaitlistService(notifier).offer_spot(w, T0)
    notifier.send.assert_called_once_with(10, T0 + OFFER_WINDOW)
