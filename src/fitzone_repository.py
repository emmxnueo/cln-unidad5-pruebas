from sqlalchemy import Column, Integer, select
from sqlalchemy.orm import Session

from src.repository import Base


class WaitlistRow(Base):
    __tablename__ = "waitlist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, nullable=False)
    member_id = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)


class SqlWaitlistRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, class_id, member_id, position):
        self.session.add(WaitlistRow(class_id=class_id, member_id=member_id, position=position))

    def members(self, class_id):
        query = (
            select(WaitlistRow.member_id)
            .where(WaitlistRow.class_id == class_id)
            .order_by(WaitlistRow.position)
        )
        return list(self.session.scalars(query))
