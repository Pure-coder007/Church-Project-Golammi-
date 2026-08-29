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
        raise RuntimeError("No production database URL found in .env.")
    return target_url


def load_local_superadmin():
    if not os.path.exists(LOCAL_DB_PATH):
        raise RuntimeError(f"Local database not found at {LOCAL_DB_PATH}.")

    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT username, email, password_hash, full_name, role, is_active, created_at, updated_at, last_login
            FROM users
            WHERE role = 'super_admin'
            ORDER BY id ASC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise RuntimeError("No local superadmin record found.")

    return dict(row)


def reset_postgres_content(connection):
    existing_tables = {
        row[0]
        for row in connection.exec_driver_sql(
            "select table_name from information_schema.tables where table_schema = 'public'"
        ).fetchall()
    }
    managed_tables = [
        "activity_logs",
        "blog_comments",
        "blog_posts",
        "church_stats",
        "contact_messages",
        "donation_submissions",
        "events",
        "financial_records",
        "gallery_images",
        "member_growth",
        "prayer_requests",
        "radio_schedules",
        "radio_stations",
        "sermons",
        "testimonies",
    ]
    truncatable_tables = [table for table in managed_tables if table in existing_tables]

    if truncatable_tables:
        connection.exec_driver_sql(
            "TRUNCATE TABLE "
            + ", ".join(truncatable_tables)
            + " RESTART IDENTITY CASCADE"
        )
    if "users" in existing_tables:
        connection.exec_driver_sql("DELETE FROM users WHERE role <> 'super_admin'")


def reset_sqlite_content(db, models):
    ordered_models = [
        models.ActivityLog,
        models.BlogComment,
        models.BlogPost,
        models.ChurchStats,
        models.ContactMessage,
        models.DonationSubmission,
        models.Event,
        models.FinancialRecord,
        models.GalleryImage,
        models.MemberGrowth,
        models.PrayerRequest,
        models.RadioSchedule,
        models.RadioStation,
        models.Sermon,
        models.Testimony,
    ]
    for model in ordered_models:
        db.session.query(model).delete()
    db.session.query(models.User).filter(models.User.role != "super_admin").delete()


def main():
    target_url = load_target_database_url()
    os.environ["DATABASE_URL"] = target_url
    os.environ["FLASK_ENV"] = "production"

    from app import create_app
    from config import ProductionConfig
    from extensions import db
    from models.activity import ActivityLog
    from models.blog import BlogComment, BlogPost
    from models.church_stats import ChurchStats, FinancialRecord, MemberGrowth
    from models.contact import ContactMessage
    from models.donation import DonationSubmission
    from models.event import Event
    from models.gallery import GalleryImage
    from models.prayer import PrayerRequest
    from models.radio import RadioSchedule, RadioStation
    from models.sermon import Sermon
    from models.testimony import Testimony
    from models.user import User

    class ModelBundle:
        pass

    ModelBundle.ActivityLog = ActivityLog
    ModelBundle.BlogComment = BlogComment
    ModelBundle.BlogPost = BlogPost
    ModelBundle.ChurchStats = ChurchStats
    ModelBundle.ContactMessage = ContactMessage
    ModelBundle.DonationSubmission = DonationSubmission
    ModelBundle.Event = Event
    ModelBundle.FinancialRecord = FinancialRecord
    ModelBundle.GalleryImage = GalleryImage
    ModelBundle.MemberGrowth = MemberGrowth
    ModelBundle.PrayerRequest = PrayerRequest
    ModelBundle.RadioSchedule = RadioSchedule
    ModelBundle.RadioStation = RadioStation
    ModelBundle.Sermon = Sermon
    ModelBundle.Testimony = Testimony
    ModelBundle.User = User

    superadmin_data = load_local_superadmin()
    app = create_app(ProductionConfig)

    with app.app_context():
        dialect = db.engine.dialect.name

        if dialect == "postgresql":
            with db.engine.begin() as connection:
                reset_postgres_content(connection)
        else:
            reset_sqlite_content(db, ModelBundle)

        user = User.query.filter_by(role="super_admin").first()
        if user is None:
            user = User(
                username=superadmin_data["username"],
                email=superadmin_data["email"],
                full_name=superadmin_data["full_name"],
                role="super_admin",
                is_active=bool(superadmin_data["is_active"]),
            )
            db.session.add(user)

        user.username = superadmin_data["username"]
        user.email = superadmin_data["email"]
        user.full_name = superadmin_data["full_name"]
        user.role = "super_admin"
        user.is_active = bool(superadmin_data["is_active"])
        user.password_hash = superadmin_data["password_hash"]
        user.last_login = superadmin_data["last_login"]
        user.updated_at = datetime.utcnow()
        db.session.commit()

        print("Production database reset complete.")
        print(f"Superadmin preserved: {user.email}")


if __name__ == "__main__":
    main()
