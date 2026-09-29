from datetime import datetime
from sqlalchemy import (
    UniqueConstraint,
    CheckConstraint,
    ForeignKey,
    BigInteger,
    Integer,
    String,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PriceThreshold(Base):
    __tablename__ = "price_thresholds"
    __table_args__ = (
        UniqueConstraint("user_id", "direction"),
        CheckConstraint("direction IN ('above', 'below')", name="valid_direction"),
        CheckConstraint("price_copper > 0", name="positive_threshold"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    direction: Mapped[str] = mapped_column(String(5))
    price_copper: Mapped[int] = mapped_column(BigInteger)
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="price_thresholds")
