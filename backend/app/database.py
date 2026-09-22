from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# 轻量幂等迁移：create_all 不会为已存在的表补列，这里按 inspector 结果显式 ADD COLUMN。
# (table, column, column_ddl)
_EXTRA_COLUMNS = [
    ("delivery_routes", "max_cold_volume_l", "DOUBLE PRECISION DEFAULT 12.0"),
    ("subscriber_stops", "is_cold", "BOOLEAN DEFAULT FALSE"),
    ("pack_bags", "is_cold", "BOOLEAN DEFAULT FALSE"),
    ("bag_items", "is_cold", "BOOLEAN DEFAULT FALSE"),
    ("reject_records", "is_cold", "BOOLEAN DEFAULT FALSE"),
]


def ensure_columns() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, column, ddl in _EXTRA_COLUMNS:
            if table not in existing_tables:
                continue
            if column in {c["name"] for c in inspector.get_columns(table)}:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
