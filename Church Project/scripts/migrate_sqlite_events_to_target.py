import os
import sqlite3
import sys
from datetime import datetime

from dotenv import dotenv_values


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
LOCAL_DB_PATH = os.path.join(PROJECT_ROOT, "instance", "golammi.db")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def load_target_database_url():
    env_values = dotenv_values(ENV_PATH)
    target_url = env_values.get("PRODUCTION_DATABASE_URL") or env_values.get("DATABASE_URL")
    if not target_url:
        raise RuntimeError("No target database URL found in .env.")
    return target_url


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def load_local_events():
    if not os.path.exists(LOCAL_DB_PATH):
        raise RuntimeError(f"Local database not found at {LOCAL_DB_PATH}.")

    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                title,
                slug,
                description,
                short_description,
                category,
                start_date,
                end_date,
                start_time,
                end_time,
                location,
                venue,
                is_online,
                online_link,
                image,
                is_featured,
                is_published,
                registration_required,
                registration_link,
                created_at,
                updated_at
            FROM events
            ORDER BY start_date ASC, created_at ASC
            """
        ).fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]


def main():
    target_url = load_target_database_url()
    os.environ["DATABASE_URL"] = target_url
    os.environ["FLASK_ENV"] = "production"

    from app import create_app
    from config import ProductionConfig
    from extensions import db
    from models.event import Event
    from models.user import User

    local_events = load_local_events()
    if not local_events:
        print("No local events found to migrate.")
        return

    app = create_app(ProductionConfig)

    with app.app_context():
        superadmin = User.query.filter_by(role="super_admin").order_by(User.created_at.asc()).first()
        if not superadmin:
            raise RuntimeError("No superadmin found in target database.")

        inserted = 0
        updated = 0

        for row in local_events:
            event = Event.query.filter_by(slug=row["slug"]).first()
            is_new = event is None
            if is_new:
                event = Event(
                    slug=row["slug"],
                    created_by=superadmin.id,
                )
                db.session.add(event)

            event.title = row["title"]
            event.description = row["description"] or ""
            event.short_description = row["short_description"]
            event.category = row["category"] or "conference"
            event.start_date = parse_datetime(row["start_date"])
            event.end_date = parse_datetime(row["end_date"])
            event.start_time = row["start_time"]
            event.end_time = row["end_time"]
            event.location = row["location"]
            event.venue = row["venue"]
            event.is_online = bool(row["is_online"])
            event.online_link = row["online_link"]
            event.image = row["image"]
            event.is_featured = bool(row["is_featured"])
            event.is_published = bool(row["is_published"])
            event.registration_required = bool(row["registration_required"])
            event.registration_link = row["registration_link"]
            event.created_at = parse_datetime(row["created_at"]) or datetime.utcnow()
            event.updated_at = parse_datetime(row["updated_at"]) or datetime.utcnow()
            event.updated_by = superadmin.id
            if not event.created_by:
                event.created_by = superadmin.id

            if is_new:
                inserted += 1
            else:
                updated += 1

        db.session.commit()

        print(f"Local events processed: {len(local_events)}")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")


if __name__ == "__main__":
    main()
