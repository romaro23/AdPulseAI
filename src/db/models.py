from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Numeric, DateTime, func, CheckConstraint
from sqlalchemy import Enum as SQLEnum
from enum import StrEnum
from decimal import Decimal
from datetime import datetime

class VerticalType(StrEnum):
    E_COMMERCE = "e-commerce"
    FINTECH = "fintech"
    EDTECH = "edtech"
    SAAS = "saas"

class CampaignStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"

class Base(DeclarativeBase):
    pass

class Campaign(Base):
    __tablename__ = 'campaigns'
    __table_args__ = (
        CheckConstraint("daily_budget >= 0", name="check_daily_budget_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    vertical: Mapped[VerticalType] = mapped_column(SQLEnum(VerticalType, native_enum=True))
    daily_budget: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    status: Mapped[CampaignStatus] = mapped_column(SQLEnum(CampaignStatus, native_enum=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())