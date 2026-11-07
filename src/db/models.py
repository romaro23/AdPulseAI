from uuid import uuid4, UUID

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import String, Numeric, DateTime, func, CheckConstraint, ForeignKey, Integer, Date, UniqueConstraint, \
    Boolean
from sqlalchemy import Enum as SQLEnum
from enum import StrEnum
from decimal import Decimal
from datetime import datetime, date
from src.db.base import Base

class VerticalType(StrEnum):
    E_COMMERCE = "e-commerce"
    FINTECH = "fintech"
    EDTECH = "edtech"
    SAAS = "saas"

class CampaignStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"

class BidStrategy(StrEnum):
    LOWEST_COST = "lowest_cost"
    COST_CAP = "cost_cap"
    TARGET_ROAS = "target_roas"

class Format(StrEnum):
    VIDEO = "video"
    STATIC_IMAGE = "static_image"
    CAROUSEL = "carousel"

class CTAType(StrEnum):
    LEARN_MORE = "learn_more"
    SIGN_UP = "sign_up"
    SHOP_NOW = "shop_now"

class AdCreativeStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    FATIGUED = "fatigued"

class DeviceOS(StrEnum):
    IOS = "ios"
    MACOS = "macos"
    ANDROID = "android"
    WINDOWS = "windows"


class Campaign(Base):
    __tablename__ = 'campaigns'
    __table_args__ = (
        CheckConstraint("daily_budget > 0", name="check_daily_budget_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    vertical: Mapped[VerticalType] = mapped_column(
        SQLEnum(
            VerticalType,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        )
    )
    daily_budget: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(
            CampaignStatus,
            native_enum=True,
            values_callable = lambda obj: [e.value for e in obj],
        ),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    ad_sets: Mapped[list["AdSet"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

class AdSet(Base):
    __tablename__ = 'ad_sets'
    __table_args__ = (
        CheckConstraint("age_min >= 18 AND age_max >= age_min", name="check_valid_age_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    target_geo: Mapped[str] = mapped_column(String(2))
    age_min: Mapped[int] = mapped_column(Integer())
    age_max: Mapped[int] = mapped_column(Integer())
    bid_strategy: Mapped[BidStrategy] = mapped_column(
        SQLEnum(
            BidStrategy,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="ad_sets")
    ad_creatives: Mapped[list["AdCreative"]] = relationship(
        back_populates="ad_set",
        cascade="all, delete-orphan",
    )

class AdCreative(Base):
    __tablename__ = 'ad_creatives'

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_set_id: Mapped[int] = mapped_column(ForeignKey("ad_sets.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    format: Mapped[Format] = mapped_column(
        SQLEnum(
            Format,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    cta_type: Mapped[CTAType] = mapped_column(
        SQLEnum(
            CTAType,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    status: Mapped[AdCreativeStatus] = mapped_column(
        SQLEnum(
            AdCreativeStatus,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )

    ad_set: Mapped["AdSet"] = relationship(back_populates="ad_creatives")
    daily_ad_metrics: Mapped[list["DailyAdMetric"]] = relationship(
        back_populates="ad_creative",
        cascade="all, delete-orphan",
    )
    lead_events: Mapped[list["LeadEvent"]] = relationship(
        back_populates="ad_creative",
        cascade="all, delete-orphan",
    )

class DailyAdMetric(Base):
    __tablename__ = 'daily_ad_metrics'
    __table_args__ = (
        CheckConstraint("impressions >= 0", name="check_imressions_positive_or_zero"),
        CheckConstraint("clicks >= 0", name="check_clicks_positive_or_zero"),
        CheckConstraint("spend >= 0", name="check_spend_positive_or_zero"),
        CheckConstraint("clicks <= impressions", name="check_clicks_less_or_equal_than_impressions"),
        UniqueConstraint("ad_creative_id", "metric_date", name="uq_creative_metric_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_creative_id: Mapped[int] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), index=True)
    metric_date: Mapped[date] = mapped_column(Date(), index=True)
    impressions: Mapped[int] = mapped_column(Integer())
    clicks: Mapped[int] = mapped_column(Integer())
    spend: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), default=Decimal("0.00"))

    ad_creative: Mapped["AdCreative"] = relationship(back_populates="daily_ad_metrics")

class LeadEvent(Base):
    __tablename__ = 'lead_events'
    __table_args__ = (
        CheckConstraint("user_age > 0", name="check_user_age_positive"),
        CheckConstraint("NOT (is_sale AND NOT is_lead)", name="check_sale_requires_lead"),
        CheckConstraint(
            "(is_sale AND revenue > 0) OR (NOT is_sale AND revenue = 0)",
            name="check_revenue_matches_sale",
        )
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ad_creative_id: Mapped[int] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), index=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    device_os: Mapped[DeviceOS] = mapped_column(
        SQLEnum(
            DeviceOS,
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
    )
    user_age: Mapped[int] = mapped_column(Integer())
    is_lead: Mapped[bool] = mapped_column(Boolean())
    is_sale: Mapped[bool] = mapped_column(Boolean())
    revenue: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), default=Decimal("0.00"))

    ad_creative: Mapped["AdCreative"] = relationship(back_populates="lead_events")
