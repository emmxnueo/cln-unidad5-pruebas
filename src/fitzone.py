from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

OFFER_WINDOW = timedelta(minutes=15)   # ADR-002: 15 min para confirmar
NO_SHOW_LIMIT = timedelta(minutes=10)  # ADR-002: retraso de 10 min libera el lugar


class WaitlistEmpty(Exception):
    pass


class OfferExpired(Exception):
    pass


@dataclass
class Offer:
    member_id: int
    offered_at: datetime
    status: str = "PENDING"

    def confirm(self, now):
        if now - self.offered_at > OFFER_WINDOW:
            self.status = "EXPIRED"
            raise OfferExpired("offer expired")
        self.status = "CONFIRMED"
        return self.member_id


class Waitlist:
    """Lista de espera FIFO."""

    def __init__(self):
        self._queue = deque()

    def join(self, member_id):
        if member_id in self._queue:
            raise ValueError("already in waitlist")
        self._queue.append(member_id)

    def members(self):
        return list(self._queue)

    def next_for_cancellation(self, now):
        if not self._queue:
            raise WaitlistEmpty("no members waiting")
        return Offer(self._queue.popleft(), now)


def assign_on_no_show(class_start, now, present_members):
    """Lugar liberado por retraso: asignación inmediata al socio presente."""
    if now - class_start < NO_SHOW_LIMIT:
        raise ValueError("too early to release spot")
    if not present_members:
        raise WaitlistEmpty("no member present")
    return present_members[0]


class WaitlistService:
    def __init__(self, notifier):
        self.notifier = notifier

    def offer_spot(self, waitlist, now):
        offer = waitlist.next_for_cancellation(now)
        self.notifier.send(offer.member_id, offer.offered_at + OFFER_WINDOW)
        return offer
