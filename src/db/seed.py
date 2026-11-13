import asyncio
import random
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.base import Base
from src.db.models import Campaign, VerticalType, CampaignStatus, AdSet, BidStrategy, AdCreative, AdCreativeStatus, \
    CTAType, Format, DailyAdMetric, LeadEvent, DeviceOS
from src.db.session import engine, async_session_factory

def calculate_conversion_prob(
        campaign: Campaign,
        ad_set: AdSet,
        ad_creative: AdCreative,
        device_os: DeviceOS,
        user_age: int,
) -> float:
    base_prob = 0.03

    if ad_creative.name == "ab_control_static":
        return 0.040
    if ad_creative.name == "ab_treatment_video":
        return 0.058

    if device_os in (DeviceOS.IOS, DeviceOS.MACOS) and ad_set.target_geo == "US":
        base_prob += 0.045
    if ad_creative.format == Format.VIDEO:
        base_prob += 0.025
    if campaign.vertical == VerticalType.FINTECH and 27 <= user_age <= 42:
        base_prob += 0.040
    elif campaign.vertical == VerticalType.EDTECH and 18 <= user_age <= 26:
        base_prob += 0.035

    return min(base_prob, 0.35)


async def initialize_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed_database(session: AsyncSession):
    campaigns_data = [
        ("TechFlow SaaS Scaling", VerticalType.SAAS, Decimal("500.00")),
        ("NeoBank Card Acquisition", VerticalType.FINTECH, Decimal("1200.00")),
        ("Python AI Bootcamp", VerticalType.EDTECH, Decimal("300.00")),
        ("StreetWear Q4 Promo", VerticalType.E_COMMERCE, Decimal("800.00")),
    ]

    campaigns = [
        Campaign(
            name=name,
            vertical=vertical,
            daily_budget=budget,
            status=CampaignStatus.ACTIVE,
        )
        for name, vertical, budget in campaigns_data
    ]


    session.add_all(campaigns)
    await session.flush()

    ad_sets: list[AdSet] = []
    ad_set_contexts: list[tuple[AdSet, Campaign]] = []
    for campaign in campaigns:
        for i in range(2):
            geo = random.choice(["US", "CA", "MX", "ES", "UA"])
            a_min = random.randint(18, 35)
            a_max = random.randint(a_min + 10, 60)

            ad_set = AdSet(
                campaign_id=campaign.id,
                name=f"{campaign.vertical.value.upper()}_{geo}_AdSet_{i + 1}",
                target_geo=geo,
                age_min=a_min,
                age_max=a_max,
                bid_strategy=random.choice(list(BidStrategy)),
            )

            ad_sets.append(ad_set)
            ad_set_contexts.append((ad_set, campaign))

    session.add_all(ad_sets)
    await session.flush()

    ad_creatives: list[AdCreative] = []
    ad_creative_contexts: list[tuple[AdCreative, AdSet, Campaign]] = []
    for ad_set, campaign in ad_set_contexts:
        for i in range(2):
            ad_creative = AdCreative(
                ad_set_id=ad_set.id,
                name=f"{ad_set.name}_AdCreative_{i + 1}",
                format=random.choice(list(Format)),
                cta_type=random.choice(list(CTAType)),
                status=random.choice(list(AdCreativeStatus)),
            )

            ad_creatives.append(ad_creative)
            ad_creative_contexts.append((ad_creative, ad_set, campaign))

    ad_creatives[0].name="ab_control_static"
    ad_creatives[0].format = Format.STATIC_IMAGE
    ad_creatives[1].name="ab_treatment_video"
    ad_creatives[1].format = Format.VIDEO

    session.add_all(ad_creatives)
    await session.flush()

    daily_ad_metrics: list[DailyAdMetric] = []
    today = date.today()
    for ad_creative in ad_creatives:
        for day_offset in range(30):
            current_date = today - timedelta(days=day_offset)
            impressions = random.randint(2000, 15000)
            clicks = int(impressions * random.uniform(0.01, 0.035))
            cpc = random.uniform(0.1, 2.0)

            daily_ad_metric = DailyAdMetric(
                ad_creative_id=ad_creative.id,
                metric_date=current_date,
                impressions=impressions,
                clicks=clicks,
                spend=Decimal(f"{clicks * cpc:.2f}"),
            )

            if random.random() < 0.04:
                if random.random() < 0.5:
                    daily_ad_metric.spend *= 9
                    daily_ad_metric.clicks = int(impressions * random.uniform(0.005, 0.01))
                else:
                    daily_ad_metric.clicks = int(impressions * random.uniform(0.25, 0.40))
                    daily_ad_metric.spend = Decimal(f"{daily_ad_metric.clicks * cpc:.2f}")

            daily_ad_metrics.append(daily_ad_metric)

    session.add_all(daily_ad_metrics)
    await session.flush()

    lead_events: list[LeadEvent] = []
    now = datetime.now(timezone.utc)
    for ad_creative, ad_set, campaign in ad_creative_contexts:
        if ad_creative.name in ("ab_control_static", "ab_treatment_video"):
            num_events = 2500
        else:
            num_events = random.randint(600, 1000)

        for _ in range(num_events):
            device_os = random.choice(list(DeviceOS))
            user_age = random.randint(ad_set.age_min, ad_set.age_max)

            p_lead = calculate_conversion_prob(campaign, ad_set, ad_creative, device_os, user_age)
            is_lead = random.random() < p_lead
            is_sale = False
            revenue = Decimal("0.00")

            if is_lead:
                if random.random() < 0.25:
                    is_sale = True
                    revenue = Decimal(f"{random.uniform(25.0, 250.0):.2f}")

            lead_event = LeadEvent(
                ad_creative_id=ad_creative.id,
                clicked_at=now - timedelta(days=random.randint(0, 30), seconds=random.randint(0, 86400)),
                device_os=device_os,
                user_age=user_age,
                is_lead=is_lead,
                is_sale=is_sale,
                revenue=revenue
            )

            lead_events.append(lead_event)

    session.add_all(lead_events)
    await session.commit()


async def main():
    await initialize_tables()
    async with async_session_factory() as session:
        await seed_database(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
