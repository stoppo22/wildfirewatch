"""Enrich persisted fire events with cached WorldCover context."""

import argparse
import logging
import os
import sqlite3
import sys
from pathlib import Path

import ee
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wildfirewatch.database import (  # noqa: E402
    create_tables,
    load_fire_events,
    load_land_cover_context,
)
from wildfirewatch.environment import (  # noqa: E402
    get_or_fetch_land_cover_context,
    land_cover_name,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich persisted fire events with ESA WorldCover context."
    )
    parser.add_argument(
        "database",
        type=Path,
        help="Path to the WildfireWatch SQLite database.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    load_dotenv(PROJECT_ROOT / ".env")
    project_id = os.getenv("EARTH_ENGINE_PROJECT")
    if not project_id:
        raise SystemExit("EARTH_ENGINE_PROJECT is missing from the local .env file.")

    connection = sqlite3.connect(args.database)
    try:
        create_tables(connection)
        events = load_fire_events(connection)

        if not events:
            connection.commit()
            logging.info("No persisted fire events found.")
            return

        ee.Initialize(project=project_id)
        cached_count = 0
        fetched_count = 0
        missing_count = 0

        for event in events:
            was_cached = load_land_cover_context(connection, event.event_id) is not None
            context = get_or_fetch_land_cover_context(connection, event)

            if context is None:
                missing_count += 1
                logging.warning("Event %s has no land-cover value.", event.event_id)
                continue

            if was_cached:
                cached_count += 1
            else:
                fetched_count += 1

            logging.info(
                "Event %s: %s (code %s).",
                event.event_id,
                land_cover_name(context.class_code),
                context.class_code,
            )

        connection.commit()
    except Exception:
        connection.rollback()
        logging.exception("Environmental enrichment failed; changes rolled back.")
        raise SystemExit(1)
    finally:
        connection.close()

    logging.info(
        "Enrichment complete: %s fetched, %s cached, %s unavailable.",
        fetched_count,
        cached_count,
        missing_count,
    )


if __name__ == "__main__":
    main()
