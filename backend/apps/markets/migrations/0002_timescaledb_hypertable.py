"""Convert market_price_bars into a TimescaleDB hypertable.

Replaces the single-column (ts) primary key Django created with the composite
(instrument_id, interval, ts) — Timescale requires the partition column (ts) to
be part of every unique index — then promotes the table to a hypertable.
"""
from django.db import migrations

FORWARD = """
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

ALTER TABLE market_price_bars DROP CONSTRAINT market_price_bars_pkey;
ALTER TABLE market_price_bars
    ADD CONSTRAINT market_price_bars_pkey PRIMARY KEY (instrument_id, "interval", ts);

SELECT create_hypertable(
    'market_price_bars', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE,
    migrate_data => TRUE
);
"""

# Reversing a hypertable in place is non-trivial; this is a no-op (drop the app's
# tables to fully reverse in dev).
REVERSE = "SELECT 1;"


class Migration(migrations.Migration):
    dependencies = [("markets", "0001_initial")]

    operations = [migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE)]
