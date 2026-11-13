from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.schemas import CampaignFunnelMetrics
from src.db.models import DailyAdMetric, LeadEvent, Campaign, AdSet, AdCreative


async def get_campaign_funnel_metrics(
    session: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[CampaignFunnelMetrics]:
    delivery_stmt = select(
        DailyAdMetric.ad_creative_id,
        func.sum(DailyAdMetric.impressions).label("impressions"),
        func.sum(DailyAdMetric.clicks).label("clicks"),
        func.sum(DailyAdMetric.spend).label("spend"),
    ).group_by(DailyAdMetric.ad_creative_id)

    if start_date is not None:
        delivery_stmt = delivery_stmt.where(DailyAdMetric.metric_date >= start_date)
    if end_date is not None:
        delivery_stmt = delivery_stmt.where(DailyAdMetric.metric_date <= end_date)

    delivery_cte = delivery_stmt.cte("delivery_cte")

    conversion_stmt = select(
        LeadEvent.ad_creative_id,
        func.count().filter(LeadEvent.is_lead.is_(True)).label("leads"),
        func.count().filter(LeadEvent.is_sale.is_(True)).label("sales"),
        func.sum(LeadEvent.revenue).label("revenue"),
    ).group_by(LeadEvent.ad_creative_id)

    if start_date is not None:
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        conversion_stmt = conversion_stmt.where(LeadEvent.clicked_at >= start_dt)
    if end_date is not None:
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        conversion_stmt = conversion_stmt.where(LeadEvent.clicked_at < end_dt)

    conversion_cte = conversion_stmt.cte("conversion_cte")

    main_stmt = (
        select(
            Campaign.id.label("campaign_id"),
            Campaign.name.label("campaign_name"),
            Campaign.vertical,
            func.coalesce(func.sum(delivery_cte.c.impressions), 0).label("impressions"),
            func.coalesce(func.sum(delivery_cte.c.clicks), 0).label("clicks"),
            func.coalesce(func.sum(delivery_cte.c.spend), Decimal("0.00")).label("spend"),
            func.coalesce(func.sum(conversion_cte.c.leads), 0).label("leads"),
            func.coalesce(func.sum(conversion_cte.c.sales), 0).label("sales"),
            func.coalesce(func.sum(conversion_cte.c.revenue), Decimal("0.00")).label("revenue"),
        )
        .outerjoin(AdSet, AdSet.campaign_id == Campaign.id)
        .outerjoin(AdCreative, AdCreative.ad_set_id == AdSet.id)
        .outerjoin(delivery_cte, delivery_cte.c.ad_creative_id == AdCreative.id)
        .outerjoin(conversion_cte, conversion_cte.c.ad_creative_id == AdCreative.id)
        .group_by(Campaign.id, Campaign.name, Campaign.vertical)
        .order_by(Campaign.id)
    )

    result = await session.execute(main_stmt)
    return [CampaignFunnelMetrics(**row) for row in result.mappings().all()]

