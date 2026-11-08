import asyncio
from decimal import Decimal

from src.db.base import Base
from src.db.models import Campaign, VerticalType, CampaignStatus
from src.db.session import engine, async_session_factory


async def initialize_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed_database():
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

    async with async_session_factory() as session:
        session.add_all(campaigns)
        await session.commit()


async def main():
    await initialize_tables()
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
