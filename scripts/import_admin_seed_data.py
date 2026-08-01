"""One-off data migration: load radium-admin's static src/data/*.json seeds
into Postgres. Idempotent per table — skips any table that already has rows.

Run once, from radium-backend, with the app's dependencies on PATH:

    python scripts/import_admin_seed_data.py

Assumes radium-admin is a sibling checkout (../radium-admin); override with
--data-dir if that's not the case.
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from app.core.logging import configure_logging
from app.db.session import AsyncSessionLocal, engine
from app.models.accessory import Accessory
from app.models.activity_log import ActivityLog
from app.models.category import Category
from app.models.enquiry import Enquiry
from app.models.product import Product
from app.models.variant import Variant

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "radium-admin" / "src" / "data"


def load(data_dir: Path, name: str) -> list[dict]:
    return json.loads((data_dir / name).read_text())


async def table_is_empty(session, model) -> bool:
    count = await session.scalar(select(func.count()).select_from(select(model.id).subquery()))
    return count == 0


async def import_categories(session, data_dir: Path) -> None:
    if not await table_is_empty(session, Category):
        logger.info("categories already has rows — skipping")
        return
    items = load(data_dir, "categories.json")
    for c in items:
        session.add(Category(id=c["id"], label=c["label"], blurb=c.get("blurb")))
    logger.info("Queued %d categories", len(items))


async def import_products(session, data_dir: Path) -> None:
    if not await table_is_empty(session, Product):
        logger.info("products already has rows — skipping")
        return
    items = load(data_dir, "products.json")
    for p in items:
        session.add(
            Product(
                id=p["id"],
                slug=p["slug"],
                name=p["name"],
                series=p["series"],
                tagline=p["tagline"],
                category=p["category"],
                status=p.get("status", "available"),
                note=p.get("note", ""),
                form_factor=p.get("formFactor", ""),
                has_models=p.get("hasModels", False),
                summary=p.get("summary", ""),
                highlights=p.get("highlights", []),
                applications=p.get("applications", []),
                specs=p.get("specs", []),
                images=p.get("images", []),
            )
        )
    logger.info("Queued %d products", len(items))


async def import_variants(session, data_dir: Path) -> None:
    """Seed the unified variants table from the legacy per-family JSON files."""
    if not await table_is_empty(session, Variant):
        logger.info("variants already has rows — skipping")
        return
    count = 0
    if (data_dir / "jupiter-models.json").is_file():
        for m in load(data_dir, "jupiter-models.json"):
            session.add(
                Variant(
                    id=m["id"],
                    name=m["name"],
                    code=m["code"],
                    family=m["family"],
                    rack_units=m.get("rackUnits", "4U"),
                    status=m.get("status", "available"),
                )
            )
            count += 1
    if (data_dir / "chassis-models.json").is_file():
        for m in load(data_dir, "chassis-models.json"):
            session.add(
                Variant(
                    id=m["id"],
                    name=m["model"],
                    code=None,
                    family=m["family"],
                    rack_units=m.get("ru", "2U"),
                    img=m.get("img", ""),
                    bullets=m.get("bullets", []),
                    status=m.get("status", "available"),
                )
            )
            count += 1
    logger.info("Queued %d variants", count)


async def import_accessories(session, data_dir: Path) -> None:
    if not await table_is_empty(session, Accessory):
        logger.info("accessories already has rows — skipping")
        return
    items = load(data_dir, "accessories.json")
    for a in items:
        session.add(
            Accessory(
                id=a["id"],
                name=a["name"],
                sku=a["sku"],
                category=a["category"],
                description=a.get("description", ""),
                for_=a.get("for", []),
                status=a.get("status", "available"),
            )
        )
    logger.info("Queued %d accessories", len(items))


async def import_enquiries(session, data_dir: Path) -> None:
    if not await table_is_empty(session, Enquiry):
        logger.info("enquiries already has rows — skipping")
        return
    items = load(data_dir, "enquiries.json")
    for e in items:
        session.add(
            Enquiry(
                name=e["name"],
                org=e.get("org", ""),
                email=e["email"],
                phone=e.get("phone", ""),
                interest=e.get("interest", ""),
                message=e.get("message", ""),
                status=e.get("status", "new"),
                received_at=datetime.fromisoformat(e["receivedAt"]),
            )
        )
    logger.info("Queued %d enquiries", len(items))


async def import_activity(session, data_dir: Path) -> None:
    if not await table_is_empty(session, ActivityLog):
        logger.info("activity_log already has rows — skipping")
        return
    items = load(data_dir, "activity.json")
    for a in items:
        session.add(
            ActivityLog(
                type=a["type"],
                module=a["module"],
                label=a["label"],
                at=datetime.fromisoformat(a["at"]),
            )
        )
    logger.info("Queued %d activity entries", len(items))


async def run(data_dir: Path) -> None:
    async with AsyncSessionLocal() as session:
        # Order matters: categories before products, products before variants.
        await import_categories(session, data_dir)
        await session.flush()
        await import_products(session, data_dir)
        await session.flush()
        await import_variants(session, data_dir)
        await import_accessories(session, data_dir)
        await import_enquiries(session, data_dir)
        await import_activity(session, data_dir)
        await session.commit()
    logger.info("Done.")


async def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    if not args.data_dir.is_dir():
        raise SystemExit(f"Data dir not found: {args.data_dir}")
    try:
        await run(args.data_dir)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
