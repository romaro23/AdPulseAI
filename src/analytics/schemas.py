from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, computed_field
from src.db.models import VerticalType

TWO_PLACES = Decimal("0.01")

class CampaignFunnelMetrics(BaseModel):
    campaign_id: int
    campaign_name: str
    vertical: VerticalType

    impressions: int
    clicks: int
    spend: Decimal
    leads: int
    sales: int
    revenue: Decimal

    @computed_field
    @property
    def ctr(self) -> Decimal | None:
        if self.impressions == 0:
            return None
        return (Decimal(self.clicks) / Decimal(self.impressions) * Decimal(100)).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

    @computed_field
    @property
    def cpc(self) -> Decimal | None:
        if self.clicks == 0:
            return None
        return (self.spend / self.clicks).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @computed_field
    @property
    def cpl(self) -> Decimal | None:
        if self.leads == 0:
            return None
        return (self.spend / self.leads).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @computed_field
    @property
    def cpa(self) -> Decimal | None:
        if self.sales == 0:
            return None
        return (self.spend / self.sales).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @computed_field
    @property
    def roas(self) -> Decimal | None:
        if self.spend == Decimal(0):
            return None
        return (self.revenue / self.spend).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)