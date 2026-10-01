from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    BigInteger,
    Integer,
    String,
    DateTime,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PriceAlert(Base):
    __tablename__ = "price_alerts"
    __table_args__ = (
        CheckConstraint(
            "threshold_direction IN ('above', 'below')", name="valid_direction"
        ),
        CheckConstraint("threshold_price_copper > 0", name="positive_threshold"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    threshold_direction: Mapped[str] = mapped_column(String(5))
    threshold_price_copper: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("price_snapshots.id", ondelete="NO ACTION")
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
